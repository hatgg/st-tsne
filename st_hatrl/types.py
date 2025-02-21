from dataclasses import dataclass
from enum import Enum
import json
from typing import (
    Dict,
    Generic,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TypedDict,
    Union,
    Literal,
)

from pydantic import BaseModel, Field
import pandas as pd

StateNames = Literal["Battle", "Battle Rewards", "Exp/Relic Screen"]


@dataclass(frozen=True)
class CardEffectInfo:
    type: Optional[str]
    target: Optional[str]
    value: Optional[int]


@dataclass(frozen=True)
class CardInfo:
    effects: Tuple[
        Optional[CardEffectInfo], Optional[CardEffectInfo], Optional[CardEffectInfo]
    ]
    element: str
    legality: str
    viewType: str


class PhaseInfo(NamedTuple):
    phase_name: StateNames
    start: int
    end: int


ScreenStepDict = Dict[StateNames, List[PhaseInfo]]


@dataclass(frozen=True)
class EffectTuple:
    effect: Optional[str]
    target: Optional[str]


@dataclass
class EffectStats:
    total_value: int = 0
    max_value: int = 0
    count: int = 0
    none_flag: bool = False

    def add(self, effect: CardEffectInfo):
        self.count += 1
        if effect.value is None:
            self.none_flag = True
            value = 1
        else:
            if self.none_flag:
                raise Exception(
                    f"found a case where value was sometimes None, and sometimes not {effect} "
                )
            value = effect.value
        self.total_value += value
        self.max_value = max(self.max_value, value)


EffectData = List[Tuple[EffectTuple, EffectStats]]


@dataclass
class ItemStats:
    picked: int = 0
    seen: int = 0

    def merge(self, other: "ItemStats"):
        self.picked += other.picked
        self.seen += other.seen


@dataclass
class CardBattleRewardData:
    all_cards: Dict[CardInfo, ItemStats]


class CardRewardData:
    picked_cards: List[CardInfo]
    seen_cards: List[CardInfo]


class TSNEPointData(BaseModel):
    collection: List[CardInfo]
    x: float
    y: float
    id: str
    effect_count: List[float]


class TSNEPointData3D(TSNEPointData):
    z: Optional[float] = Field(default=None)  # Equivalent to `total=False`


class TSNEOutput(BaseModel):
    effect_names: List[str]
    points: List[Union[TSNEPointData, TSNEPointData3D]]


@dataclass
class PointData:
    x: List[float]
    y: List[float]
    id: List[str]
    collection: List[List[CardInfo]]
    effect_count: List[List[float]]
    point_index: List[int]


@dataclass
class TSNEData:
    effect_names: List[str]
    points: PointData


def build_point_data(points: List[TSNEPointData | TSNEPointData3D]) -> PointData:
    x = []
    y = []
    id = []
    point_index = []
    collection = []
    effect_count = []
    for idx, p in enumerate(points):
        x.append(p.x)
        y.append(p.y)
        id.append(p.id)
        collection.append(p.collection)
        effect_count.append(p.effect_count)
        point_index.append(idx)
    return PointData(
        x=x,
        y=y,
        id=id,
        point_index=point_index,
        collection=collection,
        effect_count=effect_count,
    )


def load_scatter_collection(file_path: str) -> TSNEData:
    with open(file_path, "r") as f:
        json_file = json.load(f)
    tsne = TSNEOutput.model_validate(json_file)

    effect_names = tsne.effect_names
    points = tsne.points
    p_data = build_point_data(points)
    return TSNEData(effect_names=effect_names, points=p_data)


def load_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


T = TypeVar("T")


class AnalysisType(Enum):
    COLLECTION_SCATTER_2D = "collection_scatter_2d"
    CSV = "csv"


class FileKey(Enum):
    LAST_KNOWN_COL = "last_known_collection_tsne2.json"
    GARY_2_COL = "gary_2_tsne2.json"
    BATTLE_REWARDS = "battle_rewards.csv"
    RELICS = "relics.csv"


ProcessedKeyLiteral = Literal[
    "last_known_collection_tsne2", "battle_rewards", "relics", "gary_2_tsne2"
]


@dataclass(frozen=True)
class ProcessInfo(Generic[T]):
    analysis: AnalysisType
    processed_key: ProcessedKeyLiteral
    data_type: Type[T]


ProcessedValue = Union[TSNEData, pd.DataFrame]

# A single mapping that captures all metadata and output type info.
FILE_PROCESS_MAP: Dict[FileKey, ProcessInfo] = {
    FileKey.LAST_KNOWN_COL: ProcessInfo[TSNEData](
        analysis=AnalysisType.COLLECTION_SCATTER_2D,
        processed_key="last_known_collection_tsne2",
        data_type=TSNEData,
    ),
    FileKey.GARY_2_COL: ProcessInfo[TSNEData](
        analysis=AnalysisType.COLLECTION_SCATTER_2D,
        processed_key="gary_2_tsne2",
        data_type=TSNEData,
    ),
    FileKey.BATTLE_REWARDS: ProcessInfo[pd.DataFrame](
        analysis=AnalysisType.CSV,
        processed_key="battle_rewards",
        data_type=pd.DataFrame,
    ),
    FileKey.RELICS: ProcessInfo[pd.DataFrame](
        analysis=AnalysisType.CSV, processed_key="relics", data_type=pd.DataFrame
    ),
}
PROCESSED_KEY_MAP = {v.processed_key: v.analysis for k, v in FILE_PROCESS_MAP.items()}


class ProcessedDataContainer(TypedDict, total=False):
    last_known_collection_tsne2: TSNEData
    gary_2_tsne2: TSNEData
    battle_rewards: pd.DataFrame
    relics: pd.DataFrame

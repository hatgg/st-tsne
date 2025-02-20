from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional, Tuple, TypedDict, Union,Literal

from pydantic import BaseModel, Field



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

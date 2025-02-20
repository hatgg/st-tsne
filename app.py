from dataclasses import dataclass
import os
import json
import pandas as pd
import streamlit as st
from typing import List, Tuple, TypedDict
import plotly.graph_objects as go
from streamlit_plotly_events import (
    plotly_events,
)  # <-- pip install streamlit-plotly-events
from st_hatrl.types import CardInfo, TSNEOutput, TSNEPointData, TSNEPointData3D
from st_hatrl.utils import render_card

st.set_page_config(layout="wide")

# Directory containing your datasets
DATA_DIR = "data"


class SourceDataset(TypedDict, total=False):
    tsne2: TSNEOutput
    tsne3: TSNEOutput


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


class ProcessedDataset(TypedDict, total=False):
    tsne2: TSNEData


@st.cache_data
def list_data_folders(directory):
    """Return a sorted list of subfolders in the data directory."""
    folders = [
        d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))
    ]
    return sorted(folders)


@st.cache_data
def list_files(folder_path):
    """Return a list of JSON and CSV files in the selected folder."""
    all_files = os.listdir(folder_path)
    json_files = [f for f in all_files if f.endswith(".json")]
    csv_files = [f for f in all_files if f.endswith(".csv")]
    return json_files, csv_files


def load_json_file(file_path):
    """Load and return JSON data."""
    with open(file_path, "r") as f:
        return json.load(f)


def load_csv_file(file_path):
    """Load and return CSV data as a DataFrame."""
    return pd.read_csv(file_path)


def load_dataset(folder_path) -> SourceDataset:
    """
    Load known files from the selected folder.
    In this example, we expect a points.json and a metadata.csv.
    Adjust the filenames and processing as needed.
    """
    source_data: SourceDataset = {}
    points_path = os.path.join(folder_path, "tsne2.json")
    if os.path.exists(points_path):
        with open(points_path, "r") as f:
            source_data = json.load(f)
            source_data["tsne2"] = TSNEOutput.model_validate(source_data)
    return source_data


@st.cache_data
def build_dataset(folder_path) -> ProcessedDataset:
    source_dataset = load_dataset(folder_path)
    proc_data: ProcessedDataset = {}
    tsne2 = source_dataset.get("tsne2")
    if tsne2:
        effect_names = tsne2.effect_names
        points = tsne2.points
        p_data = build_point_data(points)
        proc_data["tsne2"] = TSNEData(effect_names=effect_names, points=p_data)
    return proc_data


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


def show_tsne_data(tsne_data: TSNEData):
    if tsne_data:
        effect_names = tsne_data.effect_names
        p_data = tsne_data.points

        # Create two main columns: left for the chart and right for the cards
        left_col, right_col = st.columns([2, 1])
        with left_col:
            # Build a scatter plot using Plotly Graph Objects (go)
            fig = go.Figure(
                data=go.Scatter(
                    x=p_data.x,
                    y=p_data.y,
                    mode="markers",
                    marker=dict(size=8, color="rgba(34,197,94,0.7)"),
                    hovertext=p_data.id,
                )
            )

            # Ensure clicks on the data points are registered
            fig.update_layout(title="2D Scatter Plot", clickmode="event+select")

            st.write("### Scatter Plot (Click on a point to see details)")
            # Use plotly_events to capture click events
            selected_points = plotly_events(
                fig, click_event=True, override_height=400, key="scatter_chart"
            )

        if selected_points:
            point_index = selected_points[0]["pointIndex"]

            # Prepare the bar chart as before
            effect_counts = p_data.effect_count[point_index]
            colors = [
                "red",
                "blue",
                "green",
                "orange",
                "purple",
                "cyan",
                "magenta",
                "yellow",
                "brown",
                "pink",
            ]
            bar_colors = [colors[i % len(colors)] for i in range(len(effect_names))]
            bar_fig = go.Figure(
                data=go.Bar(x=effect_names, y=effect_counts, marker_color=bar_colors)
            )
            bar_fig.update_layout(
                title="Effect Counts", xaxis_title="Effect", yaxis_title="Count"
            )

            with left_col:
                st.write("### Effect Bar Chart")
                st.plotly_chart(bar_fig, use_container_width=True)

            with right_col:
                st.write("### Card Collection")
                selected_cards = p_data.collection[point_index]

                # Display cards two per row
                for i in range(0, len(selected_cards), 2):
                    row_cards = selected_cards[i : i + 2]
                    card_cols = st.columns(2)
                    for j, card in enumerate(row_cards):
                        with card_cols[j]:
                            render_card(card)
        else:
            st.info(
                "Click on a point in the scatter plot to see details and effect bar chart."
            )
    else:
        st.info("No point data available in this folder.")


@st.cache_data
def show_file_contents(folder_path, file_name):
    """Display the content of a selected file."""
    file_path = os.path.join(folder_path, file_name)

    if file_name.endswith(".json"):
        st.subheader(f"📂 JSON File: {file_name}")
        data = load_json_file(file_path)
        st.json(data)
    elif file_name.endswith(".csv"):
        st.subheader(f"📊 CSV File: {file_name}")
        df = load_csv_file(file_path)
        st.dataframe(df, use_container_width=True, height=len(df) * 35 + 50)


# Sidebar: allow the user to choose a dataset folder
st.sidebar.header("Select a Data Folder")
folders = list_data_folders(DATA_DIR)
selected_folder = st.sidebar.selectbox("Data Folder", folders)

# Upload option
st.sidebar.markdown("---")
st.sidebar.header("Or Upload Your Own Files")
uploaded_files = st.sidebar.file_uploader(
    "Select JSON/CSV files", accept_multiple_files=True, type=["json", "csv"]
)

# Main app title
st.title("Data Analysis App")

if selected_folder:
    folder_path = os.path.join(DATA_DIR, selected_folder)
    st.subheader(f"Dataset: {selected_folder}")

    # List available JSON and CSV files
    json_files, csv_files = list_files(folder_path)
    all_files = json_files + csv_files

    if not all_files:
        st.warning("No JSON or CSV files found in the selected folder.")
    else:
        # Create tabs for each file
        tabs = st.tabs(all_files)

        for tab, file_name in zip(tabs, all_files):
            with tab:
                if file_name == "tsne2.json":
                    dataset = build_dataset(folder_path)
                    tsne2_data = dataset.get("tsne2")
                    if tsne2_data:
                        show_tsne_data(tsne2_data)
                    else:
                        st.info("No valid TSNE data found in tsne2.json.")
                else:
                    show_file_contents(folder_path, file_name)

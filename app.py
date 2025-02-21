from dataclasses import dataclass
import os
import json
import pandas as pd
import streamlit as st
from typing import List, Tuple, TypedDict, cast
import plotly.graph_objects as go
from streamlit_plotly_events import (
    plotly_events,
)  # <-- pip install streamlit-plotly-events
from st_hatrl.types import (
    FILE_PROCESS_MAP,
    PROCESSED_KEY_MAP,
    AnalysisType,
    CardInfo,
    FileKey,
    ProcessedDataContainer,
    ProcessedKeyLiteral,
    ProcessedValue,
    TSNEData,
    TSNEOutput,
    TSNEPointData,
    TSNEPointData3D,
    load_csv,
    load_scatter_collection,
)
from st_hatrl.utils import render_card

st.set_page_config(layout="wide")

# Directory containing your datasets
DATA_DIR = "data"


# class SourceDataset(TypedDict, total=False):
#     tsne2: TSNEOutput


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
    json_files = [
        os.path.join(folder_path, f) for f in all_files if f.endswith(".json")
    ]
    csv_files = [os.path.join(folder_path, f) for f in all_files if f.endswith(".csv")]
    return json_files, csv_files


def load_json_file(file_path):
    """Load and return JSON data."""
    with open(file_path, "r") as f:
        return json.load(f)


# def load_csv_file(file_path):
#     """Load and return CSV data as a DataFrame."""
#     return pd.read_csv(file_path)


def get_file_key_from_filename(filename: str) -> FileKey:
    # Extract the base name and remove the extension.
    base = os.path.basename(filename)
    name_without_ext, _ = os.path.splitext(base)
    # Loop through FILE_PROCESS_MAP to find a matching processed_key.
    for key, process_info in FILE_PROCESS_MAP.items():
        if process_info.processed_key == name_without_ext:
            return key
    raise ValueError(f"Unknown file type for filename: {filename}")


@st.cache_data
def build_dataset(files: list[str]) -> ProcessedDataContainer:
    dataset: ProcessedDataContainer = {}
    for file in files:
        file_key = get_file_key_from_filename(file)

        process_info = FILE_PROCESS_MAP[file_key]

        if process_info.analysis == AnalysisType.COLLECTION_SCATTER_2D:
            dataset[process_info.processed_key] = load_scatter_collection(file)
        elif process_info.analysis == AnalysisType.CSV:
            dataset[process_info.processed_key] = load_csv(file)
    return dataset


@st.cache_data
def load_folder(folder_path: str):
    # List available JSON and CSV files
    json_files, csv_files = list_files(folder_path)
    all_files = json_files + csv_files

    valid_set = set([key.value for key, val in FILE_PROCESS_MAP.items()])
    valid_files = [x for x in all_files if os.path.split(x)[-1] in valid_set]

    if not valid_files:
        st.warning("No JSON or CSV files found in the selected folder.")
        return {}
    else:
        # Create tabs for each file
        dataset = build_dataset(valid_files)
        return dataset


def show_dataset(dataset: ProcessedDataContainer):
    proc_keys = list(dataset.keys())
    tabs = st.tabs(proc_keys)

    for tab, proc_key in zip(tabs, proc_keys):
        analysis_type = PROCESSED_KEY_MAP[proc_key]
        data = dataset[proc_key]
        with tab:
            show_analysis(data, analysis_type=analysis_type, key=proc_key)


def show_analysis(
    data: ProcessedValue, analysis_type: AnalysisType, key: ProcessedKeyLiteral
):
    if analysis_type == AnalysisType.COLLECTION_SCATTER_2D:
        show_tsne_data(data, proc_key=key)

    elif analysis_type == AnalysisType.CSV:
        show_df(data)


def show_tsne_data(tsne_data: TSNEData, proc_key: ProcessedKeyLiteral):
    effect_names = tsne_data.effect_names
    p_data = tsne_data.points

    color_option = st.selectbox(
        "Select color data",
        options=["Default", "episode_return"],
        key=f"color_select_{proc_key}",
    )

    if color_option == "Default":
        marker_color = "rgba(34,197,94,0.7)"  # Default static color
    else:
        marker_color = p_data.episode_return  # Use the list of floats

    # Create two main columns: left for the chart and right for the cards
    left_col, right_col = st.columns([2, 1])
    with left_col:
        # Build a scatter plot using Plotly Graph Objects (go)
        fig = go.Figure(
            data=go.Scatter(
                x=p_data.x,
                y=p_data.y,
                mode="markers",
                marker=dict(
                    size=8,
                    color=marker_color,
                    colorscale="Viridis",  # Only applies if marker_color is a list of numbers
                    showscale=True if color_option != "Default" else False,
                ),
                hovertext=p_data.id,
            )
        )

        # Ensure clicks on the data points are registered
        fig.update_layout(title="2D Scatter Plot", clickmode="event+select")

        st.write("### Scatter Plot (Click on a point to see details)")
        # Use plotly_events to capture click events
        selected_points = plotly_events(
            fig, click_event=True, override_height=400, key=f"scatter_{proc_key}"
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
            st.plotly_chart(bar_fig, use_container_width=True, key=f"bar_{proc_key}")

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


@st.cache_data
def show_df(df: pd.DataFrame):
    st.dataframe(df, use_container_width=True, height=len(df) * 35 + 50)


# @st.cache_data
# def show_file_contents(folder_path, file_name):
#     """Display the content of a selected file."""
#     file_path = os.path.join(folder_path, file_name)

#     if file_name.endswith(".json"):
#         st.subheader(f"📂 JSON File: {file_name}")
#         data = load_json_file(file_path)
#         st.json(data)
#     elif file_name.endswith(".csv"):
#         st.subheader(f"📊 CSV File: {file_name}")
#         df = load_csv_file(file_path)
#         st.dataframe(df, use_container_width=True, height=len(df) * 35 + 50)


# Sidebar: allow the user to choose a dataset folder
st.sidebar.header("Select a Data Folder")
folders = list_data_folders(DATA_DIR)
selected_folder = st.sidebar.selectbox("Data Folder", folders)

# Upload option
# st.sidebar.markdown("---")
# st.sidebar.header("Or Upload Your Own Files")
# uploaded_files = st.sidebar.file_uploader(
#     "Select JSON/CSV files", accept_multiple_files=True, type=["json", "csv"]
# )

# Main app title
st.title("Data Analysis App")

if selected_folder:
    folder_path = os.path.join(DATA_DIR, selected_folder)
    st.subheader(f"Dataset: {selected_folder}")
    dataset = load_folder(folder_path)
    show_dataset(dataset)

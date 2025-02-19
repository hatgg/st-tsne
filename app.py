import os
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events  # <-- pip install streamlit-plotly-events

# Directory containing your datasets
DATA_DIR = "data"

@st.cache_data
def list_data_folders(directory):
    """Return a sorted list of subfolders in the data directory."""
    folders = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    return sorted(folders)

@st.cache_data
def load_dataset(folder_path):
    """
    Load known files from the selected folder.
    We expect a tsne2.json file that contains the data.
    """
    data = {}
    points_path = os.path.join(folder_path, "tsne2.json")
    if os.path.exists(points_path):
        with open(points_path, "r") as f:
            data = json.load(f)
    return data

def show_data(dataset):
    tsne2 = dataset.get("tsne2")
    if tsne2:
        effect_names = tsne2["effect_names"]
        points = tsne2["points"]

        # Convert list of point dicts to a DataFrame.
        # Expect each point to have at least: x, y, id, effect_count, etc.
        df = pd.DataFrame(points)
        # Create a unique index for each point to track click events
        df = df.reset_index().rename(columns={"index": "point_index"})
        x = df["x"].to_list()
        y = df["y"].to_list()
        id = df["id"].to_list()
        # Build a scatter plot using Plotly Graph Objects (go)
        fig = go.Figure(
            data=go.Scatter(
                x=x,
                y=y,
                mode="markers",
                marker=dict(size=8, color="rgba(34,197,94,0.7)"),
                # # Use the unique point index as custom data so we can determine which point was clicked
                # customdata=df["point_index"],
                # # Use hover text to show the point id
                # hovertext=df["id"],
                # hoverinfo="text"
                # mode="lines+markers",  # show both line and markers
                # marker=dict(size=12)   # increase marker size for easier clicking

            )
        )
        # fig = go.Figure(
        #     data=go.Scatter(
        #         x=[1, 2],
        #         y=[1, 2],
        #         mode="lines+markers",  # show both line and markers
        #         marker=dict(size=12)   # increase marker size for easier clicking
        #     )
        # )

        # Ensure clicks on the data points are registered
        fig.update_layout(title="2D Scatter Plot", clickmode="event+select")

        st.write("### Scatter Plot (Click on a point to see details)")
        # Use plotly_events to capture click events
        selected_points = plotly_events(fig, click_event=True, override_height=400, key="scatter_chart")
        if selected_points:
            print(selected_points)
        # if selected_points:
        #     # Retrieve the point_index from the customdata of the clicked point
        #     selected_index = selected_points[0]["customdata"]
        #     selected_point = df[df["point_index"] == selected_index].iloc[0]

        #     # Show point details
        #     st.write("### Selected Point Details")
        #     st.json(selected_point.to_dict())

        #     # If the point contains effect counts, display a bar chart.
        #     if "effect_count" in selected_point:
        #         effect_counts = selected_point["effect_count"]

        #         # Define colors (similar to your React colors array)
        #         colors = [
        #             "red", "blue", "green", "orange", "purple",
        #             "cyan", "magenta", "yellow", "brown", "pink"
        #         ]
        #         bar_colors = [colors[i % len(colors)] for i in range(len(effect_names))]

        #         bar_fig = go.Figure(
        #             data=go.Bar(
        #                 x=effect_names,
        #                 y=effect_counts,
        #                 marker_color=bar_colors
        #             )
        #         )
        #         bar_fig.update_layout(
        #             title="Effect Counts",
        #             xaxis_title="Effect",
        #             yaxis_title="Count"
        #         )

        #         st.write("### Effect Bar Chart")
        #         st.plotly_chart(bar_fig, use_container_width=True)
        # else:
        #     st.info("Click on a point in the scatter plot to see details and effect bar chart.")
    else:
        st.info("No point data available in this folder.")

# Sidebar: allow the user to choose one of the available dataset folders
st.sidebar.header("Select a Data Folder")
folders = list_data_folders(DATA_DIR)
selected_folder = st.sidebar.selectbox("Data Folder", folders)

# Optionally, let the user upload their own files
st.sidebar.markdown("---")
st.sidebar.header("Or Upload Your Own Files")
uploaded_files = st.sidebar.file_uploader(
    "Select JSON/CSV files",
    accept_multiple_files=True,
    type=["json", "csv"]
)

# Main app title
st.title("Data Analysis App")

# Load and display dataset if a folder is selected
if selected_folder:
    folder_path = os.path.join(DATA_DIR, selected_folder)
    st.subheader(f"Dataset: {selected_folder}")
    # We expect the JSON to contain a key "tsne2" similar to your React code
    dataset = {"tsne2": load_dataset(folder_path)}
    show_data(dataset)

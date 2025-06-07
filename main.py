import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import folium
from folium.plugins import HeatMap
from data_processing import raw_data

st.set_page_config(page_title="Vulcano Dashboard", layout="wide")

st.title("Vulcano Dashboard")

# sidebar config
st.sidebar.header("Filter Eruptions")
min_year = int(raw_data["Start Year"].min())
max_year = int(raw_data["Start Year"].max())
year_range = st.sidebar.slider("Year Range", min_year, max_year, (min_year, max_year))
vei_options = st.sidebar.multiselect("VEI", sorted(raw_data["VEI"].dropna().unique()), default=sorted(raw_data["VEI"].dropna().unique()))

filtered_df = raw_data[
    (raw_data["Start Year"] >= year_range[0]) &
    (raw_data["Start Year"] <= year_range[1]) &
    (raw_data["VEI"].isin(vei_options))
]

# Map of eruptions
m = folium.Map(location=[0, 0], zoom_start=3, tiles="CartoDB positron")
for _, row in filtered_df.iterrows():
    popup_text = f"""
    <b>{row['Volcano Name']}</b><br>
    <b>Eruption Date:</b> {row['Start Year']}<br>
    <b>VEI:</b> {row['VEI']} {row['VEI Modifier'] if pd.notnull(row['VEI Modifier']) else ''}<br>
    <b>Eruption Category:</b> {row['Eruption Category']}<br>
    <b>Evidence Method:</b> {row['Evidence Method (dating)']}
    """
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=5,
        color="red",
        fill=True,
        fill_color="orange",
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(m)

st_data = st_folium(m, use_container_width=True, height=600)

# Heatmap of eruptions - all eruptions
m2 = folium.Map(location=[0, 0], zoom_start=3, tiles="CartoDB dark_matter")
heat_data = filtered_df[["Latitude", "Longitude"]].values.tolist()
HeatMap(heat_data, radius=10, blur=15, max_zoom=4).add_to(m2)

st_folium(m2, use_container_width=True, height=600)


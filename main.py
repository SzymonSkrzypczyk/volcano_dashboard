import streamlit as st
import pydeck as pdk
from data_processing import raw_data

st.set_page_config(page_title="Vulcano Dashboard", layout="wide")

st.title("Vulcano Dashboard")

# sidebar settings
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

# Maps
view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1.5, pitch=0)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position='[Longitude, Latitude]',
    get_color='[255, 100, 100, 160]',
    get_radius=50000,
    pickable=True,
)

tooltip = {
    "html": "<b>{Volcano Name}</b><br>"
            "Year: {Start Year}<br>"
            "VEI: {VEI}<br>"
            "Category: {Eruption Category}<br>"
            "Dating: {Evidence Method (dating)}",
    "style": {"backgroundColor": "black", "color": "white"}
}

st.subheader("Volcano Locations")
st.pydeck_chart(pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

heat_layer = pdk.Layer(
    "HeatmapLayer",
    data=filtered_df,
    get_position='[Longitude, Latitude]',
    aggregation='MEAN',
    get_weight=1,
    radiusPixels=60,
)

st.subheader("Eruption Heatmap")
st.pydeck_chart(pdk.Deck(
    layers=[heat_layer],
    initial_view_state=view_state
))

# Charts
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Eruption Counts by Year")
    year_counts = raw_data["Start Year"].value_counts().sort_index()
    st.area_chart(year_counts)

with col2:
    st.subheader("Eruption Counts by VEI")
    vei_counts = raw_data["VEI"].value_counts().sort_index()
    st.bar_chart(vei_counts)

with col3:
    st.subheader("Eruption Counts by Category")
    category_counts = raw_data["Eruption Category"].value_counts()
    st.bar_chart(category_counts)

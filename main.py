import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
from matplotlib.colors import Normalize, to_hex
from matplotlib import cm
import plotly.express as px
import json

from country_continent_mapper import country_to_continent
from data_processing import combined, COUNTRIES_DATA
from config import continent_colors, min_number_of_eruptions_for_single_country

st.set_page_config(page_title="Volcano Dashboard", layout="wide")
st.title("🌋 Volcano Eruption Dashboard")

# sidebar settings
st.sidebar.header("🔍 Filter Eruptions")
min_year = int(combined["Start Year"].min())
max_year = int(combined["Start Year"].max())
year_range = st.sidebar.slider("Year Range", min_year, max_year, (0, max_year))
vei_options = st.sidebar.multiselect("VEI", sorted(combined["VEI"].dropna().unique()),
                                     default=sorted(combined["VEI"].dropna().unique()))

with st.sidebar.expander("ℹ️ Term Explanation"):
    st.markdown("""
    **VEI (Volcanic Explosivity Index):** Scale from 0 (non-explosive) to 8 (mega-colossal).  
    **Eruption Category:** Type of eruption.  
    **Evidence Method:** How eruption was dated.  
    """)

filtered_df = combined[
    (combined["Start Year"] >= year_range[0]) &
    (combined["Start Year"] <= year_range[1]) &
    (combined["VEI"].isin(vei_options))
    ]

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
    "html": "<b>{Volcano Name}</b><br>Year: {Start Year}<br>VEI: {VEI}<br>Country: {Country}<br>Category: {Eruption Category}",
    "style": {"backgroundColor": "black", "color": "white"}
}

st.subheader("🗺️ Volcano Locations")
st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip=tooltip))

heat_layer = pdk.Layer(
    "HeatmapLayer",
    data=filtered_df,
    get_position='[Longitude, Latitude]',
    aggregation='MEAN',
    get_weight=1,
    radiusPixels=60,
)

st.subheader("🔥 Eruption Heatmap")
st.pydeck_chart(pdk.Deck(layers=[heat_layer], initial_view_state=view_state))

st.subheader("📆 Eruptions by Year")
year_counts = filtered_df["Start Year"].value_counts().sort_index()
st.bar_chart(year_counts)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🌋 Eruptions by VEI")
    vei_counts = filtered_df["VEI"].value_counts().sort_index()
    st.bar_chart(vei_counts)

with col2:
    st.subheader("📊 Eruption Categories (Log Scale)")
    counts = filtered_df["Eruption Category"].value_counts()
    log_counts = np.log(counts)
    df_cat = pd.DataFrame({
        "Category": counts.index,
        "Count": counts.values,
        "Log Count": log_counts.values
    })
    fig = px.bar(df_cat, x="Category", y="Log Count", hover_data=["Count"], title="Log-Scaled Eruption Counts")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🏳️ Eruptions by Country")

country_counts = filtered_df["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Eruption Count"]

country_counts = filtered_df["Country"].value_counts().reset_index()
country_counts.columns = ["Country", "Eruption Count"]

# 2. Dodaj kontynent korzystając ze słownika country_to_continent
country_counts["Continent"] = country_counts["Country"].map(country_to_continent).fillna("Unknown")

# 3. Filtruj kraje z > 10 erupcji (zmienna możesz dostosować)
country_counts = country_counts[country_counts["Eruption Count"] > min_number_of_eruptions_for_single_country]

# 4. Zdefiniuj paletę kolorów dla kontynentów (dopasuj do swoich potrzeb)

fig_bar = px.bar(
    country_counts,
    x="Country",
    y="Eruption Count",
    color="Continent",
    color_discrete_map=continent_colors,
    title=f"Eruptions per Country ( more than {min_number_of_eruptions_for_single_country} eruptions )"
)

# 6. Wyświetlamy wykres w Streamlit
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("🌍 Eruptions by Continent")

country_counts = filtered_df["Continent"].value_counts().reset_index()
country_counts.columns = ["Continent", "Eruption Count"]
fig_bar = px.bar(
    country_counts,
    x="Continent",
    y="Eruption Count",
    title="Eruptions per Country",
    color="Continent",
    color_discrete_map=continent_colors
)
st.plotly_chart(fig_bar, use_container_width=True)

fig_pie = px.pie(
    country_counts,
    names="Continent",
    values="Eruption Count",
    title="Procentowy udział erupcji według kontynentu",
    color="Continent",
    color_discrete_map=continent_colors
)

st.plotly_chart(fig_pie, use_container_width=True)

choropleth_df = filtered_df.groupby("ISO3").size().reset_index(name="Eruption Count")
with COUNTRIES_DATA.open("r", encoding="utf-8") as f:
    geojson = json.load(f)

eruption_dict = dict(zip(choropleth_df["ISO3"], choropleth_df["Eruption Count"]))
max_eruptions = max(eruption_dict.values())

norm = Normalize(vmin=0, vmax=max_eruptions)
cmap = cm.get_cmap("Oranges")

for feature in geojson["features"]:
    iso = feature["properties"]["ISO3166-1-Alpha-3"]
    eruptions = eruption_dict.get(iso, 0)
    color_rgba = cmap(norm(eruptions))
    color_hex = to_hex(color_rgba)
    feature["properties"]["eruption_count"] = eruptions
    feature["properties"]["fill_color"] = list((int(c * 255) for c in color_rgba[:3]))

geo_layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    pickable=True,
    stroked=False,
    filled=True,
    get_fill_color="properties.fill_color",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=0.5,
    auto_highlight=True,
)

view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1.5, pitch=0)

tooltip = {
    "html": "<b>{name}</b><br>Eruptions: {eruption_count}",
    "style": {"backgroundColor": "black", "color": "white"}
}

st.subheader("🗺️ Eruption Density by Country")
st.pydeck_chart(pdk.Deck(
    layers=[geo_layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

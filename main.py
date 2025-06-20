import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
from matplotlib.colors import Normalize
from matplotlib import cm
import plotly.express as px
import json
from country_continent_mapper import country_to_continent
from data_processing import combined, COUNTRIES_DATA
from config import continent_colors, min_number_of_eruptions_for_single_country, vei_colors, category_colors

st.set_page_config(page_title="Dashboard Wulkanów", layout="wide")
st.title("🌋 Dashboard Erupcji Wulkanicznych")

st.sidebar.header("🔍 Filtruj Erupcje")
min_year = int(combined["Start Year"].min())
max_year = int(combined["Start Year"].max())
year_range = st.sidebar.slider("Zakres lat", min_year, max_year, (0, max_year))
vei_options = st.sidebar.multiselect("Indeks Eksplozywności VEI", sorted(combined["VEI"].dropna().unique()),
                                     default=sorted(combined["VEI"].dropna().unique()))

with st.sidebar.expander("ℹ️ Wyjaśnienie pojęć"):
    st.markdown("""
    **VEI (Volcanic Explosivity Index):** Skala od 0 (nieeksplozywna) do 8 (mega-kolosalna).  
    **Kategoria erupcji:** Typ erupcji (np. centralna, szczelinowa).  
    **Metoda datowania:** Sposób ustalenia czasu erupcji (np. archeologiczna, historyczna, geochronologia).  
    """)

filtered_df = combined[
    (combined["Start Year"] >= year_range[0]) &
    (combined["Start Year"] <= year_range[1]) &
    (combined["VEI"].isin(vei_options))
]

st.subheader("🗺️ Lokalizacje Wulkanów")

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
    "html": "<b>{Volcano Name}</b><br>Rok: {Start Year}<br>VEI: {VEI}<br>Kraj: {Country}<br>Kategoria: {Eruption Category}",
    "style": {"backgroundColor": "black", "color": "white"}
}

st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip=tooltip))

st.subheader("🔥 Mapa Cieplna Erupcji")
heat_layer = pdk.Layer(
    "HeatmapLayer",
    data=filtered_df,
    get_position='[Longitude, Latitude]',
    aggregation='MEAN',
    get_weight=1,
    radiusPixels=60,
)
st.pydeck_chart(pdk.Deck(layers=[heat_layer], initial_view_state=view_state))

st.subheader("📆 Liczba Erupcji w Czasie")
year_counts = filtered_df["Start Year"].value_counts().sort_index()
st.bar_chart(year_counts)


col1, col2 = st.columns(2)
with col1:
    st.subheader("🌋 Erupcje według VEI")
    vei_counts = filtered_df["VEI"].value_counts().sort_index().reset_index()
    vei_counts.columns = ["VEI", "Liczba"]
    vei_counts["VEI"] = vei_counts["VEI"].astype(str)

    fig = px.bar(
        vei_counts,
        x="VEI",
        y="Liczba",
        title="Liczba erupcji według VEI",
        color="VEI",
        color_discrete_map=vei_colors,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Kategorie Erupcji (Skala Logarytmiczna)")
    counts = filtered_df["Eruption Category"].value_counts()
    log_counts = np.log(counts)
    df_cat = pd.DataFrame({
        "Kategoria": counts.index,
        "Liczba": counts.values,
        "Logarytm liczby": log_counts.values
    })

    fig = px.bar(
        df_cat,
        x="Kategoria",
        y="Logarytm liczby",
        hover_data=["Liczba"],
        title="Logarytmiczna liczba erupcji według kategorii",
        color="Kategoria",
        color_discrete_map=category_colors
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🏳️ Erupcje według Krajów")

country_counts = filtered_df["Country"].value_counts().reset_index()
country_counts.columns = ["Kraj", "Liczba Erupcji"]
country_counts["Kontynent"] = country_counts["Kraj"].map(country_to_continent).fillna("Nieznany")

country_counts = country_counts[country_counts["Liczba Erupcji"] > min_number_of_eruptions_for_single_country]

fig_bar = px.bar(
    country_counts,
    x="Kraj",
    y="Liczba Erupcji",
    color="Kontynent",
    color_discrete_map=continent_colors,
    title=f"Erupcje według krajów (więcej niż {min_number_of_eruptions_for_single_country})"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("🌍 Erupcje według Kontynentów")
continent_counts = filtered_df["Continent"].value_counts().reset_index()
continent_counts.columns = ["Kontynent", "Liczba Erupcji"]

fig_bar = px.bar(
    continent_counts,
    x="Kontynent",
    y="Liczba Erupcji",
    title="Liczba erupcji według kontynentów",
    color="Kontynent",
    color_discrete_map=continent_colors
)
st.plotly_chart(fig_bar, use_container_width=True)

fig_pie = px.pie(
    continent_counts,
    names="Kontynent",
    values="Liczba Erupcji",
    title="Procentowy udział erupcji według kontynentów",
    color="Kontynent",
    color_discrete_map=continent_colors
)
st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("🗺️ Gęstość Erupcji według Krajów")

choropleth_df = filtered_df.groupby("ISO3").size().reset_index(name="Liczba Erupcji")
with COUNTRIES_DATA.open("r", encoding="utf-8") as f:
    geojson = json.load(f)

eruption_dict = dict(zip(choropleth_df["ISO3"], choropleth_df["Liczba Erupcji"]))
max_eruptions = max(eruption_dict.values())
norm = Normalize(vmin=0, vmax=max_eruptions)
cmap = cm.get_cmap("Oranges")

for feature in geojson["features"]:
    iso = feature["properties"]["ISO3166-1-Alpha-3"]
    eruptions = eruption_dict.get(iso, 0)
    color_rgba = cmap(norm(eruptions))
    feature["properties"]["Liczba Erupcji"] = eruptions
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

tooltip = {
    "html": "<b>{name}</b><br>Liczba erupcji: {Liczba Erupcji}",
    "style": {"backgroundColor": "black", "color": "white"}
}

st.pydeck_chart(pdk.Deck(
    layers=[geo_layer],
    initial_view_state=view_state,
    tooltip=tooltip
))

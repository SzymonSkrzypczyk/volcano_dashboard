import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
from matplotlib.colors import Normalize, to_hex
from matplotlib import cm
import plotly.express as px
import json
import geopandas as gpd

from country_continent_mapper import country_to_continent
from data_processing import combined, COUNTRIES_DATA
from config import continent_colors, min_number_of_eruptions_for_single_country, vei_colors, category_colors

gdf_bound = gpd.read_file("data/tect/PB2002_boundaries.shp")
gdf_orogens = gpd.read_file("data/tect/PB2002_orogens.shp")
gdf_plates = gpd.read_file("data/tect/PB2002_plates.shp")

gdf_plates.rename(columns={"PlateName": "name"}, inplace=True)
gdf_orogens.rename(columns={"Name": "name"}, inplace=True)
gdf_bound.rename(columns={"Name": "name"}, inplace=True)

gdf_bound1 = gdf_bound[gdf_bound['Type'] == 'subduction']
gdf_bound2 = gdf_bound[gdf_bound['Type'].isna()]

gdf_bound1 = gdf_bound1.to_crs(epsg=4326)
gdf_bound2 = gdf_bound2.to_crs(epsg=4326)
gdf_orogens = gdf_orogens.to_crs(epsg=4326)
gdf_plates = gdf_plates.to_crs(epsg=4326)

rift_geojson1 = json.loads(gdf_bound1.to_json())
rift_geojson2 = json.loads(gdf_bound2.to_json())
orogen_geojson = json.loads(gdf_orogens.to_json())
plates_geojson = json.loads(gdf_plates.to_json())

st.set_page_config(page_title="Dashboard Wybuchów Wulkanicznych", layout="wide")
tab1, tab2 = st.tabs(["Główna", "Strefy ryftowe"])

with tab1:
    st.title("Dashboard Wybuchów Wulkanicznych")

    st.sidebar.header("Filtruj wybuchy")
    min_year = int(combined["Start Year"].min())
    max_year = int(combined["Start Year"].max())
    year_range = st.sidebar.slider("Zakres lat", min_year, max_year, (0, max_year))
    vei_options = st.sidebar.multiselect("VEI", sorted(combined["VEI"].dropna().unique()),
                                        default=sorted(combined["VEI"].dropna().unique()))

    with st.sidebar.expander("ℹWyjaśnienie terminów"):
        st.markdown("""
        **VEI (Wulkaniczny Indeks Eksplozji):** Skala od 0 (nieeksplozyjny) do 8 (mega-kolosalny).  
        **Kategoria wybuchu:** Typ erupcji.  
        **Metoda dowodu:** Sposób datowania erupcji.  
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
        "html": "<b>{Volcano Name}</b><br>Rok: {Start Year}<br>VEI: {VEI}<br>Kraj: {Country}<br>Kategoria: {Eruption Category}",
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.subheader("Lokalizacje wulkanów")
    st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state, tooltip=tooltip))

    heat_layer = pdk.Layer(
        "HeatmapLayer",
        data=filtered_df,
        get_position='[Longitude, Latitude]',
        aggregation='MEAN',
        get_weight=1,
        radiusPixels=60,
    )

    st.subheader("Mapa gęstości wybuchów")
    st.pydeck_chart(pdk.Deck(layers=[heat_layer], initial_view_state=view_state))

    st.subheader("📆 Wybuchy według lat")
    year_counts = filtered_df["Start Year"].value_counts().sort_index()
    st.bar_chart(year_counts)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Wybuchy według VEI")
        vei_counts = filtered_df["VEI"].value_counts().sort_index().reset_index()
        vei_counts.columns = ["VEI", "Liczba"]
        vei_counts["VEI"] = vei_counts["VEI"].astype(str)

        fig = px.bar(
            vei_counts,
            x="VEI",
            y="Liczba",
            title="Wybuchy według VEI",
            color="VEI",
            color_discrete_map=vei_colors,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Kategorie wybuchów (skala logarytmiczna)")
        counts = filtered_df["Eruption Category"].value_counts()
        log_counts = np.log(counts)
        df_cat = pd.DataFrame({
            "Category": counts.index,
            "Liczba": counts.values,
            "Log Count": log_counts.values
        })
        fig = px.bar(
            df_cat,
            x="Category",
            y="Log Count",
            hover_data=["Liczba"],
            title="Liczba wybuchów (skala logarytmiczna)",
            color="Category",
            color_discrete_map=category_colors
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Wybuchy według krajów")

    country_counts = filtered_df["Country"].value_counts().reset_index()
    country_counts.columns = ["Country", "Liczba wybuchów"]

    country_counts["Continent"] = country_counts["Country"].map(country_to_continent).fillna("Nieznany")
    country_counts = country_counts[country_counts["Liczba wybuchów"] > min_number_of_eruptions_for_single_country]

    fig_bar = px.bar(
        country_counts,
        x="Country",
        y="Liczba wybuchów",
        color="Continent",
        color_discrete_map=continent_colors,
        title=f"Wybuchy według krajów (więcej niż {min_number_of_eruptions_for_single_country} wybuchów)"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Wybuchy według kontynentów")

    continent_counts = filtered_df["Continent"].value_counts().reset_index()
    continent_counts.columns = ["Continent", "Liczba wybuchów"]
    fig_bar = px.bar(
        continent_counts,
        x="Continent",
        y="Liczba wybuchów",
        title="Wybuchy według kontynentów",
        color="Continent",
        color_discrete_map=continent_colors
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    fig_pie = px.pie(
        continent_counts,
        names="Continent",
        values="Liczba wybuchów",
        title="Procentowy udział wybuchów według kontynentu",
        color="Continent",
        color_discrete_map=continent_colors
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    choropleth_df = filtered_df.groupby("ISO3").size().reset_index(name="Liczba wybuchów")
    with COUNTRIES_DATA.open("r", encoding="utf-8") as f:
        geojson = json.load(f)

    eruption_dict = dict(zip(choropleth_df["ISO3"], choropleth_df["Liczba wybuchów"]))
    max_eruptions = max(eruption_dict.values()) if eruption_dict else 1

    norm = Normalize(vmin=0, vmax=max_eruptions)
    cmap = cm.get_cmap("Oranges")

    for feature in geojson["features"]:
        iso = feature["properties"]["ISO3166-1-Alpha-3"]
        eruptions = eruption_dict.get(iso, 0)
        color_rgba = cmap(norm(eruptions))
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

    tooltip = {
        "html": "<b>{name}</b><br>Liczba wybuchów: {eruption_count}",
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.subheader("Gęstość wybuchów według krajów")
    st.pydeck_chart(pdk.Deck(
        layers=[geo_layer],
        initial_view_state=view_state,
        tooltip=tooltip
    ))

with tab2:
    st.subheader("Wybuchy wulkaniczne w kontekście stref ryftowych")
    col1, col2, col3 = st.columns(3)
    st.sidebar.header("Włącz warstwy tektoniczne")
    with col1:
        show_rift = st.checkbox("Pokaż granice płyt tektonicznych", value=True)
    with col3:
        show_orogen = st.checkbox("Pokaż orogeny", value=False)
    with col2:
        show_plates = st.checkbox("Pokaż płyty tektoniczne", value=False)

    layers = [scatter_layer]

    if show_rift:
        rift_layer1 = pdk.Layer(
            "GeoJsonLayer",
            rift_geojson1,
            pickable=True,
            stroked=True,
            filled=False,
            get_line_color=[100, 200, 100],
            line_width_min_pixels=3,
            auto_highlight=True,
        )
        rift_layer2 = pdk.Layer(
            "GeoJsonLayer",
            rift_geojson2,
            pickable=True,
            stroked=True,
            filled=False,
            get_line_color=[100, 100, 200],
            line_width_min_pixels=3,
            auto_highlight=True,
        )
        layers.append(rift_layer1)
        layers.append(rift_layer2)

    if show_plates:
        plates_layer = pdk.Layer(
            "GeoJsonLayer",
            plates_geojson,
            pickable=True,
            stroked=True,
            filled=True,
            get_fill_color=[100, 200, 100, 30],
            get_stroke_color=[100, 100, 100],
            line_width_min_pixels=1,
            auto_highlight=True,
        )
        layers.append(plates_layer)

    if show_orogen:
        orogen_layer = pdk.Layer(
            "GeoJsonLayer",
            orogen_geojson,
            pickable=True,
            stroked=False,
            filled=True,
            get_fill_color=[200, 100, 200, 70],
            line_width_min_pixels=3,
            auto_highlight=True,
        )
        layers.append(orogen_layer)

    tooltip2 = {
        "html": "<b>{name}</b><br>",
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, tooltip=tooltip2))

    st.markdown("""
    ### Wulkany i strefy ryftowe

    #### Czym jest ryft?
    Ryft to miejsce, gdzie skorupa ziemska jest rozciągana, tworząc szczelinę (zwykle na skutek konwekcji).  
    Gorący materiał (np. magma) z wnętrza Ziemi wypływa przez tę szczelinę, ochładza się i tworzy wulkan.

    #### Subdukcja
    Subdukcja to proces powstający wskutek ruchu płyt tektonicznych wywołanego rozciąganiem litosfery.  
    Gdy płyty oceaniczne i kontynentalne się zderzają, płyta kontynentalna unosi się, a oceaniczna zanurza pod nią.  
    Zanurzona płyta topnieje, a uwolniona woda obniża temperaturę topnienia skał, co sprzyja powstawaniu wulkanów.  
    Wulkany powstałe przez subdukcję zwykle nie leżą dokładnie na granicy subdukcji, lecz nieco na boku.

    Na mapie strefy ryftowe oznaczono kolorem niebieskim, a subdukcję zielonym.
    """)

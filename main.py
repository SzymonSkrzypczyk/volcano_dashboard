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

#loading rift files
gdf_bound = gpd.read_file("data/tect/PB2002_boundaries.shp")
gdf_orogens = gpd.read_file("data/tect/PB2002_orogens.shp")
gdf_plates = gpd.read_file("data/tect/PB2002_plates.shp")

gdf_plates.rename(columns={"PlateName": "name"},inplace=True)
gdf_orogens.rename(columns={"Name": "name"},inplace=True)
gdf_bound.rename(columns={"Name": "name"},inplace=True)

gdf_bound1 = gdf_bound[gdf_bound['Type'] == 'subduction']
gdf_bound2 = gdf_bound[gdf_bound['Type'].isna()]

gdf_bound1  = gdf_bound1.to_crs(epsg=4326)
gdf_bound2  = gdf_bound2.to_crs(epsg=4326)
gdf_orogens = gdf_orogens.to_crs(epsg=4326)
gdf_plates = gdf_plates.to_crs(epsg=4326)
#to json
rift_geojson1 = json.loads(gdf_bound1.to_json())
rift_geojson2 = json.loads(gdf_bound2.to_json())
orogen_geojson = json.loads(gdf_orogens.to_json())
plates_geojson = json.loads(gdf_plates.to_json())


st.set_page_config(page_title="Volcano Dashboard", layout="wide")
tab1, tab2 = st.tabs(["Main", "Rift zones"])

with tab1:
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
        vei_counts = filtered_df["VEI"].value_counts().sort_index().reset_index()
        vei_counts.columns = ["VEI", "Count"]
        vei_counts["VEI"] = vei_counts["VEI"].astype(str)

        fig = px.bar(
            vei_counts,
            x="VEI",
            y="Count",
            title="Eruptions by VEI",
            color="VEI",
            color_discrete_map=vei_colors,
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Eruption Categories (Log Scale)")
        counts = filtered_df["Eruption Category"].value_counts()
        log_counts = np.log(counts)
        df_cat = pd.DataFrame({
            "Category": counts.index,
            "Count": counts.values,
            "Log Count": log_counts.values
        })
        fig = px.bar(
            df_cat,
            x="Category",
            y="Log Count",
            hover_data=["Count"],
            title="Log-Scaled Eruption Counts",
            color="Category",
            color_discrete_map=category_colors
        )
        fig.update_layout(showlegend=False)
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

with tab2:
    st.subheader("Vulcanic Eruptions in the Context of Rift Zones")
    col1, col2, col3 = st.columns(3)
    st.sidebar.header("Toggle Tectonic Layers")
    with col1:
        show_rift = st.checkbox("Show Tectonic Plate Boundaries", value=True)
    with col3:
        show_orogen = st.checkbox("Show Orogens", value=False)
    with col2:
        show_plates = st.checkbox("Show Tectonic Plates", value=False)

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
        get_stroke_color=[100,100,100],
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

    st.pydeck_chart(pdk.Deck(layers=[layers], initial_view_state=view_state, tooltip=tooltip2))

    st.markdown("""
    ### Volcanoes and Rift Zones

    #### What is a Rift?
    A rift is often assiociated with formation of volanoes. It is a place where litosphere is pulled apart creating a gap (usually by convection). 
    Later, convection pushes the hot material (such as magma) from inside the Earth. When material reaches surface, it cools down and creates volcano.

    #### Subduction
    Subduction is a result of tectonic plate movement caused by rifting. When litosphere is pulled apart in one area, tectonic plates move and often collide with other plates. 
    When an oceanic plate and a continental plate meet, continental one goes up and the oceanic goes down due to difference in density. 
    Bottom plate is pushed down and melts due to the heat. Then the water that was trapped in that plate decreases heat needed to melt surrounding rocks. 
    This proces creates conditions favorable for the formation of vulcanoes. Subduction created vulcanoes are typically offset to subduction zone.

    On the map rift zones are blue and subduction zones are green.
    """)
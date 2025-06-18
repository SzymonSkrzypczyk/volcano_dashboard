from pathlib import Path
import pandas as pd
import geopandas as gpd
from country_continent_mapper import country_to_continent


RAW_DATA = Path("data/raw_data.csv")
ERUPTION_DATA = Path("data/eruption_data.pkl")
COUNTRIES_DATA = Path("data/countries.geojson")

eruption_data = pd.read_pickle(ERUPTION_DATA)

_volcano_df = pd.read_csv(RAW_DATA, skiprows=1)
_countries_gdf = gpd.read_file(COUNTRIES_DATA)
volcano_gdf = gpd.GeoDataFrame(
    _volcano_df,
    geometry=gpd.points_from_xy(_volcano_df["Longitude"], _volcano_df["Latitude"]),
    crs="EPSG:4326"
)
_countries_gdf = _countries_gdf.to_crs(volcano_gdf.crs)
combined = gpd.sjoin(volcano_gdf, _countries_gdf, how="left", predicate="within")
combined = combined.rename(
    columns={"name": "Country", "ISO3166-1-Alpha-3": "ISO3", "ISO3166-1-Alpha-2": "ISO2"})

combined['Continent'] = combined["Country"].map(country_to_continent).fillna('Unknown')

if __name__ == '__main__':
    print(combined.head().columns)
    print(combined['Eruption Category'].unique())

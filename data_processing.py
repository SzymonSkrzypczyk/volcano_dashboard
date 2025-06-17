from pathlib import Path
import pandas as pd
import geopandas as gpd
import pycountry
import pycountry_convert as pc

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

def country_name_to_continent(country_name):
    try:
        # Try to get the country from pycountry
        country = pycountry.countries.lookup(country_name)
        iso2 = country.alpha_2
        continent_code = pc.country_alpha2_to_continent_code(iso2)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except Exception:
        return None

combined['Continent'] = combined['Country'].apply(country_name_to_continent)

if __name__ == '__main__':
    print(combined.head().columns)
    print(combined['Continent'].unique())

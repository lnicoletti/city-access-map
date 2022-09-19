# %matplotlib inline
import glob
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import dask.dataframe as dd
import matplotlib.pyplot as plt

from pandana.loaders import osm
from pandana.loaders.pandash5 import network_to_pandas_hdf5
import pandana as pdna
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import osmnx as ox
from random import sample
from tqdm import tqdm

# from scipy.stats import mstats
# from shapely.geometry import Polygon
# import seaborn as sns
# from urban_access.data.urban_access import create_hexgrid, create_hex_access
directory = os.chdir(r'C:\Users\Leonardo\OneDrive\Documents\TU_Delft\CodingProjects\UrbanAccessibilityWorld')

print("loading data")
# download POIs at https://github.com/MorbZ/OsmPoisPbf/ using uac_filter.txt
df = pd.read_csv("data/raw/poi/poi.csv")
poi_types = pd.read_excel("data/raw/poi/poi_code_name_mapper.xlsx")
# download this data at http://cidportal.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_STAT_UCDB2015MT_GLOBE_R2019A/V1-2/
uc = pd.read_csv("data/raw/GHS_STAT_UCDB2015MT_GLOBE_R2019A/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.csv", encoding = "ISO-8859-1", engine='python')

print("preparing data")
uc = uc[['ID_HDC_G0', "CTR_MN_NM", "UC_NM_MN", "P15", "AREA"]].dropna()
# city + country
uc["UC_NM_CTR"] = uc["UC_NM_MN"] + ", " +  uc["CTR_MN_NM"]

df.ID_HDC_G0 = df.ID_HDC_G0.astype(int)
# merge df with uc data
df = df.merge(uc, on="ID_HDC_G0") 
poi_types = poi_types.replace(" ", np.NaN).dropna()
df = df.merge(poi_types, on="poi_type_id")
# make df of ratio poi/pop to filter data
df["count"] = 1
df_poi_per_pop = df.groupby(["ID_HDC_G0", "UC_NM_CTR"]).agg({"P15":"mean", "count":"sum", "AREA":"mean"}).reset_index()
df_poi_per_pop["poi_per_pop"] = df_poi_per_pop["count"]/df_poi_per_pop["P15"]
df_poi_per_pop["poi_per_km2"] = df_poi_per_pop["count"]/df_poi_per_pop["AREA"]

# list of urban centers to keep (at least 1 POI per km2)
uc_keep = df_poi_per_pop[(df_poi_per_pop.poi_per_km2>=1)&(df_poi_per_pop["count"]>=20)].ID_HDC_G0.to_list()
df_keep = df[df['ID_HDC_G0'].isin(uc_keep)]

#function to compute accessibility indicator for each category with regards to each node on the network
def create_access_gdf(pois = None, network = None, maxdist = 1000):
    
    '''Computes walking distances from each street intersection to each of the seven categories of urban amenities'''
    # precomputes the range queries (the reachable nodes within this maximum distance)
    # so, as long as you use a smaller distance, cached results will be used
    print("initialize network pois")
    # network.precompute(maxdist + 1)
#     # initialize the underlying C++ points-of-interest engine
#     network.init_pois(num_categories=num_categories, max_dist=maxdist, max_pois=num_pois)

    cat_list_str = list(pois.groupby(['category']).mean().reset_index()['category'])

    print("creating dummy df")
    #create dummy dataframe (only way of doing it so far is to run dummy network analysis at 1m)
    for cat in cat_list_str:
        pois_subset = pois[pois['category']==cat]
        network.set_pois(category = cat, maxdist = 1, maxitems=len(pois_subset), x_col=pois_subset['lon'], y_col=pois_subset['lat'])
        accessibility = network.nearest_pois(distance=1, category=cat) 
        
    print("calculating category distances")
    #now calculate distances
    for cat in cat_list_str:
        pois_subset = pois[pois['category']==cat]
        network.set_pois(category = cat, maxdist = maxdist, maxitems=len(pois_subset), 
                                 x_col=pois_subset['lon'], y_col=pois_subset['lat'])

        accessibility[str(cat)] = network.nearest_pois(distance=maxdist, category=cat) 

    print("cleaning up the output, adding metadata")
    #merge accessibility values with walk nodes ids geodataframe
    access = pd.merge(accessibility.reset_index().drop(1, axis=1),
                               network.nodes_df.reset_index(),
                               on='id')
    # add metadata
    access["ID_HDC_G0"] = pois["ID_HDC_G0"].unique()[0]
    access["CTR_MN_NM"] = pois["CTR_MN_NM"].unique()[0]
    access["UC_NM_MN"] = pois["UC_NM_MN"].unique()[0]
    access["P15"]	= pois["P15"].unique()[0]
    access["AREA"] = pois["AREA"].unique()[0]
    access["UC_NM_CTR"] = pois["UC_NM_CTR"].unique()[0]
    
    #convert to geodataframe
    access = gpd.GeoDataFrame(access, geometry=gpd.points_from_xy(access.x, access.y))
    #set right crs
    access.crs = {'init' :'epsg:4326'}
    
    #drop NaNs
    access = access.dropna()
#     access = access[~(access == 10000).any(1)].reset_index().drop('index', axis=1)

    return access

    ## %%time
print("beginning loop")
### global loop
# for city in sample(list(df_keep["ID_HDC_G0"].unique()), 2):
# for city in df_keep["ID_HDC_G0"].unique():

# processed cities
p_cities = [city.split(".")[0] for city in os.listdir("G:/UrbanAccessibilityWorld/data/processed/access/")]
# remaning cities
r_cities = list(df_keep[~df_keep["ID_HDC_G0"].isin(p_cities)].groupby("ID_HDC_G0").mean().sort_values("AREA", ascending=False).reset_index().ID_HDC_G0.unique())

# for city in tqdm(list(pd.DataFrame(df_keep.ID_HDC_G0.value_counts()).reset_index()["index"])[184:]):#[2:]
# for city in tqdm(r_cities[184:]):#[2:]
for city in tqdm(r_cities):#[2:]

    city_name = df_keep[df_keep["ID_HDC_G0"]==city]["UC_NM_CTR"].unique()[0]
    print(f"calculating accessibility for {city_name}")
    # subset pois for specific urban center
    pois = df_keep[df_keep["ID_HDC_G0"]==city]
    pois = gpd.GeoDataFrame(
        pois, geometry=gpd.points_from_xy(pois.lon, pois.lat))
    
    # get boundary coords of urban center
    lng_min = pois.total_bounds[0] #lng_min
    lat_min = pois.total_bounds[1] #lat_min
    lng_max = pois.total_bounds[2] #lng_max
    lat_max = pois.total_bounds[3] #lat_max
    
    # get pedestrian network
    network = osm.pdna_network_from_bbox(lat_min, lng_min, lat_max, lng_max, network_type='walk')
    access = create_access_gdf(pois = pois, network = network, maxdist = 5000)
    
    access.to_csv(f"G:/UrbanAccessibilityWorld/data/processed/access/{city}.csv")
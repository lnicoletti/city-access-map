from tqdm import tqdm
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
import os

localDir = "C:/Users/Leonardo/OneDrive/Documents/TU_Delft/CodingProjects/UrbanAccessibilityWorld"
popDir = "G:/CodingProjects/leoTemp/data/processed/UApolys"
accessDir = "G:/CodingProjects/UrbanAccessibilityWorld/data/processed/access/"
gridAccessDir = "G:/CodingProjects/UrbanAccessibilityWorld/data/processed/gridAccess"
aggDir = "G:/CodingProjects/UrbanAccessibilityWorld/data/processed/agg"


# urban centers database for later
uc = pd.read_csv(f"{localDir}/data/raw/GHS_STAT_UCDB2015MT_GLOBE_R2019A/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.csv", encoding = "ISO-8859-1", engine='python')
uc = uc[['ID_HDC_G0', "CTR_MN_NM", "UC_NM_MN", "P15", "AREA"]].dropna()
# city + country
uc["UC_NM_CTR"] = uc["UC_NM_MN"] + ", " +  uc["CTR_MN_NM"]
uc["ID_HDC_G0"] = uc["ID_HDC_G0"].astype("int")

#function to create accessibility by Hexagon
def create_hex_access(access = None, hexgrid = None, fillna = None, fillna_value = None, sjoin_method = "nearest", joinMethod='left', idCol="index", outputShape="grid"):
    
    '''Computes average accessibility per hexagon by taking the average of walking distances within each hexagon
        
    Args: 
        access (GeoDataFrame) : Point GeoDataFrame with distance values.
        hexgrid : hexagon grid
    
    Returns:
        gdf (GeoDataFrame) : Hexagon grid GeoDataFrame with averaged distance values for each category of amenities.

    '''
    
    #join transit access points to census
    hexgrid = hexgrid.reset_index()
    
    if sjoin_method == "nearest":
        hex_access = gpd.sjoin_nearest(hexgrid, access, how=joinMethod, max_distance=0.0003)
    else:
        hex_access = gpd.sjoin(hexgrid, access, how=joinMethod)



    hex_access[idCol] = hex_access[idCol] 
    hex_access = hex_access.groupby(idCol).median()
#     hex_access = hex_access[["mobility", "active_living", "nightlife", "food_choices",
#                                    "community_space", "education", "health_wellbeing"]]
    
    #hex_access = hex_access.fillna(method = 'ffill')
    if fillna_value == None:
        if fillna == None:
            hex_access = hex_access.dropna()
        elif fillna != None:
            hex_access = hex_access.fillna(method = fillna)
    else:
#         hex_access = hex_access.fillna(hex_access.max(), downcast='infer')
        hex_access = hex_access.fillna(value = fillna_value)
#         hex_access = hex_access.fillna(method = 'ffill')


#     hex_access = access.merge(hex_access, on='id')

    if outputShape == "access":
        hex_access = access.merge(hex_access, on=idCol)
#         hex_access = hex_access.drop(f'{idCol}_right',axis=1)
    else:
        hex_access = hexgrid.merge(hex_access, on=idCol)
        hex_access = hex_access.drop(f'index_right',axis=1)
    
    
    return hex_access


popData = [file.split(".")[0] for file in os.listdir(popDir) if file.split(".")[1] == "shp"]
accessData = [city.split(".")[0] for city in os.listdir(accessDir)]


# processed cities
p_cities = [city.split(".")[0] for city in os.listdir(gridAccessDir)]
# remaning cities
r_cities = [city for city in popData if city not in p_cities]


# loop for each individual city
for UA in tqdm(r_cities):
    # loop through each city and average access within each population cell
    uaAccess = pd.read_csv(f"{accessDir}/{UA}.csv")#[["id",	"active_living",	"community_space",	"education",	"food_choices",	"health_wellbeing",	"mobility",	"nightlife",	"x",	"y",	"ID_HDC_G0",	"CTR_MN_NM",	"UC_NM_MN",	"P15",	"AREA",	"UC_NM_CTR",	"geometry"]]
    uaPop = gpd.read_file(f"{popDir}/{UA}.shp")
    uaPop = uaPop.to_crs("EPSG:4326")
    uaAccess_gdf = gpd.GeoDataFrame(
                    uaAccess, geometry=gpd.points_from_xy(uaAccess.x, uaAccess.y, crs="EPSG:4326"))
    
    gridAccess = create_hex_access(access = uaAccess_gdf, hexgrid = uaPop, fillna = None, fillna_value = None, sjoin_method="nearest")
    
    gridAccess["lng"] = gridAccess.geometry.centroid.x
    gridAccess["lat"] = gridAccess.geometry.centroid.y
    t = pd.DataFrame(gridAccess.drop(columns=["index", "VALUE_x", "id", "x", "y", "AREA", "P15", "geometry", "Unnamed: 0"]))
    t = t.rename(columns={"VALUE_y":"POP_2015"})
    
    # reduce data size by convertinh floats to integers
    accessCols = ['active_living', 'community_space', 'education', 'food_choices', 'health_wellbeing', 'nightlife', 'mobility']
    convert_dict = {col: int for col in t.columns if col in accessCols}
 
    t = t.astype(convert_dict)
    t["POP_2015"] = t["POP_2015"].round(0).astype(int)
    t["ID_HDC_G0"] = t["ID_HDC_G0"].astype(int)
    # t = t[t["POP_2015"]!=0]
    
    # save final dataset
    t.to_csv(f"{gridAccessDir}/{UA}.csv")
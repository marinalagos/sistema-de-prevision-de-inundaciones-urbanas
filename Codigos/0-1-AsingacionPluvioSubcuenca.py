import pandas as pd
import xarray as xr
from shapely.geometry import Polygon, MultiPoint, Point
import pyproj
from scipy.spatial import KDTree
from glob import glob

# DEFINIR PYTHONPATH (directorio raíz del repositorio)
# Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
repo_path = os.getenv('PYTHONPATH')
if repo_path:
    os.chdir(repo_path)
    
inp_file = 'Carpeta_base_SWMM/model_base.inp'
nc_file = glob('Carpeta_base_SWMM/*.nc')[0]

with open(inp_file) as f:
    lines = f.readlines()

# Extracción de tabla de subcuencas:
inicio = lines.index('[SUBCATCHMENTS]\n') + 3
fin = lines.index('[SUBAREAS]\n') -1
lines_subcuencas = lines[inicio:fin]
df_subcuencas = pd.DataFrame([i.split() for i in lines_subcuencas], columns=['Name', 'RainGage', 'Outlet', 'Area', 'Imperv', 'Width', 'Slope', 'CurbLen'])
df_subcuencas = df_subcuencas.set_index('Name')

ini = lines.index('[Polygons]\n') + 3
fin = lines.index('[SYMBOLS]\n') -1
lines_polygons = lines[ini:fin]
df_polygons = pd.DataFrame([i.split() for i in lines_polygons], columns=['subcatchment', 'xcoord', 'ycoord'])
df_polygons = df_polygons.set_index('subcatchment')

# CSR Posgar 2007 Faja 5 (código EPSG: 5347)
origen = pyproj.CRS.from_epsg(5347)
# WGS84 (código EPSG: 4326)
destino = pyproj.CRS.from_epsg(4326)
# Crea un transformador de coordenadas
posgar2geo = pyproj.Transformer.from_crs(origen, destino, always_xy=True)

subc = df_polygons.index[0]
coords = []
subc_centroid = {}
for index, row in df_polygons.iterrows():
    if index == subc:
        xcoord, ycoord = float(row.xcoord), float(row.ycoord)
        xcoord, ycoord = posgar2geo.transform(xcoord, ycoord)        
        coords.append((xcoord, ycoord))

    else:
        polygon = Polygon(coords)
        centroid = polygon.centroid
        subc_centroid[subc] = centroid

        subc = index
        xcoord, ycoord = float(row.xcoord), float(row.ycoord)
        xcoord, ycoord = posgar2geo.transform(xcoord, ycoord)        
        coords = [(xcoord, ycoord)]

puntos = list(subc_centroid.values())
multi_point = MultiPoint(puntos)
minlon, minlat, maxlon, maxlat = multi_point.bounds
#------------------------------------------------------------------------#
ds = xr.open_dataset(nc_file, decode_coords = 'all', engine = 'netcdf4')
ds1 = ds.where((ds.XLONG > minlon - .1) & (ds.XLONG < maxlon + .1)  & (ds.XLAT > minlat - .1) & (ds.XLAT < maxlat + .1), drop=True)

lats = ds1.XLAT.values
lons = ds1.XLONG.values

cell_coords = {}
for lat in lats:
    str_lat = f'{(round(lat*-1000,0)):.0f}'
    for lon in lons:
        str_lon = f'{(round(lon*-1000,0)):.0f}'
        cell = f'P{str_lat}_{str_lon}'
        cell_coords[cell] = Point(lon, lat)

coordenadas1 = [p.coords[:][0] for p in subc_centroid.values()]
coordenadas2 = [p.coords[:][0] for p in cell_coords.values()]

# Crea un KDTree a partir de las coordenadas de diccionario2
kdtree = KDTree(coordenadas2)

# Encuentra el punto más cercano en diccionario2 para cada punto en diccionario1
puntos_mas_cercanos = {}
asignacion = {}
for clave1, coordenadas1 in zip(subc_centroid.keys(), coordenadas1):
    _, indice = kdtree.query(coordenadas1)
    punto_mas_cercano = cell_coords[list(cell_coords.keys())[indice]]
    puntos_mas_cercanos[clave1] = punto_mas_cercano
    asignacion[clave1] = list(cell_coords.keys())[indice]

df_sub_cell = pd.DataFrame.from_dict(asignacion, orient='index')
import pandas as pd
import xarray as xr
from shapely.geometry import Polygon, MultiPoint, Point
import pyproj
from scipy.spatial import KDTree
from glob import glob

# DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)



# ARCHIVOS DE ENTRADA
inp_file = 'Carpeta_base_SWMM/model_base.inp'
nc_file = glob('Carpeta_base_SWMM/*.nc')[0]



# SISTEMAS DE COORDENADAS
crs_SWMM = pyproj.CRS.from_epsg(5347) # CRS Posgar 2007 Faja 5 (código EPSG: 5347)
crs_netCDF = pyproj.CRS.from_epsg(4326) # WGS84 (código EPSG: 4326)
posgar2geo = pyproj.Transformer.from_crs(crs_SWMM, crs_netCDF, always_xy=True) # Conversor de coordenadas



# 1. EXTRACCIÓN DE CENTROIDES DE LOS POLÍGONOS DE SUBCUENCAS A PARTIR DEL .inp
# Abre el archivo de entrada y lee todas las líneas
with open(inp_file) as f:
    lines = f.readlines()

# Extracción de la tabla de polígonos del archivo .inp
ini = lines.index('[Polygons]\n') + 3
fin = lines.index('[SYMBOLS]\n') - 1
lines_polygons = lines[ini:fin]
df_polygons = pd.DataFrame([i.split() for i in lines_polygons], columns=['subcatchment', 'xcoord', 'ycoord'])
df_polygons = df_polygons.set_index('subcatchment')

# Inicializa la primera subcuenca y las listas para las coordenadas y centroides
subc = df_polygons.index[0]
coords = []
subc_centroid = {}

# Itera sobre cada fila del DataFrame de polígonos
for index, row in df_polygons.iterrows():
    # Si el índice es igual al subcuenca actual, va guardando las coordenadas
    if index == subc:
        xcoord, ycoord = float(row.xcoord), float(row.ycoord)
        xcoord, ycoord = posgar2geo.transform(xcoord, ycoord)        
        coords.append((xcoord, ycoord))
    # Si no, cierra el polígono, calcula el centroide, y pasa a la siguiente subcuenca
    else:
        polygon = Polygon(coords)
        centroid = polygon.centroid
        subc_centroid[subc] = centroid

        subc = index
        xcoord, ycoord = float(row.xcoord), float(row.ycoord)
        xcoord, ycoord = posgar2geo.transform(xcoord, ycoord)        
        coords = [(xcoord, ycoord)]

# Crea un MultiPoint a partir de los centroides
puntos = list(subc_centroid.values())
multi_point = MultiPoint(puntos)
# Obtiene los límites (min/max) de las coordenadas de los centroides
minlon, minlat, maxlon, maxlat = multi_point.bounds



# 2. EXTRACCIÓN DE CENTROIDES DE LAS CELDAS DE PRECIPITACIÓN A PARTIR DEL .nc
ds = xr.open_dataset(nc_file, decode_coords='all', engine='netcdf4')
ds1 = ds.where((ds.XLONG > minlon - .1) & (ds.XLONG < maxlon + .1) & 
               (ds.XLAT > minlat - .1) & (ds.XLAT < maxlat + .1), 
               drop=True)

lats = ds1.XLAT.values
lons = ds1.XLONG.values

cell_coords = {}

for lat in lats:
    # Formatea la latitud en un string para usar como clave
    str_lat = f'{(round(lat*-1000,0)):.0f}'
    for lon in lons:
        # Formatea la longitud en un string para usar como clave
        str_lon = f'{(round(lon*-1000,0)):.0f}'
        # Crea una clave única para la celda
        cell = f'P{str_lat}_{str_lon}'
        # Almacena las coordenadas de la celda en el diccionario
        cell_coords[cell] = Point(lon, lat)



# 3. ASIGNACIÓN SUBCUENCA-CELDA
coordenadas1 = [p.coords[:][0] for p in subc_centroid.values()]
coordenadas2 = [p.coords[:][0] for p in cell_coords.values()]

kdtree = KDTree(coordenadas2) # Crea un KDTree a partir de las coordenadas de las celdas

# Encuentra el punto más cercano en las celdas para cada centroide de subcuencas
puntos_mas_cercanos = {}
asignacion = {}
for clave1, coordenadas1 in zip(subc_centroid.keys(), coordenadas1):
    _, indice = kdtree.query(coordenadas1)  # Busca el índice del punto más cercano en el KDTree
    punto_mas_cercano = cell_coords[list(cell_coords.keys())[indice]]   # Obtiene el punto más cercano de las celdas
    puntos_mas_cercanos[clave1] = punto_mas_cercano
    asignacion[clave1] = list(cell_coords.keys())[indice]

# Crea un DataFrame a partir del diccionario de asignación
df_sub_cell = pd.DataFrame.from_dict(asignacion, orient='index')



# MODIFICACIÓN DE TABLA DE SUBCUENCAS EN EL ARCHIVO .inp
# Extracción de la tabla de subcuencas del archivo .inp
inicio = lines.index('[SUBCATCHMENTS]\n') + 3
fin = lines.index('[SUBAREAS]\n') - 1
lines_subcuencas = lines[inicio:fin]
df_subcuencas = pd.DataFrame([i.split() for i in lines_subcuencas], columns=['Name', 'RainGage', 'Outlet', 'Area', 'Imperv', 'Width', 'Slope', 'CurbLen'])
df_subcuencas = df_subcuencas.set_index('Name')

# Cruzar con el dataframe de asignación subcuenca-celda
df_subcuencas = pd.merge(df_subcuencas, df_sub_cell,
                        right_index = True, left_index = True,
                        how = 'left', sort = False)

df_subcuencas[0] = df_subcuencas[0].fillna(df_sub_cell.values[0][0]) # Para las celdas sin área, no hay celda asociada. En esos casos, se asigna una celda arbitraria (la primera de la lista)
df_subcuencas['RainGage'] = df_subcuencas[0]
df_subcuencas = df_subcuencas.drop(columns=[0])

str_subcatchments = df_subcuencas.to_string(index=True, header=False, index_names=False, justify='left')
# inicio = lines2.index('[SUBCATCHMENTS]\n') + 3
# fin = lines2.index('[SUBAREAS]\n') -1
# lines3 = lines2[:inicio] + [str_subcatchments] + ['\n'] + lines2[fin:]
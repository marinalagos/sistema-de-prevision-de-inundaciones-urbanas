import geopandas as gpd
import pandas as pd
from shapely import wkt
import os
import json
import numpy as np

# THIESSEN y IDW
# Inputs:
#   - Coordenadas de las estaciones puntuales
#   - Coordenadas de la grilla
#   - Datos de las estaciones puntuales
#   - EPSG
#   - potencia (IDW)
# Outputs:
#   - Datos asociados a las celdas de cada grilla

# #  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
# repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
# if repo_path:
#     os.chdir(repo_path)

# #  1. PARÁMETROS
# with open('PAQUETES/EMAs_INA_sim_continua/config_exp/config.json', 'r') as f:
#     content = f.read()
#     if not content.strip():
#         print("El archivo config.json está vacío.")
#     else:
#         params = json.loads(content)

# #  2. CREAR OUTPUTS DE PRUEBA

# gdf_grid = pd.read_csv(params['path_cell_coords'], index_col=0)
# gdf_grid['geometry'] = gdf_grid['Coordinates'].apply(wkt.loads)
# gdf_grid = gpd.GeoDataFrame(gdf_grid, geometry='geometry')
# gdf_grid.set_crs(epsg=params['epsg_precipitacion'], inplace=True)
# gdf_grid = gdf_grid['geometry']

# data = pd.read_csv('auxiliares/data.csv', index_col=0)
# gdf_data = pd.read_csv('auxiliares/coords_data.csv', index_col=0)
# gdf_data = gpd.GeoDataFrame(gdf_data, geometry=gpd.points_from_xy(gdf_data.lon, gdf_data.lat), crs=params['epsg_precipitacion'])
# gdf_data = gdf_data['geometry']


# epsg = params['epsg_SWMM']



def thiessen(data, geoseries_data, geoseries_grid, epsg):
    """
    Parameters:
      - data: Datos de las estaciones puntuales
      - geoseries_data: Coordenadas de las estaciones puntuales
      - geoseries_grid: Coordenadas de la grilla
      - EPSG
    
    Outputs:
      - Datos asociados a las celdas de cada grilla
    """

    # Definir proyección para el cálculo de la distancia
    gdf_data = geoseries_data.to_crs(epsg=epsg) 
    gdf_grid = geoseries_grid.to_crs(epsg=epsg).to_frame() # convertir a geodataframe

    # Crear una lista para almacenar el ID del punto más cercano en gdf_data
    nearest_ids = []

    # Iterar sobre cada punto en gdf_grid
    for geom in gdf_grid.geometry:
        # Calcular distancias de este punto a todos los puntos en gdf_data
        distances = gdf_data.geometry.distance(geom)
        
        # Obtener el índice del punto más cercano
        nearest_id = distances.idxmin()
        nearest_ids.append(nearest_id)

    # Agregar los IDs más cercanos como una nueva columna en gdf_grid
    gdf_grid['nearest_id'] = nearest_ids

    # Crear el dataset objetivo
    cells_data = []
    for idx, row in gdf_grid.iterrows():
        id_data = str(row.nearest_id)
        cells_data.append(data[id_data].rename(idx))

    grid_data = pd.concat(cells_data, axis=1)
    return grid_data

def idw(data, geoseries_data, geoseries_grid, epsg, p=2):
    """
    Parameters:
      - data: Datos de las estaciones puntuales
      - geoseries_data: Coordenadas de las estaciones puntuales
      - geoseries_grid: Coordenadas de la grilla
      - EPSG: tienen que ser coordenas proyectadas para poder medir distancias.
      - potencia (IDW)
    
    Outputs:
      - Datos asociados a las celdas de cada grilla
    """

    # Definir proyección para el cálculo de la distancia
    gdf_data = geoseries_data.to_crs(epsg=epsg) 
    gdf_grid = geoseries_grid.to_crs(epsg=epsg).to_frame() # convertir a geodataframe

    # Calcular valores para cada celda de la grilla
    grid_data = []
    for index, row in gdf_grid.iterrows():
        distances = gdf_data.geometry.distance(row.geometry)
        distances[distances == 0] = 1e-10 # evitar la división por cero
        weights = 1 / (distances ** p)
        values = []
        for id, w in weights.items():
            values.append(data[(id)]*w)
        cell_series = sum(values).rename(index)
        cell_series = cell_series/sum(weights)
        grid_data.append(cell_series)
    
    grid_data = pd.concat(grid_data, axis=1)

    return grid_data


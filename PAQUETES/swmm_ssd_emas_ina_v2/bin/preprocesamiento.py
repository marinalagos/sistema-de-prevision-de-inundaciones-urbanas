# -*- coding: utf-8 -*-

import os
import json
from TOOLS.consultar_base_ina import consultar_base_ina
from TOOLS.modificar_inp_base import modificar_inp_base
from TOOLS.setear_fechas_paths_inp import setear_fechas_paths_inp
from UTILS.utils_swmm.create_rainfall_file import create_rainfall_file
from UTILS.find_dir_lastest_file import find_dir_latest_file
from UTILS.utils_swmm.create_slurm_file import create_slurm_file
import UTILS.spatial_interpolation as spint
import pandas as pd
import argparse
import geopandas as gpd
from shapely import wkt

experimento = 'swmm_ssd_emas_ina_v2'

#  0. DEFINIR LA FECHA

parser = argparse.ArgumentParser(description="Script de preprocesamiento")
parser.add_argument("--inicio_sim", required=True, help="Timestamp en formato YYYY-MM-DDTHH:MM:SSZ")
args = parser.parse_args()
inicio_sim = args.inicio_sim
inicio_sim = pd.to_datetime(inicio_sim)
print(f"Inicio simulación: {inicio_sim}")

#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)

# 1. CONSULTAR ARCHIVOS .json 
# 1.a. Credenciales
with open('credenciales.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo credenciales.json está vacío.")
    else:
        token_base_INA = json.loads(content)['token_base_INA']

# 1.b. PARÁMETROS
with open(f'PAQUETES/{experimento}/config_exp/config.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo config.json está vacío.")
    else:
        params = json.loads(content)

fin_sim = inicio_sim + pd.Timedelta(minutes = params['frecuencia_min'])

# 2. DATOS DE PRECIPITACIÓN
# 2.a. CONSULTAR ALERTA INA
df_coords, df_pp = consultar_base_ina(inicio_sim = inicio_sim,
                                      fin_sim = fin_sim,
                                      token_base_INA = token_base_INA,
                                      params = params,
                                      )

# 2.b. INTERPOLACIÓN IDW (sin este paso se aplica Thiessen por defecto)
gdf_pluvios = gpd.GeoDataFrame(df_coords, 
                               geometry=gpd.points_from_xy(df_coords.lon, df_coords.lat), 
                               crs='EPSG:4326')

df_coords_grid = pd.read_csv(params['path_cell_coords'], index_col=0)

gdf_grid = gpd.GeoDataFrame(df_coords_grid, 
                            geometry=gpd.points_from_xy(df_coords_grid.lon, df_coords_grid.lat), 
                            crs='EPSG:4326')

df_pp_grid = spint.idw(data = df_pp,
                       geoseries_data = gdf_pluvios,
                       geoseries_grid = gdf_grid,
                       epsg = params['epsg_SWMM'],
                       p = params['potencia_idw'])


# 3. GENERAR ARCHIVO DE PRECIPITACIÓN
filepath_rainfall = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/p.txt'
create_rainfall_file(data = df_pp_grid,
                     file_path = filepath_rainfall)

# 4. MODIFICAR .INP BASE (ASIGNACIÓN PLUVIO-SUBCUENCAS)
modificar_inp_base(inp_file = params['inp_base'],
                   inp_file_modificado = params['inp_modificado'],
                   df_coords = df_coords_grid,
                   epsg_SWMM = params['epsg_SWMM'],
                   epsg_precipitacion = params['epsg_precipitacion'])

# 5. CONFIGURAR FECHAS Y PATHS CORRESPONDIENTES EN EL .INP
# 5.a. Encontrar el hotstart de inicio, como el más reciente
dirpath_lastest_hsf = find_dir_latest_file(root_dir = 'data/HIST/PREP/',
                                           experimento = 'swmm_ssd_emas_ina_v2',
                                           file_name = 'hotstart.hsf')
print(f'HSFin: {dirpath_lastest_hsf}')

# 5.b. Crear directorio para recibir los archivos de salida (.rpt, .out, .hsf)
dirpath_outputs = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'
if not os.path.exists(dirpath_outputs): 
    os.makedirs(dirpath_outputs)

# 5.c. Generar .inp con las fechas y los paths correspondientes
setear_fechas_paths_inp(inicio_sim = inicio_sim,
                        fin_sim = fin_sim,
                        inp_base_modificado = params['inp_modificado'],
                        filepath_HSin = f'{dirpath_lastest_hsf}/hotstart.hsf',
                        filepath_HSout = f'{dirpath_outputs}/hotstart.hsf', # Capaz no es necesario guardarlo
                        filepath_rainfall = filepath_rainfall,
                        dt_precipitacion_minutos = params['dt_precipitacion_minutos'],
                        pformat = params['pformat'],
                        dirpath_new_inp = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}'
                        )

# 6. GENERAR ARCHIVO .sh
create_slurm_file(path_slurm_file = f'PAQUETES/{experimento}/bin/run_swmm_{inicio_sim:%Y%m%d%H%M}.sh',
                  path_swmm = params['swmmexe'],
                  dirpath_model = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  dirpath_out = f'data/HIST/FCST/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  )



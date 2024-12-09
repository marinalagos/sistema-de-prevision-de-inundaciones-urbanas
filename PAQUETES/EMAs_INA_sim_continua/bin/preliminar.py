import os
import json
from glob import glob
from TOOLS.asignacion_pluvio_cuenca import asignacion_pluvio_cuenca
from TOOLS.consultar_emas_base_ina import consultar_emas_base_ina
from UTILS.utils_swmm import create_rainfall_file
import pandas as pd


inicio_sim = pd.to_datetime('2024-10-10 00:00', utc=True)
fin_sim = pd.to_datetime('2024-10-13 00:00', utc=True)
experimento = 'swmm_ssd_emas_ina'

#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)

# 1. CONSULTAR ARCHIVOS .json DE CREDENCIALES Y PARÁMETROS
# 1.a. Credenciales
with open('credenciales.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo credenciales.json está vacío.")
    else:
        token_base_INA = json.loads(content)['token_base_INA']

# 1.b. PARÁMETROS
with open('PAQUETES/EMAs_INA_sim_continua/config_exp/config.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo config.json está vacío.")
    else:
        params = json.loads(content)


# 2. ASIGNACIÓN PLUVIO CUENCA
asignacion_pluvio_cuenca(inp_file = params['inp_base'],
                         nc_file = params['nc_grid'], 
                         inp_file_modificado = params['inp_modificado'],
                         epsg_SWMM = params['epsg_SWMM'],
                         epsg_precipitacion = params['epsg_precipitacion'],
                         path_cell_coords = params['path_cell_coords'])

# 3. CONSULTAR EMAs BASE INA
grid_data = consultar_emas_base_ina(inicio_sim = inicio_sim,
                                    fin_sim = fin_sim,
                                    token_base_INA = token_base_INA,
                                    params = params)

# 4. GENERAR ARCHIVO DE PRECIPITACIÓN
create_rainfall_file(data = grid_data,
                     file_path = f'data/HIST/OBS/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/p.txt')

# 5. CORRER SWMM
# 
# 6. GUARDAR OUTPUT
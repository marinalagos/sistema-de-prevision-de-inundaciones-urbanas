import os
import json
from glob import glob
from TOOLS.asignacion_pluvio_cuenca import asignacion_pluvio_cuenca
from TOOLS.consultar_emas_base_ina import consultar_emas_base_ina
from TOOLS.crear_inp import crear_inp
from UTILS.utils_swmm.create_rainfall_file import create_rainfall_file
from UTILS.find_dir_lastest_file import find_dir_latest_file
from UTILS.utils_swmm.create_slurm_file import create_slurm_file
import pandas as pd


inicio_sim = pd.to_datetime('2024-12-19 04:00', utc=True)
fin_sim = pd.to_datetime('2024-12-19 05:00', utc=True)
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
with open(f'PAQUETES/{experimento}/config_exp/config.json', 'r') as f:
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
                     file_path = f'data/HIST/OBS/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/')

# 5. GENERAR ARCHIVO .inp

# 5.a. Encontrar el hotstart de inicio, como el más reciente
pathdir_lastest_hsf = find_dir_latest_file(root_dir = 'data/HIST/PREP/',
                                           experimento = 'swmm_ssd_emas_ina',
                                           file_name = 'hotstart.hsf')

# 5.b. Crear archivo .inp
crear_inp(inicio_sim = inicio_sim,
          fin_sim = fin_sim,
          experimento = experimento,
          inp_base = params['inp_modificado'],
          pathdir_hsf = pathdir_lastest_hsf)

# 5.c. Crear la carpeta para el hotstart de salida
pathdir_out_hsf = f'data/HIST/PREP/{fin_sim:%Y/%m/%d/%H%M%S}/{experimento}/'
if not os.path.exists(pathdir_out_hsf): 
    os.makedirs(pathdir_out_hsf)


# 6. GENERAR ARCHIVO .sh
create_slurm_file(path_slurm_file = f'PAQUETES/{experimento}/bin/run_swmm.sh',
                  path_swmm = params['swmmexe'],
                  pathdir_model = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  pathdir_out = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  jobname = f'{experimento}_{inicio_sim:%Y%m%d%H%M}',
                  # PENSAR SI HAY ALGUNA UBICACIÓN MEJOR PARA EL LOG
                  logfile = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/log.txt',
                  nodelist = params['nodelist'],
                  cpupertask = params['cpupertask']
                  )

# 5. CORRER SWMM
# 6. GUARDAR OUTPUT

# output_path = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'

# if not os.path.exists(output_path): 
#     os.makedirs(output_path) # PENSAR QUE VA ACA!!!!
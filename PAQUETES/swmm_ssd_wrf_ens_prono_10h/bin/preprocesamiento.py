# -*- coding: utf-8 -*-

import os
import json
from glob import glob
from TOOLS.asignacion_pluvio_cuenca import asignacion_pluvio_cuenca
from TOOLS.consultar_aws import consultar_aws
from TOOLS.modificar_inp_base import modificar_inp_base
from TOOLS.setear_fechas_paths_inp import setear_fechas_paths_inp
from UTILS.utils_swmm.create_rainfall_file import create_rainfall_file
from UTILS.find_dir_lastest_file import find_dir_latest_file
from UTILS.utils_swmm.create_slurm_file import create_slurm_file
import pandas as pd
import argparse

experimento = 'swmm_ssd_wrf_ens_prono_10h'

#  0. DEFINIR LA FECHA

parser = argparse.ArgumentParser(description="Script de preprocesamiento")
parser.add_argument("--inicio_sim", required=True, help="Timestamp en formato YYYY-MM-DDTHH:MM:SSZ")
args = parser.parse_args()
inicio_sim = args.inicio_sim
inicio_sim = pd.to_datetime(inicio_sim)
print(f"Inicio simulación: {inicio_sim}")

now = pd.Timestamp.now(tz='utc')
inicio_sim = pd.Timestamp(year=now.year, month=now.month, day=now.day, hour=now.hour, tz='utc')


# inicio_sim = pd.to_datetime('2024-12-26 19:00', utc=True)

#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)



# 1. CONSULTAR ARCHIVOS .json DE PARÁMETROS
with open(f'PAQUETES/{experimento}/config_exp/config.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo config.json está vacío.")
    else:
        params = json.loads(content)

fin_sim = inicio_sim + pd.Timedelta(minutes = params['frecuencia_min'])



# 2. CONSULTAR AWS
df_coords, df_pp = consultar_aws(duracion_PHH = 10,
                                 duracion_PM  = 72,
                                 fecha_inicio = inicio_sim)



# 3. GENERAR ARCHIVO DE PRECIPITACIÓN
filepath_rainfall = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/p.txt'
create_rainfall_file(data = df_pp,
                     file_path = filepath_rainfall)



# 4. MODIFICAR .INP BASE (ASIGNACIÓN PLUVIO-SUBCUENCAS)
modificar_inp_base(inp_file = params['inp_base'],
                   inp_file_modificado = params['inp_modificado'],
                   df_coords = df_coords,
                   epsg_SWMM = params['epsg_SWMM'],
                   epsg_precipitacion = params['epsg_precipitacion'])



# 5. CONFIGURAR FECHAS Y PATHS CORRESPONDIENTES EN EL .INP
# 5.a. Encontrar el hotstart de inicio, como el más reciente
dirpath_lastest_hsf = find_dir_latest_file(root_dir = 'data/HIST/PREP/',
                                           experimento = 'swmm_ssd_emas_ina',
                                           file_name = 'hotstart.hsf')
print(f'HSFin: {dirpath_lastest_hsf}')

# 5.b. Crear directorio para recibir los archivos de salida (.rpt, .out, .hsf)
dirpath_outputs = f'data/HIST/FCST/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'
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
                        filepath_new_inp = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/model.inp'
                        )



# 6. GENERAR ARCHIVO .sh
create_slurm_file(path_slurm_file = f'PAQUETES/{experimento}/bin/run_swmm_{inicio_sim:%Y%m%d%H%M}.sh',
                  path_swmm = params['swmmexe'],
                  pathdir_model = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  pathdir_out = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/',
                  jobname = f'{experimento}_{inicio_sim:%Y%m%d%H%M}',
                  # PENSAR SI HAY ALGUNA UBICACIÓN MEJOR PARA EL LOG
                  logfile = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/log.txt',
                  nodelist = params['nodelist'],
                  cpupertask = params['cpupertask'],
                  errorfile = f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/error.txt'
                  )

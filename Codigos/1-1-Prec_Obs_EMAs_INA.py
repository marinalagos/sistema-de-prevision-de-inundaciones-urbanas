import pandas as pd
import requests
import json
import os
import argparse

# 0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)



# 1. PARSEAR INPUTS
# Crear el parser
parser = argparse.ArgumentParser(description='Procesar archivos de entrada y NetCDF.')

# Añadir los argumentos que esperas recibir
parser.add_argument('inicio_sim', 
                    type = str, 
                    help = 'Timestamp (UTC) del inicio de la simulación. Formato: yyyy-mm-dd hh:mm'
                    )

parser.add_argument('fin_sim', 
                    type = str, 
                    help = 'Timestamp (UTC) del fin de la simulación. Formato: yyyy-mm-dd hh:mm'
                    )

parser.add_argument('--cell_coords', 
                    type = str, 
                    help = 'Ruta al .csv con las coordenadas de la grilla.',
                    default = 'Carpeta_base_SWMM/coordenadas_celdas.csv'
                    )

# Parsear los argumentos
args = parser.parse_args()

inicio_sim = pd.to_datetime(args.inicio_sim, utc=True)
fin_sim = pd.to_datetime(args.fin_sim, utc=True)
path_cell_cords = args.cell_coords

                    

# 2. CONSULTAR ARCHIVOS .json DE CREDENCIALES Y PARÁMETROS
# Credenciales
with open('credenciales.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo credenciales.json está vacío.")
    else:
        token_base_INA = json.loads(content)['token_base_INA']

# EMAs a consultar
with open('config.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo config.json está vacío.")
    else:
        params_base_INA = json.loads(content)['params_base_INA']



# 3. CONSULTA A LA BASE DEL INA
ids_serie = params_base_INA['ids_EMAs_consultadas']    

for id_serie in ids_serie:
    print(id_serie)
    response = requests.get(
    f"https://alerta.ina.gob.ar/a6/obs/puntual/series/{id_serie}/observaciones", 
    headers={'Authorization': f'Bearer {token_base_INA}'}, 
    params={'timestart': '2024-09-13', 'timeend': '2024-09-15'}
    )
    print(response.json())

import pandas as pd
import requests
import json
import os

# DEFINIR PYTHONPATH (directorio raíz del repositorio)
# Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
repo_path = os.getenv('PYTHONPATH')
if repo_path:
    os.chdir(repo_path)

# CONSULTA ARCHIVOS .json DE CREDENCIALES Y PARÁMETROS

with open('credenciales.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo credenciales.json está vacío.")
    else:
        token_base_INA = json.loads(content)['token_base_INA']

# Obtener listado de EMAs a consultar

with open('config.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo config.json está vacío.")
    else:
        params_base_INA = json.loads(content)['params_base_INA']

# CONSULTA A LA BASE DEL INA
ids_serie = params_base_INA['ids_EMAs_consultadas']    

for id_serie in ids_serie:
    print(id_serie)
    response = requests.get(
    f"https://alerta.ina.gob.ar/a6/obs/puntual/series/{id_serie}/observaciones", 
    headers={'Authorization': f'Bearer {token_base_INA}'}, 
    params={'timestart': '2024-09-13', 'timeend': '2024-09-15'}
    )
    print(response.json())

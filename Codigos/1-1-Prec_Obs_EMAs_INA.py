import pandas as pd
import requests
import json
import os
import argparse

# 0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)



# # 1. PARSEAR INPUTS
# # Crear el parser
# parser = argparse.ArgumentParser(description='Procesar archivos de entrada y NetCDF.')

# # Añadir los argumentos que esperas recibir
# parser.add_argument('inicio_sim', 
#                     type = str, 
#                     help = 'Timestamp (UTC) del inicio de la simulación. Formato: yyyy-mm-dd hh:mm'
#                     )

# parser.add_argument('fin_sim', 
#                     type = str, 
#                     help = 'Timestamp (UTC) del fin de la simulación. Formato: yyyy-mm-dd hh:mm'
#                     )

# parser.add_argument('dt_min', 
#                     type = int, 
#                     help = 'Paso temporal deseado en minutos.'
#                     )

# parser.add_argument('--cell_coords', 
#                     type = str, 
#                     help = 'Ruta al .csv con las coordenadas de la grilla.',
#                     default = 'Carpeta_base_SWMM/coordenadas_celdas.csv'
#                     )

# # Parsear los argumentos
# args = parser.parse_args()

# inicio_sim = pd.to_datetime(args.inicio_sim, utc=True)
# fin_sim = pd.to_datetime(args.fin_sim, utc=True)
# dt_min = args.dt_min
# path_cell_cords = args.cell_coords

inicio_sim = pd.to_datetime('2024-10-01 00:00', utc=True)
fin_sim = pd.to_datetime('2024-10-01 01:00', utc=True)
dt_min = 5
path_cell_cords = 'Carpeta_base_SWMM/coordenadas_celdas.csv'



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

dfs = []

for id_serie in ids_serie:
    print(id_serie)
    response = requests.get(
    f"https://alerta.ina.gob.ar/a6/obs/puntual/series/{id_serie}/observaciones", 
    headers={'Authorization': f'Bearer {token_base_INA}'}, 
    # 'timestart' y 'timeend' en hora BA (+03)
    params={'timestart': f'{inicio_sim.tz_convert(tz="America/Argentina/Buenos_Aires"):%Y-%m-%d %H:%M}', 
            'timeend': f'{fin_sim.tz_convert(tz="America/Argentina/Buenos_Aires"):%Y-%m-%d %H:%M}'}
    )
    df = pd.DataFrame(response.json())
    if not df.empty:
        df = df.rename(columns={'valor': id_serie})
        df = df[['timestart', 'timeend', id_serie]]
        df.timestart = pd.to_datetime(df.timestart)
        df.timeend = pd.to_datetime(df.timeend)
        dfs.append(df)
        j = response.json()
        print(df.timestart - df.timeend)


# 4. PREPROCESAMIENTO DATOS EMAs
series = []
for df in dfs:
    # a. Identificar datos faltantes y completar con NaN
    dt = (df.timestart - df.timestart.shift(1)).value_counts().idxmax() # time delta
    df = df.set_index('timestart')
    serie = df[df.columns[-1]]
    serie = serie.resample(dt).asfreq()

    # b. Llevar a intensidad (en lugar de volumen)
    serie = serie*pd.Timedelta(hours=1)/dt

    # c. Llevar a intervalos de un minuto
    serie = serie.resample('60s').bfill()
    series.append(serie)

# d. Llevar a paso temporal deseado
df = pd.concat(series, axis=1)
df = df.resample(f'{dt_deseado}min', origin='end').mean()
    


# 5. INTERPOLACIÓN ESPACIAL (THIESSEN O IDW). DE EMAs A CELDAS.
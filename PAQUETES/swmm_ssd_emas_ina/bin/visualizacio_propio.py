import os
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd


#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)


# Ruta base donde buscar los archivos
base_path = "data/HIST/POST"
experimento = 'swmm_ssd_emas_ina'

# Obtener el tiempo actual y el límite de 24 horas atrás
now = datetime.utcnow()

files = []
for lag in range(24):
    date = now - pd.Timedelta(hours=lag)
    file_path = f'{base_path}/{date:%Y/%m/%d/%H0000}/{experimento}/series.json'
    if os.path.isfile(file_path):
        files.append(file_path)

if files:
    print('ok')
    dfs = []
    for file in files:
        series = []
        with open(file, 'r') as f:
            data = json.load(f)
            sensores = data.get("sensores", {})
            for sensor, sensor_data in sensores.items():
                observaciones = sensor_data.get("observaciones", {}).get("Flow_depth", {})
                series.append(pd.Series(data = observaciones, name=sensor))
        dfs.append(pd.DataFrame(series).transpose())

    df = pd.concat(dfs)
    fig, ax = plt.subplots()
    df.plot(ax=ax)
    plt.ylim(0, max(df.max().max(), 3))
    plt.grid()
    plt.tight_layout()
    plt.xticks(rotation=90)
    plt.ylabel('Nivel hidrométrico [m]')
else:
    print('No se encontraron archivos en las últimas 24 hs.')

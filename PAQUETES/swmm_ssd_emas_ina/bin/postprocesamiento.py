from swmmtoolbox import swmmtoolbox as stb
import pandas as pd
import json
import datetime

experimento = 'swmm_ssd_emas_ina'

#  0. DEFINIR LA FECHA

parser = argparse.ArgumentParser(description="Script de preprocesamiento")
parser.add_argument("--inicio_sim", required=True, help="Timestamp en formato YYYY-MM-DDTHH:MM:SSZ")
args = parser.parse_args()
inicio_sim = args.inicio_sim
inicio_sim = pd.to_datetime(inicio_sim)
print(f"Inicio simulación: {inicio_sim}")

# inicio_sim = pd.to_datetime('2024-03-19 23:30', utc=True)

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

# 2. EXTRAER SERIES

resultados = {"simulacion":{'inicio_sim': inicio_sim.strftime("%Y-%m-%d %H:%M:%S%z"),
                            'modelo_base': params["inp_base"]},
              "sensores": {}}
if "points_of_interest" in params:
    pois = params['points_of_interest']
    for poi in pois:
        link = pois[poi]['link_swmm']
        serie_link = stb.extract(f'data/HIST/ASIM/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/model.out',
                                 f'link,{link},Flow_depth')
        serie_link = serie_link.tz_localize('utc')
        serie_link = serie_link.round(2)
        serie_link.index = serie_link.index.strftime("%Y-%m-%d %H:%M:%S%z")
        resultados["sensores"][poi] = {"nombre_completo": pois[poi]['nombre_completo'],
                                       "link_swmm": pois[poi]['link_swmm'],
                                       "observaciones": {"Flow_depth": serie_link.squeeze().to_dict()}
                                       }

    json_dirpath = f'data/HIST/POST/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'
    if not os.path.exists(json_dirpath): 
        os.makedirs(json_dirpath)


    with open(f'{json_dirpath}/series.json', "w") as outfile: 
        json.dump(resultados, outfile)
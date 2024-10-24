import os

#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)

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


# inp_file = 'Carpeta_base_SWMM/model_base.inp'
# nc_file = glob('Carpeta_base_SWMM/*.nc')[0]
# inp_file_modificado = 'modelo_prueba.inp'
# epsg_SWMM = 5347
# epsg_precipitacion = 4326
# path_cell_cords = 'Carpeta_base_SWMM/coordenadas_celdas.csv'
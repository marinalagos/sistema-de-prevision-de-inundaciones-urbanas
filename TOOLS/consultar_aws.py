import s3fs
import pandas as pd

import s3fs
import pandas as pd

# Parámetros del pronóstico
DURACION_HH = 10  # Duración del pronóstico hidrológico-hidráulico en horas
DURACION_WRF = 72  # Duración del pronóstico de WRF en horas

#------------------------------------------------------------#
# 1. BUSCAR ÚLTIMA INICIALIZACIÓN DE NWP DISPONIBLE
#------------------------------------------------------------#

# Configuración de S3
fs = s3fs.S3FileSystem(anon=True)  # Cambiar a False si se requiere autenticación
BASE_PATH = 'smn-ar-wrf/DATA/WRF/DET/'

# Tiempos de referencia
now = pd.Timestamp.now(tz='utc')
fecha_limite = now - pd.Timedelta(hours=DURACION_WRF)
start_date_wrf = pd.Timestamp(year=now.year, month=now.month, day=now.day, hour=now.hour, tz='utc')

# Variable para almacenar la última carpeta válida
ultima_carpeta_valida = None

while start_date_wrf > fecha_limite:
    # Construir la ruta del día actual
    day_path = f"{BASE_PATH}{start_date_wrf:%Y/%m/%d}/"

    # Verificar si el día tiene datos
    if fs.exists(day_path):
        horas_disponibles = sorted(fs.ls(day_path))  # Obtener las horas disponibles

        while horas_disponibles:
            latest_folder = horas_disponibles.pop()  # Tomar la última hora disponible
            y, m, d, h = latest_folder.split('/')[-4:]

            # Calcular el plazo del pronóstico
            dt_inicializacion = pd.Timestamp(year=int(y), month=int(m), day=int(d), hour=int(h), tz='utc')
            plazo_inicio = int((start_date_wrf - dt_inicializacion).total_seconds() // 3600)
            plazos_necesarios = range(plazo_inicio, plazo_inicio + DURACION_HH)

            # Generar los nombres esperados de archivos
            archivos_esperados = {
                f"{latest_folder}/WRFDETAR_10M_{dt_inicializacion:%Y%m%d_%H}_{p:03d}.nc" for p in plazos_necesarios
            }

            # Obtener archivos existentes
            archivos_reales = set(fs.ls(latest_folder))

            # Verificar si están todos los archivos requeridos
            if archivos_esperados.issubset(archivos_reales):
                ultima_carpeta_valida = latest_folder
                break  # Salimos del `while horas_disponibles`

        if ultima_carpeta_valida:
            break  # Salimos del `while start_date_wrf > fecha_limite`

    # Retroceder un día
    start_date_wrf -= pd.Timedelta(days=1)

# Resultado final
if ultima_carpeta_valida:
    print(f"Última carpeta válida: {ultima_carpeta_valida}")
else:
    print("No se encontraron datos completos en las últimas 72 horas.")

#------------------------------------------------------------#
# 2. DESCARGAR ARCHIVOS NECESARIOS
#------------------------------------------------------------#

# Aclaración (https://odp-aws-smn.github.io/documentation_wrf_det/Estructura_de_datos/): 
# /DATA/WRF/DET/2022/03/14/00/WRFDETAR_10M_20220314_00_012.nc corresponde a los pronósticos 
# inicializados el 14 de marzo de 2022 a las 00 UTC para el plazo 12 horas de las variables 
# con una frecuencia de 10 minutos. Este archivo contiene 6 tiempos cuya validez va desde 
# 12:00UTC hasta 12:50UTC.

# ds_list = []


# files = fs.glob(f'{latest_folder}/WRFDETAR_10M_{START_DATE:%Y%m%d_%H}_*.nc')
# for s3_file in files:
#     print(s3_file)
#     f = fs.open(s3_file)
#     ds_tmp = xr.open_dataset(f, decode_coords = 'all', engine = 'h5netcdf')
#     ds_list.append(ds_tmp)
# if len(ds_list) == 0:
#     time.sleep(600)

#     files = fs.ls(latest_folder)
#     print(f'Archivos en {latest_folder}: {files}')
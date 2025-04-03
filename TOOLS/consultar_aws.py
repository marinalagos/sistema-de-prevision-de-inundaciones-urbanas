import s3fs
import pandas as pd

hs_HH = 10 # duración de pronóstico hidrológico-hidráulico

# 1. BUSCAR ÚLTIMA INICIALIZACIÓN DE NWP DISPONIBLE
hs_WRF = 72 # duración de pronóstico de WRF

now = pd.Timestamp.now(tz='utc')
fecha_limite_hacia_atras = now - pd.Timedelta(hours=hs_WRF)

START_DATE = pd.Timestamp(year=now.year, month=now.month, day=now.day, hour=now.hour, tz='utc')
START_DATE_WRF = START_DATE

fs = s3fs.S3FileSystem(anon=True)
base_path = 'smn-ar-wrf/DATA/WRF/DET/'

while START_DATE_WRF > fecha_limite_hacia_atras:
    year, month, day = START_DATE_WRF.strftime("%Y"), START_DATE_WRF.strftime("%m"), START_DATE_WRF.strftime("%d")
    day_path = f"{base_path}{year}/{month}/{day}/"

    if fs.exists(day_path):  # Si el día existe, buscar la última hora disponible
        hours = fs.ls(day_path)
        while hours:
            latest_folder = sorted(hours)[-1]  # Tomar la última hora disponible
            y,m,d,h = latest_folder.split('/')[-4:]
            dt_plazo_000 = pd.Timestamp(year=int(y), month=int(m), day=int(d), hour=int(h), tz='utc')
            plazo_START_DATE = int((START_DATE - dt_plazo_000).seconds/3600)
            plazos_necesarios = range(plazo_START_DATE, plazo_START_DATE + hs_HH)
            if 'estan los archivos que necesito':
                break
            latest_folder.pop()

    START_DATE_WRF = START_DATE_WRF - pd.Timedelta(days=1)

if latest_folder:
    print(f'Última inicialización de NWP disponible: {latest_folder}')
else:
    print('No hay datos disponibles en las últimas 72 horas.')
    break

# 2. DESCARGAR ARCHIVOS NECESARIOS

# Aclaración (https://odp-aws-smn.github.io/documentation_wrf_det/Estructura_de_datos/): 
# /DATA/WRF/DET/2022/03/14/00/WRFDETAR_10M_20220314_00_012.nc corresponde a los pronósticos 
# inicializados el 14 de marzo de 2022 a las 00 UTC para el plazo 12 horas de las variables 
# con una frecuencia de 10 minutos. Este archivo contiene 6 tiempos cuya validez va desde 
# 12:00UTC hasta 12:50UTC.

ds_list = []
y,m,d,h = latest_folder.split('/')[-4:]
dt_plazo_000 = pd.Timestamp(year=int(y), month=int(m), day=int(d), hour=int(h), tz='utc')
plazo_START_DATE = int((START_DATE - dt_plazo_000).seconds/3600)
plazos_necesarios = range(plazo_START_DATE, plazo_START_DATE + hs_HH)






files = fs.glob(f'{latest_folder}/WRFDETAR_10M_{START_DATE:%Y%m%d_%H}_*.nc')
for s3_file in files:
    print(s3_file)
    f = fs.open(s3_file)
    ds_tmp = xr.open_dataset(f, decode_coords = 'all', engine = 'h5netcdf')
    ds_list.append(ds_tmp)
if len(ds_list) == 0:
    time.sleep(600)

    files = fs.ls(latest_folder)
    print(f'Archivos en {latest_folder}: {files}')
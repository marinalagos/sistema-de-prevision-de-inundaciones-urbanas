import pandas as pd
import requests
import json
import os
import argparse
import geopandas as gpd
from shapely import wkt
import UTILS.spatial_interpolation as spint

def consultar_emas_base_ina(
    inicio_sim, # Timestamp (UTC) del inicio de la simulación. Formato: yyyy-mm-dd hh:mm'
    fin_sim, # Timestamp (UTC) del fin de la simulación. Formato: yyyy-mm-dd hh:mm
    token_base_INA, # Token para tener acceso a la base INA
    params, # diccionario de config.json
    path_raw_data = False
    ):

    """
    Realiza la consulta de precipitación a la base INA, indicando inicio, fin e ids
    de las estaciones. El dataframe resultado está expresado en mm/h.
    1) Realizar la consulta
    2) Preprocesamiento de los datos: identificar faltantes, convertir a intensidad
    y resamplear a intervalo deseado.
    3) Llevar los datos puntuales a una grilla (polígonos de Thiessen o IDW)
    """

    # 1. CONSULTA A LA BASE DEL INA

    dfs = []
    jsons = []

    inicio_sim = pd.to_datetime(inicio_sim, utc=True)
    fin_sim = pd.to_datetime(fin_sim, utc=True)

    ids_EMAs = params['ids_EMAs_consultadas']

    for id_serie in ids_EMAs:
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
            jsons += response.json()
            df = df.rename(columns={'valor': id_serie})
            df = df[['timestart', 'timeend', id_serie]]
            df.timestart = pd.to_datetime(df.timestart)
            df.timeend = pd.to_datetime(df.timeend)
            dfs.append(df)
            # j = response.json()
            # print(df.timestart - df.timeend)

    if path_raw_data != False:
        dir_path = os.path.dirname(path_raw_data)
        if not os.path.exists(dir_path): 
            os.makedirs(dir_path) 

        with open(path_raw_data, "w") as file:
            json.dump(jsons, file, indent=4, ensure_ascii=False)


    # 2. PREPROCESAMIENTO DATOS EMAs
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
    df = df.resample(f"{params['dt_precipitacion_minutos']}min", origin='end').mean()
    
    # e. Correr un delta t para cumplir con el formato de SWMM

    # SWMM’s rainfall Time Series and user-prepared Rainfall files treat the data as “start-of-interval”
    # values, meaning that each rainfall intensity or depth is assumed to occur at the start of its associated
    # date/time value and last for a period of time equal to the gage’s recording interval. Most rainfall
    # recording devices report their readings as “end-of-interval” values, meaning that the time stamp
    # associated with a rainfall value is for the end of the recording interval. If such data are being used
    # to populate a SWMM rainfall time series or user-prepared rainfall file then their date/time values
    # should be shifted back one recording interval to make them represent “start-of-interval” values
    # (e.g., for hourly rainfall, a reading with a time stamp of 10:00 am should be entered into the time
    # series or file as a 9:00 am value).

    df.index = df.index.shift(-1)

    # 3. INTERPOLACIÓN ESPACIAL (THIESSEN O IDW). DE EMAs A CELDAS.
    # a. Obtener coordenadas de cada una de las series con datos
    ids = []
    lats = []
    lons = []
    for id_serie in df.columns:
        response = requests.get(
            f"https://alerta.ina.gob.ar/a6/obs/puntual/series/{id_serie}", 
            headers={'Authorization': f'Bearer {token_base_INA}'}
        )
        lon, lat = response.json()['estacion']['geom']['coordinates']
        lats.append(lat)
        lons.append(lon)
        ids.append(id_serie)

    gdf_data = gpd.GeoDataFrame(index=ids, geometry=gpd.points_from_xy(lons, lats), crs='EPSG:4326')

    # b. Obtener la grilla donde interpolar valores
    gdf_grid = pd.read_csv(params['path_cell_coords'], index_col=0)
    gdf_grid['geometry'] = gdf_grid['Coordinates'].apply(wkt.loads)
    gdf_grid = gpd.GeoDataFrame(gdf_grid, geometry='geometry')
    gdf_grid.set_crs(epsg=params['epsg_precipitacion'], inplace=True)
    gdf_grid = gdf_grid['geometry']

    spatial_interpolation = params['interpolacion_espacial']
    if spatial_interpolation == 'idw':
        if 'idw_power' in params:
            df_grid = spint.idw(df, geoseries_data=gdf_data, geoseries_grid=gdf_grid, 
                                epsg = params['epsg_SWMM'], p = params['potencia_idw'])
        else:
            df_grid = spint.idw(df, geoseries_data=gdf_data, geoseries_grid=gdf_grid, 
                                epsg = params['epsg_SWMM'], p = 2)   
    
    elif spatial_interpolation == 'thiessen':
        df_grid = spint.thiessen(df, geoseries_data=gdf_data, geoseries_grid=gdf_grid,
                                 epsg = params['epsg_SWMM'])

    return df_grid
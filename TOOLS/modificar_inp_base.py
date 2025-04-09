import pandas as pd
import xarray as xr
from shapely.geometry import Polygon, MultiPoint, Point
import pyproj
from scipy.spatial import KDTree
from glob import glob
import geopandas as gpd
import argparse
import os

def modificar_inp_base(
    inp_file, # Ruta al archivo .inp a modificar
    df_coords, # DataFrame con las coordenadas de las celdas de precipitación
    epsg_SWMM, # Código EPSG del crs del modelo SWMM
    epsg_precipitacion, # Código EPSG del crs del DataFrame de precipitación
    inp_file_modificado = False, # Ruta al archivo .inp a modificar. Si no se define, se sobrescribe el .inp original
    ):
    """
    Modifica la tabla de subcuencas y de pluviómetros en el .inp base
    df_coords: DataFrame con las coordenadas de las celdas de precipitación
    """

    # 1. DEFINIR SISTEMAS DE COORDENADAS
    crs_SWMM = pyproj.CRS.from_epsg(epsg_SWMM) # CRS Posgar 2007 Faja 5 (código EPSG: 5347)
    crs_precipitacion = pyproj.CRS.from_epsg(epsg_precipitacion) # WGS84 (código EPSG: 4326)
    # posgar2geo = pyproj.Transformer.from_crs(crs_SWMM, crs_precipitacion, always_xy=True) # Conversor de coordenadas
    # geo2posgar = pyproj.Transformer.from_crs(crs_precipitacion, crs_SWMM, always_xy=True) # Conversor de coordenadas



    # 2. EXTRACCIÓN DE CENTROIDES DE LOS POLÍGONOS DE SUBCUENCAS A PARTIR DEL .inp
    # Abre el archivo de entrada y lee todas las líneas
    with open(inp_file) as f:
        lines = f.readlines()

    # Extracción de la tabla de polígonos del archivo .inp
    ini = lines.index('[Polygons]\n') + 3
    fin = lines.index('[SYMBOLS]\n') - 1 # MEJORAR ESTO, PUEDE QUE [SYMBOLS] NO EXISTA
    lines_polygons = lines[ini:fin]
    df_polygons = pd.DataFrame([i.split() for i in lines_polygons], columns=['subcatchment', 'xcoord', 'ycoord'])
    df_polygons = df_polygons.set_index('subcatchment')

    # Inicializa la primera subcuenca y las listas para las coordenadas y centroides
    subc = df_polygons.index[0]
    coords = []
    subc_centroid = {}

    # Itera sobre cada fila del DataFrame de polígonos
    for index, row in df_polygons.iterrows():
        # Si el índice es igual al subcuenca actual, va guardando las coordenadas
        if index == subc:
            xcoord, ycoord = float(row.xcoord), float(row.ycoord)
            coords.append((xcoord, ycoord))
        # Si no, cierra el polígono, calcula el centroide, y pasa a la siguiente subcuenca
        else:
            polygon = Polygon(coords)
            centroid = polygon.centroid
            subc_centroid[subc] = centroid

            subc = index
            xcoord, ycoord = float(row.xcoord), float(row.ycoord)
            coords = [(xcoord, ycoord)]



    # 3. GENERAR LOS DOS DATAFRAMES DE COORDENADAS (PLUVIÓMETROS Y SUBCUENCAS)
    # 3.a. PLUVIÓMETROS
    gdf_pluviometros = gpd.GeoDataFrame(df_coords,
                                        geometry = gpd.points_from_xy(df_coords.lon, df_coords.lat),
                                        crs = crs_precipitacion).drop(columns=['lon', 'lat'])
    gdf_pluviometros = gdf_pluviometros.to_crs(crs_SWMM)

    # 3.b. SUBCUENCAS
    gdf_subcuencas = gpd.GeoDataFrame(index = list(subc_centroid.keys()),
                                      geometry = list(subc_centroid.values()),
                                      crs = crs_SWMM)
    


    # 4. ENCONTRAR PARA CADA SUBCUENCA EL PLUVIÓMETRO MÁS CERCANO   
    resultados = []
    # Iterar sobre cada subcuenca
    for idx_sub, sub_geom in gdf_subcuencas.geometry.items():
        # Calcular la distancia a todos los pluviómetros
        distancias = gdf_pluviometros.distance(sub_geom)
        
        # Obtener el índice del pluviómetro más cercano
        idx_pluvio_min = distancias.idxmin()
        
        # Guardar el resultado
        resultados.append({
            'subcuenca': idx_sub,
            'pluviometro': idx_pluvio_min,
        })

    # Convertir los resultados en un DataFrame
    df_asignacion = pd.DataFrame(resultados).set_index('subcuenca')



    # 5. MODIFICACIÓN DE TABLA DE PLUVIOMETROS EN EL ARCHIVO .inp
    # Extracción de la tabla de pluviometros del archivo .inp
    inicio = lines.index('[RAINGAGES]\n') + 3
    fin = lines.index('[SUBCATCHMENTS]\n') -1

    # Armar tabla nueva
    pluvio_names = df_asignacion.pluviometro.unique()
    df_rainfall = pd.DataFrame()
    df_rainfall['Name'] = pluvio_names
    df_rainfall['Format'] = 'PFORMAT'
    df_rainfall['Interval'] = 'INTERVAL_MINUTES'
    df_rainfall['SCF'] = '1.0'
    df_rainfall['Source'] = 'FILE'
    df_rainfall['filename'] = f'"RAINFALLFILEPATH"'
    df_rainfall['raingage'] = pluvio_names
    df_rainfall['unit'] = 'MM'

    # Generar nuevo string
    str_raingages = df_rainfall.to_string(index=False, header=False, justify='left')

    # Incorporar líneas nuevas
    lines = lines[:inicio] + [str_raingages] + ['\n'] + lines[fin:]



    # 6. MODIFICACIÓN DE TABLA DE SUBCUENCAS EN EL ARCHIVO .inp
    # Extracción de la tabla de subcuencas del archivo .inp
    inicio = lines.index('[SUBCATCHMENTS]\n') + 3
    fin = lines.index('[SUBAREAS]\n') - 1

    lines_subcuencas = lines[inicio:fin]
    df_subcuencas = pd.DataFrame([i.split() for i in lines_subcuencas], columns=['Name', 'RainGage', 'Outlet', 'Area', 'Imperv', 'Width', 'Slope', 'CurbLen'])
    df_subcuencas = df_subcuencas.set_index('Name')

    # Cruzar con el dataframe de asignación subcuenca-pluviometro
    df_subcuencas = pd.merge(df_subcuencas, df_asignacion,
                             right_index = True, left_index = True,
                             how = 'left', sort = False)

    df_subcuencas['pluviometro'] = df_subcuencas['pluviometro'].fillna(df_asignacion.values[0][0]) # Para las celdas sin área, no hay celda asociada. En esos casos, se asigna una celda arbitraria (la primera de la lista)
    df_subcuencas['RainGage'] = df_subcuencas['pluviometro']
    df_subcuencas = df_subcuencas.drop(columns=['pluviometro'])

    # Generar nuevo string
    str_subcatchments = df_subcuencas.to_string(index=True, header=False, index_names=False, justify='left')

    # Incorporar líneas nuevas
    lines = lines[:inicio] + [str_subcatchments] + ['\n'] + lines[fin:]



    # 7. ACTUALIZACIÓN DEL ARCHIVO .inp
    f = open (inp_file_modificado,'w')
    f.write(''.join(lines))
    f.close()
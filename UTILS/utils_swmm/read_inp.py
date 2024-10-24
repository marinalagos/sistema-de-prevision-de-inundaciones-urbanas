import time
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon #!pip install -U shapely

ruta='pruebas_borrar'
Nombre_Modelo='modelo_conupy_fmt'
name_swmm='modelo_conupy_fmt'
# Nombre_Modelo='modelo_swmm_fmt'
# name_swmm='modelo_swmm_fmt'
crs_proy='EPSG: 22176'
SubCuencas = True
Nodos = True
Links = True

archivo_inp = ruta+'/Modelos/'+Nombre_Modelo+'/'+name_swmm+'.inp'
a_inp = open(archivo_inp, 'r', encoding='latin-1')

objects = ['subcatchments', 'conduits']
subcatchments = True
junctions = True
storage = True
conduits = True
xsections = True
coordinates = True
polygons = True

general_dict = {
    'subcatchments': {'attributes': ['Name', 'Rgage', 'OutID', 'Area', '%Imperv', 'Width', 'Slope', 'Clength'],
                      'flag': False,
                      'request': subcatchments},
    'junctions': {'attributes': ['Name', 'Elev', 'Ymax', 'Y0', 'Ysur', 'Apond'],
                  'flag': False,
                  'request': junctions},
    'storage': {'attributes': ['Name', 'Elev.', 'MaxDepth', 'InitDepth', 'Shape', 'Curve', 'Type/Params', 'SurDepth', 'Fevap', 'Psi', 'Ksat', 'IMD'],
                'flag': False,
                'request': storage},
    'conduits': {'attributes': ['Name', 'From Node', 'To Node', 'Length', 'Roughness', 'InOffset', 'OutOffse', 'InitFlow', 'MaxFlow'],
                 'flag': False,
                 'request': conduits},
    'xsections': {'attributes': ['Link', 'Shape', 'Geom1','Geom2', 'Geom3', 'Geom4', 'Barrels', 'Culvert'],
                  'flag': False,
                  'request': xsections},
    'coordinates': {'attributes': ['Node', 'X-Coord', 'Y-Coord'],
                    'flag': False,
                    'request': coordinates},
    'polygons': {'attributes': ['Subcatchment', 'X-Coord', 'Y-Coord'],
                 'flag': False,
                 'request': polygons},
}

def get_ini_fin(object, linea, line, contador):
    if linea.upper().find('[' + object.upper() + ']') != -1:
        general_dict[object]['ini'] = contador
        general_dict[object]['flag'] = True
    if (len(line) == 1 or line.startswith('\t')) and general_dict[object]['flag']:
        general_dict[object]['fin'] = contador
        general_dict[object]['flag'] = False
        
if True:
# def inp2df(ruta, Nombre_Modelo, name_swmm,crs_proy,SubCuencas=True,Nodos=True,Links=True):
    #Nombre archivos
    inicio = time.time()
    archivo_inp = ruta+'/Modelos/'+Nombre_Modelo+'/'+name_swmm+'.inp'
    
    os.makedirs(ruta+'/Salidas/' + Nombre_Modelo+'/shps', exist_ok=True)
    os.makedirs(ruta+'/Salidas/' + Nombre_Modelo+'/csv', exist_ok=True)

    shp_nodos = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Nodos_'+Nombre_Modelo+'.shp'
    shp_nodos_storage = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Nodos_'+Nombre_Modelo+'_storage.shp'
    shp_links = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Links_'+Nombre_Modelo+'.shp'
    shp_cuencas = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Cuencas_'+Nombre_Modelo+'.shp'

    csv_nodos = ruta+'/Salidas/' + Nombre_Modelo+'/csv/Nodos_'+Nombre_Modelo+'.csv'
    csv_links = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Links_'+Nombre_Modelo+'.csv'
    csv_cuencas = ruta+'/Salidas/' + Nombre_Modelo+'/shps/Cuencas_'+Nombre_Modelo+'.csv'

    contador = 0

    for line in a_inp:
        linea = line.rstrip()
        contador+=1

        for object in general_dict:
            get_ini_fin(object=object, line=line, linea=linea, contador=contador)

    contador+=1
    last_line = contador
    a_inp.close()

    for object in general_dict:
        if general_dict[object]['request']:
            print(object.upper() + '\n')
            skip1 = general_dict[object]['ini'] + 2
            skip2 = last_line - general_dict[object]['fin']
            df_object = pd.read_csv(archivo_inp,
                                    sep='\s+',
                                    skiprows=skip1, 
                                    skipfooter=skip2,
                                    header=None,
                                    names=general_dict[object]['attributes'],
                                    engine='python',
                                    encoding='ISO-8859-1')
            df_object[df_object.columns[0]] = df_object[df_object.columns[0]].astype('str')
            df_object.set_index(df_object[df_object.columns[0]], inplace=True)
            del df_object[df_object.columns[0]]
            print(df_object)
            print('\n')



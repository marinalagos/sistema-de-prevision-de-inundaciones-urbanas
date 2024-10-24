import pandas as pd

def inp2df(inpfile, subcatchments=False, junctions=False, storage=False, conduits=False, xsections=False, coordinates=False, polygons=False):
    
    a_inp = open(inpfile, 'r', encoding='latin-1')
    dict_results = {}

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
            df_object = pd.read_csv(inpfile,
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
            dict_results[object] = df_object
            print(df_object)
            print('\n')
    
    return dict_results

# ver = inp2df('/home/phc/Git/sistema-de-prevision-de-inundaciones-urbanas/Carpeta_base_SWMM/model_base.inp', subcatchments=True, junctions=True)
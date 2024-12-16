# INPUT:
# - dataframe con datetimeindex donde cada columna está asociada a los datos de un raingage
# - path del archivo de lluvia a generar
# OUTPUT:
# - Rainfall file con formato SWMM (STA01 2004 06 12 00 00 0.12). Es un único archivo con la info de todos los raingages.

import os

def create_rainfall_file(data, file_path):
    lines = []

    columns = data.columns

    data['formatted_date'] = data.index.strftime("%Y\t%m\t%d\t%H\t%M")

    for P in columns:
        print(data[P])
        data['str'] = P + '\t' + data['formatted_date'] + '\t' + data[P].round(2).astype(str)
        lines = lines + list(data['str'])

    texto = '\n'.join(lines)

    if not os.path.exists(file_path): 
        os.makedirs(file_path) 

    f = open(file_path + '/p.txt','w')
    f.write(texto)
    f.close()
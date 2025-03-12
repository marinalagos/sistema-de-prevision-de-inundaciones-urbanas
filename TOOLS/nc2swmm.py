import xarray as xr
import pandas as pd

def nc2swmm(nc_filepath, swmm_base_filepath, swmm_mod_filepath, conn_subc_cell = False):
    """
    Parameters:
    - nc_filepath: precipitation netcdf filepath
    - swmm_base_filepath: swmm inp filepath
    - swmm_mod_filepath: modified swmm inp filepath
    - conn_subc_cell: path to the csv file of connections between subcatchments and precipitation cells
    
    Outputs:
    - 
    - Rainfall file - SWMM format (STA01 2004 06 12 00 00 0.12). It contains data from all rain gauges.
    """
    dir_run_unix = dir_run.replace('\\', '/')
    
    ds = xr.open_dataset(nc_filepath, decode_coords = 'all', engine = 'h5netcdf')
    init_utc = pd.to_datetime(ds.XTIME.values[0])
    end_utc  = pd.to_datetime(ds.XTIME.values[-1])


    # Asignacion subcuenca-celda
    #-----------------------------------------------------------------------------------------#
    if desde_cero:
        from subc_cell import sub_cell
        df_subc_cell = sub_cell(nc_file  = nc_filepath,
                                inp_file = swmm_base_filepath)
    else:    
        df_subc_cell = pd.read_csv('subc_cell.csv', names=[0], index_col=0)


    # Extraer las series de tiempo del .nc para generar los Px.txt
    #-----------------------------------------------------------------------------------------#
    lines = []
    cell_names = df_subc_cell[0].unique()
    for p in cell_names:
        lat, lon = p[1:].split('_')
        lat, lon = -float(lat)/1000, -float(lon)/1000
        tseries = ds.sel({'XLONG': lon, 'XLAT': lat}).PP.to_dataframe()['PP']
        tseries.index = pd.to_datetime(tseries.index).round('S')

        for index, value in tseries.items():
            lines.append(f'{p}\t{index:%Y}\t{index:%m}\t{index:%d}\t{index:%H}\t{index:%M}\t{value:.2f}')

    texto = '\n'.join(lines)
    f = open (f'{dir_run}//pp.txt','w')
    f.write(texto)
    f.close()


    # Modificar .inp
    #-----------------------------------------------------------------------------------------#
    with open(swmm_base_filepath) as f:
        lines = f.readlines()

    ### FECHAS ###
    i = 0
    line_date = -1
    while line_date == -1:
        if 'START_DATE' in lines[i]:
            line_date = i
        i += 1

    lines[line_date]     = f'START_DATE           {init_utc:%m/%d/%Y}\n'
    lines[line_date + 1] = f'START_TIME           {init_utc:%H:%M:%S}\n'
    lines[line_date + 2] = f'REPORT_START_DATE    {init_utc:%m/%d/%Y}\n'
    lines[line_date + 3] = f'REPORT_START_TIME    {init_utc:%H:%M:%S}\n'
    lines[line_date + 4] = f'END_DATE             {end_utc :%m/%d/%Y}\n'
    lines[line_date + 5] = f'END_TIME             {end_utc :%H:%M:%S}\n'

    ### HOTSTART ###
    line_hs = lines.index('SAVE HOTSTART "hotstart.hsf"\n')
    lines[line_hs] = f'SAVE HOTSTART "{dir_run_unix}/hotstart.hsf"\n'
    ### TABLA PLUVIOS ###
    inicio = lines.index('[RAINGAGES]\n') + 3
    fin = lines.index('[SUBCATCHMENTS]\n') -1

    df_rainfall = pd.DataFrame()
    df_rainfall['Name'] = cell_names
    df_rainfall['Format'] = 'VOLUME'
    df_rainfall['Interval'] = '0:10'
    df_rainfall['SCF'] = '1.0'
    df_rainfall['Source'] = 'FILE'
    df_rainfall['filename'] = f'{dir_run_unix}/pp.txt'
    df_rainfall['raingage'] = cell_names
    df_rainfall['unit'] = 'MM'

    str_raingages = df_rainfall.to_string(index=False, header=False, justify='left')

    lines2 = lines[:inicio] + [str_raingages] + ['\n'] + lines[fin:]

    ### SUBCUENCAS ###
    inicio = lines.index('[SUBCATCHMENTS]\n') + 3
    fin = lines.index('[SUBAREAS]\n') -1
    lines_subcuencas = lines[inicio:fin]
    [i.split() for i in lines_subcuencas]
    df_subcuencas = pd.DataFrame([i.split() for i in lines_subcuencas], columns=['Name', 'RainGage', 'Outlet', 'Area', 'Imperv', 'Width', 'Slope', 'CurbLen'])
    df_subcuencas = df_subcuencas.set_index('Name')
    df_subcuencas = pd.merge(df_subcuencas, df_subc_cell,
                            right_index = True,
                            left_index = True,
                            how = 'left',
                            sort = False)

    df_subcuencas[0] = df_subcuencas[0].fillna(cell_names[0])
    df_subcuencas['RainGage'] = df_subcuencas[0]
    df_subcuencas = df_subcuencas.drop(columns=[0])

    str_subcatchments = df_subcuencas.to_string(index=True, header=False, index_names=False, justify='left')
    inicio = lines2.index('[SUBCATCHMENTS]\n') + 3
    fin = lines2.index('[SUBAREAS]\n') -1
    lines3 = lines2[:inicio] + [str_subcatchments] + ['\n'] + lines2[fin:]

    ### ESCRIBIR ARCHIVO ###
    f = open (f'{dir_run}//model.inp','w')
    f.write(''.join(lines3))
    f.close()
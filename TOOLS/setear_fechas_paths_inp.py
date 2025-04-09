from UTILS.modify_textfile import modify_textfile
import pandas as pd
import os

def setear_fechas_paths_inp(inicio_sim, 
                            fin_sim, 
                            inp_base_modificado, 
                            filepath_HSin, 
                            filepath_HSout,
                            filepath_rainfall,                            
                            dt_precipitacion_minutos,
                            pformat,
                            filepath_new_inp):
    # inicio_sim = pd.to_datetime('2024-07-09 01:00', utc=True)
    # fin_sim = pd.to_datetime('2024-10-13 00:00', utc=True)
    # experimento = 'swmm_ssd_emas_ina'
    # inp_base = 'Carpeta_base_SWMM/model_base_prueba.inp'

    dt = pd.Timedelta(minutes = dt_precipitacion_minutos)
    hours = dt.components.hours
    minutes = dt.components.minutes
    interval_str = f"{hours}:{minutes:02}"

    replacements= {"STARTDATE": inicio_sim.strftime("%m/%d/%Y"),
                   "STARTTIME": inicio_sim.strftime("%H:%M:%S"),
                   "REPORTSTDATE": inicio_sim.strftime("%m/%d/%Y"),
                   "REPORTSTTIME": inicio_sim.strftime("%H:%M:%S"),
                   "ENDDATE": fin_sim.strftime("%m/%d/%Y"),
                   "ENDTIME": fin_sim.strftime("%H:%M:%S"),
                   "RAINFALLFILEPATH": filepath_rainfall,
                   "HOTSTARTIN": filepath_HSin, 
                   "HOTSTARTOUT": filepath_HSout,
                   "INTERVAL_MINUTES": interval_str,
                   "PFORMAT": pformat
                    }
                #    "HOTSTARTOUT": f'data/HIST/PREP/{fin_sim:%Y/%m/%d/%H%M%S}/{experimento}/hotstart.hsf',
                #    "RAINFALLFILEPATH": f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/p.txt',

    # path donde guardar el .inp
    # filepath_new_inp = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'

    if not os.path.exists(filepath_new_inp): 
        os.makedirs(filepath_new_inp) 

    modify_textfile(filepath = inp_base_modificado,
                    replacements = replacements,
                    output_path = filepath_new_inp,
                    stop_at_substring = "[SUBCATCHMENTS]")
from UTILS.modify_textfile import modify_textfile
import pandas as pd
import os

def crear_inp(inicio_sim, fin_sim, experimento, inp_base, pathdir_hsf, dt_precipitacion_minutos):
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
                   "RAINFALLFILEPATH": f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/p.txt',
                   "HOTSTARTIN": f'{pathdir_hsf}/hotstart.hsf', 
                   "HOTSTARTOUT": f'data/HIST/PREP/{fin_sim:%Y/%m/%d/%H%M%S}/{experimento}/hotstart.hsf',
                   "INTERVAL_MINUTES": interval_str
                    }

    # path donde guardar el .inp
    output_path = f'data/HIST/PREP/{inicio_sim:%Y/%m/%d/%H%M%S}/{experimento}/'

    if not os.path.exists(output_path): 
        os.makedirs(output_path) 

    modify_textfile(file_path = inp_base,
                    replacements = replacements,
                    output_path = output_path + '/model.inp',
                    stop_at_substring = "[SUBCATCHMENTS]")
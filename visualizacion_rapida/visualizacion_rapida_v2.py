from swmmtoolbox import swmmtoolbox as stb
import pandas as pd
import consulta_apis as api
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json

points_of_interest = {"SF_Mvideo":{"nombre_completo": "Aº San Francisco y Av. Montevideo",
                                   "link_swmm": "channel50836",
                                   "topic": "telemetria_9/nivel",
                                   "cero_api_nueva": 3.3,
                                   "id_api_anterior": '5'},
                     "LP_Libano": {"nombre_completo": "Aº Las Piedras y Rep. del Líbano",
                                   "link_swmm": "channel16633",
                                   "topic": "telemetria_12/nivel",
                                   "cero_api_nueva": 3.2,
                                   "id_api_anterior": '3'},
                     "SF_Torre":  {"nombre_completo":"Aº San Francisco y Dr. Emilio Torre",
                                   "link_swmm": "channel3626",
                                   "id_api_anterior": '8',
                                   "cero_api_anterior": 2.72},
                     "LP_Mverde": {"nombre_completo": "Aº Las Piedras y Av. Monteverde",
                                  "link_swmm": "channel16446",
                                  "id_api_anterior": '29',
                                  "cero_api_anterior": 2.78}
                     }


with open('visualizacion_rapida/series.json', 'r') as file:
    data = json.load(file)

resultados = {}

for poi in points_of_interest:
    print(poi)
    resultados[poi] = {}

    link = points_of_interest[poi]['link_swmm']
    # df_sim = stb.extract(f"{swmm_run_path}/model.out", f"link,{link},Flow_depth")
    nivel = data['sensores'][poi]['observaciones']['Flow_depth']
    df_sim = pd.Series(nivel)
    df_sim.index = pd.to_datetime(df_sim.index)
    resultados[poi]['sim'] = df_sim.rename('sim')

    fecha_inicio = df_sim.index[0]
    fecha_fin = df_sim.index[-1]
    df_obs = []

    if "topic" in points_of_interest[poi]:
        print("Disponible en la API nueva")
        topic = points_of_interest[poi]["topic"]
        df_obs = api.consultar_api_nueva(topic, fecha_inicio, fecha_fin)

        if (df_obs == []) and ('id_api_anterior' in points_of_interest[poi]):
            print("Sin datos en el periodo seleccionado en la API nueva")
            id_api = points_of_interest[poi]['id_api_anterior']
            df_obs = api.consultar_api_anterior(user = "pabloegarcia@gmail.com", 
                                                nombre = poi, 
                                                site_id = id_api,
                                                start_date = fecha_inicio.tz_convert('America/Buenos_Aires'),
                                                end_date = fecha_fin.tz_convert('America/Buenos_Aires'))
            if not df_obs.empty:
                df_obs = df_obs.set_index(pd.to_datetime(df_obs['hora']))
                if "cero_api_anterior" in points_of_interest[poi]:
                    df_obs['nivel'] = df_obs.nivel - points_of_interest[poi]["cero_api_anterior"]
                df_obs = df_obs['nivel'].rename('obs')
                df_obs = df_obs.tz_localize('America/Buenos_Aires').tz_convert('utc')
                resultados[poi]['obs'] = df_obs

        else:
            df_obs = pd.DataFrame(df_obs)
            df_obs = df_obs.set_index(pd.to_datetime(df_obs.time))
            if "cero_api_nueva" in points_of_interest[poi]:
                df_obs['Nivel'] = points_of_interest[poi]["cero_api_nueva"] - df_obs.Nivel
            df_obs = df_obs.tz_localize('utc')
            resultados[poi]['obs'] = df_obs['Nivel'].rename('obs')
    
    elif "id_api_anterior" in points_of_interest[poi]:
        print("Disponible en la API anterior")
        id_api = points_of_interest[poi]['id_api_anterior']
        df_obs = api.consultar_api_anterior(user = "pabloegarcia@gmail.com", 
                                            nombre = poi, 
                                            site_id = id_api,
                                            start_date = fecha_inicio.tz_convert('America/Buenos_Aires'),
                                            end_date = fecha_fin.tz_convert('America/Buenos_Aires'))
        df_obs = df_obs.set_index(pd.to_datetime(df_obs['hora']))
        if "cero_api_anterior" in points_of_interest[poi]:
            df_obs['nivel'] = df_obs.nivel - points_of_interest[poi]["cero_api_anterior"]
        df_obs = df_obs.tz_localize('America/Buenos_Aires').tz_convert('utc')
        df_obs = df_obs['nivel'].rename('obs')        
        resultados[poi]['obs'] = df_obs
    
    print(df_obs)

# figs_path = f'{swmm_run_path}/figs'
# if not os.path.isdir(figs_path): 
#     os.makedirs(figs_path)

for poi in points_of_interest:
    fig, ax = plt.subplots()
    ax.plot(resultados[poi]['sim'], label='simulado')
    if 'obs' in resultados[poi]:
        ax.plot(resultados[poi]['obs'], label='observado')
    ax.set_title(points_of_interest[poi]['nombre_completo'])
    ax.set_ylabel('Nivel hidrométrico [m]')
    ax.set_xlabel('Hora UTC')
    plt.legend()
    plt.grid()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))  # Formato de fecha y hora
    plt.xticks(rotation=90)  # Rotar para evitar superposición
    plt.ylim(-0.25, 3.25)
    plt.tight_layout()
    # plt.savefig(f'{figs_path}/{poi}.png')

    
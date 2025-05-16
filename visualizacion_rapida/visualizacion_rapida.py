import pandas as pd
import json
import matplotlib.pyplot as plt
from consulta_apis import consultar_api_nueva
import requests


with open('visualizacion_rapida/series.json', 'r') as file:
    data = json.load(file)


for sensor in data['sensores']:
    nivel = data['sensores'][sensor]['observaciones']['Flow_depth']
    nivel = pd.Series(nivel)
    nivel.plot(label=sensor)

plt.legend()
plt.grid()
plt.xticks(rotation=90)
plt.ylim(-0.15,)




base_url = "http://69.28.90.79:5000"  # Update this if your Flask app is running on a different host or port

def consultar_api_nueva(topic, fecha_inicio, fecha_fin):
    # Make a GET request to the /api/rango endpoint with the 'topic', 'fecha_inicio', and 'fecha_fin' parameters
    response = requests.get(
        f"{base_url}/api/rango",
        params={"topic": topic, "fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    )

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        print(f"Datos para el tema '{topic}' en el rango de fechas {fecha_inicio} a {fecha_fin}: {data}")
        return data

    else:
        print(f"Error al obtener datos en el rango de fechas. Codigo de estado: {response.status_code}")


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

observado = consultar_api_nueva

for poi in points_of_interest:
    print(poi)

    fecha_inicio = nivel.index[0]
    fecha_fin = nivel.index[-1]

    if "topic" in points_of_interest[poi]:
        print("Disponible en la API nueva")
        topic = points_of_interest[poi]["topic"]
        df_obs = consultar_api_nueva(topic, fecha_inicio, fecha_fin)
        df_obs.plot(label=poi)

plt.grid()
plt.legend()
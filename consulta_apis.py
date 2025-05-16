import requests
import pandas as pd

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

def consultar_api_anterior(user, nombre, site_id, start_date=None, end_date=None, variables=None):
    """
    Consulta la API de FDX Ingeniería y devuelve los datos como un DataFrame de pandas.

    Parámetros:
    - user: str -> Usuario de la API.
    - site_id: int -> ID del sitio a consultar.
    - start_date: str, opcional -> Fecha de inicio en formato 'YYYY-MM-DD'. Si no se proporciona, se establece una semana atrás.
    - end_date: str, opcional -> Fecha de fin en formato 'YYYY-MM-DD'. Si no se proporciona, se establece la fecha de hoy.
    - variables: list[str], opcional -> Lista de variables específicas a solicitar.

    Retorna:
    - pd.DataFrame con los datos obtenidos.
    """
    if end_date is None:
        end_date = (datetime.now()+ timedelta(days=1)).strftime('%Y-%m-%d')
    if start_date is None:
        dias_consulta=360
        start_date = (datetime.now() - timedelta(days=dias_consulta)).strftime('%Y-%m-%d')
    base_url = "http://api.fdx-ingenieria.com.ar/api_new"
    query_params = {
        "user": user,
        "site_id": site_id,
        "query": "filter_site",
        "date": f"{start_date}@{end_date}"
    }

    if variables:
        query_params["variables"] = ",".join(variables)

    response = requests.get(base_url, params=query_params)

    if response.status_code == 200:
        try:
            json_data = response.json()
            df = pd.DataFrame(json_data)

            if df.empty:
                # print(f"El DataFrame para el sitio {nombre} (id:{site_id}), no tiene datos en los ultimos {dias_consulta} días.")
                print(f"El DataFrame para el sitio {nombre} (id:{site_id}), no tiene datos en el período solicitado.")
                return None  # O devolver un DataFrame vacío, según tus necesidades

            df["hora"] = pd.to_datetime(df["hora"])
            df = df.sort_values(by='hora')
            # Cambiar el tipo de dato de las columnas
            for col in ["nivel", "bateria", "senal"]:
              try:
                df[col] = df[col].astype(float)
              except ValueError as e:
                print(f"Error al convertir la columna {col} a float: {e}")
                # Puedes manejar el error como prefieras, por ejemplo, rellenar con NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except ValueError:
            print("Error al decodificar la respuesta JSON.")
            # print(ValueError)
            print(response.json())
            return None
    else:
        print(f"Error en la solicitud: {response.status_code}")
        return None

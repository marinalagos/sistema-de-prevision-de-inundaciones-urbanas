import os
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


#  0. DEFINIR PYTHONPATH (directorio raíz del repositorio)
repo_path = os.getenv('PYTHONPATH') # Obtener el directorio del repositorio desde la variable de entorno (archivo ".env")
if repo_path:
    os.chdir(repo_path)


# Ruta base donde buscar los archivos
base_path = "data/HIST/POST"

# Obtener el tiempo actual y el límite de 24 horas atrás
now = datetime.utcnow()
last_24_hours = now - timedelta(hours=24)

def get_files_in_last_24_hours(base_path, last_24_hours):
    """Obtiene los archivos en las últimas 24 horas."""
    files = []
    for root, _, filenames in os.walk(base_path):
        for filename in filenames:
            print(filename)
            if filename == "series.json":
                # Extraer la fecha y hora del path
                print("ok")
                try:
                    parts = root.split(os.sep)
                    # Filtrar solo las partes que son números
                    date_parts = [part for part in parts[-5:] if part.isdigit()]
                    if len(date_parts) == 4:
                        yyyy, mm, dd, HHMMss = date_parts
                        file_datetime = datetime(int(yyyy), int(mm), int(dd), int(HHMMss[:2]), int(HHMMss[2:4]), int(HHMMss[4:]))
                        if file_datetime >= last_24_hours:
                            files.append(os.path.join(root, filename))
                except Exception as e:
                    print(f"Error procesando el path {root}: {e}")
    return files


def plot_sensor_data(files):
    """Plotea las series de nivel de todos los sensores superpuestas."""
    plt.figure(figsize=(10, 6))

    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            sensores = data.get("sensores", {})

            for sensor, sensor_data in sensores.items():
                observaciones = sensor_data.get("observaciones", {}).get("Flow_depth", {})
                times = [datetime.fromisoformat(ts.replace("+0000", "")) for ts in observaciones.keys()]
                levels = list(observaciones.values())

                plt.plot(times, levels, label=sensor_data.get("nombre_completo", sensor))

    plt.xlabel("Tiempo")
    plt.ylabel("Nivel (m)")
    plt.title("Niveles de sensores en las últimas 24 horas")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    # plt.show()
    plt.savefig('ver.png')

# Obtener archivos en las últimas 24 horas
files = get_files_in_last_24_hours(base_path, last_24_hours)

if files:
    plot_sensor_data(files)
else:
    print("No se encontraron archivos en las últimas 24 horas.")

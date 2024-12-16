import os

def find_latest_file(root_dir, experimento, file_extension):
    """
    Busca de manera eficiente la carpeta 'experimento' más reciente (según la jerarquía YYYY/MM/DD/HHmmss) 
    dentro de 'root_dir' que contenga al menos un archivo con la extensión requerida.
    La búsqueda se detiene tan pronto como encuentra un archivo válido.
    """
    # Obtener los años en orden descendente
    for year in sorted(os.listdir(root_dir), reverse=True):
        year_path = os.path.join(root_dir, year)
        if not os.path.isdir(year_path) or not year.isdigit():
            continue

        # Obtener los meses en orden descendente
        for month in sorted(os.listdir(year_path), reverse=True):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path) or not month.isdigit():
                continue

            # Obtener los días en orden descendente
            for day in sorted(os.listdir(month_path), reverse=True):
                day_path = os.path.join(month_path, day)
                if not os.path.isdir(day_path) or not day.isdigit():
                    continue

                # Obtener las horas en orden descendente
                for hour in sorted(os.listdir(day_path), reverse=True):
                    hour_path = os.path.join(day_path, hour)
                    if not os.path.isdir(hour_path) or not hour.isdigit():
                        continue

                    # Buscar la carpeta "experimento"
                    experimento_path = os.path.join(hour_path, experimento)
                    if os.path.isdir(experimento_path):
                        # Verificar si hay un archivo .hsf
                        if any(file.endswith(file_extension) for file in os.listdir(experimento_path)):
                            return experimento_path

    return None  # Si no se encontró nada
def modify_textfile(file_path, replacements, stop_at_substring, output_path):
    """
    Modifica palabras clave en un archivo de texto hasta un substring específico.

    Parameters:
    - file_path: Ruta del archivo de texto original.
    - replacements: Diccionario con las palabras clave y sus reemplazos.
    - stop_at_substring: Substring donde dejar de modificar.
    - output_path: Ruta del archivo de texto modificado.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Crear una lista para las líneas modificadas
    modified_lines = []
    stop_reached = False

    for line in lines:
        # Si encontramos el substring, dejamos de modificar
        if stop_at_substring in line:
            stop_reached = True

        # Reemplazar solo si aún no hemos llegado al substring
        if not stop_reached:
            for old_word, new_word in replacements.items():
                line = line.replace(old_word, new_word)

        modified_lines.append(line)

    # Guardar el archivo modificado
    with open(output_path, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)
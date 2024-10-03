import pandas as pd
import requests
import json

# CONSULTA A LA BASE DEL INA
# Obtener token

with open('credenciales.json', 'r') as f:
    content = f.read()
    if not content.strip():
        print("El archivo credenciales.json está vacío.")
    else:
        token_base_INA = json.loads(content)['token_base_INA']

# Obtener listado de EMAs a consultar


"""
-------------------------------------------------------------------------------
TOOL ejecutar_swmm
-------------------------------------------------------------------------------
Prepara* el archivo .inp y el archivo de precipitación. 
Ejecuta SWMM
Guarda los metadatos de la corrida en la base de simulaciones.
Guarda los archivos de salida en la base de outputs.
Guarda el hotstart en la base de hotstarts.
Guarda el archivo de precipitación con sus metadatos en la base de precipitacion.

Dentro de los inputs:
- Fecha inicial y final
- Grilla y fuente de precipitación
- HS de entrada

*Preparar el .inp implica:
- setear fechas de inicio y fin
- modificar las tablas de subcuencas y pluviometros acorde a la grilla utilizada
- indicar ubicación HS de entrada y de salida
- indicar ubicación de los outputs
""". 
#!/bin/bash

# Establecer PYTHONPATH desde .env
export PYTHONPATH=$(grep PYTHONPATH .env | cut -d '=' -f2)

# Eliminar archivos anteriores que no se van a volver a usar
find PAQUETES/swmm_ssd_emas_ina/bin -type f -name "run_swmm_*.sh" -exec rm {} +

# Definir el inicio de la simulación

inicio_sim=$(date -u --date="1 hour ago" +"%Y-%m-%dT%H:00:00Z")
inicio_sim_compacto=$(date -u --date="1 hour ago" +"%Y%m%d%H00")

# Enviar el primer trabajo: Preprocesamiento
job1_id=$(sbatch --parsable <<EOF
#!/bin/bash
#SBATCH --job-name=preprocesamiento
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1
#SBATCH --output=LOGS/pre_%j_$inicio_sim_compacto.log
#SBATCH --time=00:120:00
#SBATCH --mem=1G
#SBATCH --constraint="128667MB"

source /share/apps/anaconda3/bin/activate
conda activate /share/apps/anaconda3/envs/swmm_env

echo "$inicio_sim"
# Exportar PYTHONPATH dentro del job
export PYTHONPATH=$PYTHONPATH

python PAQUETES/swmm_ssd_emas_ina/bin/preprocesamiento.py --inicio_sim "$inicio_sim"
EOF
)
echo "Preprocesamiento enviado con Job ID: $job1_id"


# Enviar el segundo trabajo: Ejecución del archivo run_swmm.sh 

job2_id=$(sbatch --parsable --dependency=afterok:$job1_id <<EOF
#!/bin/bash
#SBATCH --job-name=ejecucion_modelo_$inicio_sim_compacto
#SBATCH --output=LOGS/ejecucion_modelo_%j_$inicio_sim_compacto.log
#SBATCH --time=00:120:00
#SBATCH --constraint="128667MB"                               
#SBATCH --cpus-per-task=4
#SBATCH --ntasks=1

source /share/apps/anaconda3/bin/activate
conda activate /share/apps/anaconda3/envs/swmm_env

# Verificar que el archivo run_swmm.sh existe y tiene permisos
echo "Verificando si el archivo run_swmm_$inicio_sim_compacto.sh existe..."
if [ -f "PAQUETES/swmm_ssd_emas_ina/bin/run_swmm_$inicio_sim_compacto.sh" ]; then
    echo "Archivo run_swmm_$inicio_sim_compacto.sh encontrado."
else
    echo "ERROR: No se encontró el archivo run_swmm_$inicio_sim_compacto.sh."
    exit 1
fi

chmod 775 PAQUETES/swmm_ssd_emas_ina/bin/run_swmm_$inicio_sim_compacto.sh

echo "Verificando permisos de ejecución del archivo run_swmm_$inicio_sim_compacto.sh..."
ls -l PAQUETES/swmm_ssd_emas_ina/bin/run_swmm_$inicio_sim_compacto.sh

# Agregar un comando para verificar la hora antes de ejecutar srun
echo "Hora antes de ejecutar srun: $(date)"

# Ejecutar srun para ejecutar el script run_swmm.sh
echo "Ejecutando srun con el archivo run_swmm_$inicio_sim_compacto.sh..."
srun PAQUETES/swmm_ssd_emas_ina/bin/run_swmm_$inicio_sim_compacto.sh

# Agregar un comando para verificar la hora después de ejecutar srun
echo "Hora después de ejecutar srun: $(date)"

# Verificar si el srun terminó correctamente
if [ $? -eq 0 ]; then
    echo "srun ejecutado correctamente."
else
    echo "ERROR: srun falló."
    exit 1
fi


# Si el hotstart falla (ERROR 335)
# Encontrar rpt para ver si tenemos ese error:
rpt_file=$(awk '/swmm5_1-011-cluster/ {print $3}' "$(realpath PAQUETES/swmm_ssd_emas_ina/bin/run_swmm_$inicio_sim_compacto.sh)")

# Verificar si el archivo "model.rpt" contiene el substring "ERROR 335" en las últimas 10 líneas
if tail -n 10 "$rpt_file" | grep -q "ERROR 335"; then
    echo "Se detectó 'ERROR 335' en $rpt_file"

    # Extraer el path del archivo log de preprocesamiento (job1)
    path_hsf=$(awk -F'INPHSF:' '/INPHSF:/ {print $2}' "$(realpath LOGS/pre_${job1_id}_${inicio_sim_compacto}.log)")
    
    if [ -n "$path_hsf" ]; then
        # Construir el path completo del archivo a borrar
        file_to_delete="$path_hsf/hotstart.hsf"
        
        if [ -e "$file_to_delete" ]; then
            echo "Eliminando archivo: $file_to_delete"
            rm "$file_to_delete"

            # Reiniciar el mismo script
            echo "Reiniciando $0"
            exec bash "$0"

        else
            echo "El archivo no existe: $file_to_delete"
        fi
    else
        echo "No se encontró el path en "LOGS/pre_${job1_id}_${inicio_sim_compacto}.log"
    fi

else
    echo " "
fi
EOF
)
echo "Ejecución del modelo enviada con Job ID: $job2_id"


# Enviar el tercer trabajo: Postprocesamiento
job3_id=$(sbatch --parsable --dependency=afterok:$job2_id <<EOF
#!/bin/bash
#SBATCH --job-name=postprocesamiento
#SBATCH --output=LOGS/post_%j_$inicio_sim_compacto.log
#SBATCH --time=00:120:00
#SBATCH --constraint="128667MB"                               
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1
#SBATCH --mem=3G

source /share/apps/anaconda3/bin/activate
conda activate /share/apps/anaconda3/envs/swmm_env

echo "$inicio_sim"
python PAQUETES/swmm_ssd_emas_ina/bin/postprocesamiento.py --inicio_sim "$inicio_sim"
EOF
)
echo "Postprocesamiento enviado con Job ID: $job3_id"

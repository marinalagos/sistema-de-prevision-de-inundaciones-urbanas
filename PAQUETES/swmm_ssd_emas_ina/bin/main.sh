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

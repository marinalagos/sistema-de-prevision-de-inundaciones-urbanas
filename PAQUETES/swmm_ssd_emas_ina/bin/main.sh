#!/bin/bash

# Establecer PYTHONPATH desde .env
export PYTHONPATH=$(grep PYTHONPATH .env | cut -d '=' -f2)

# Definir el inicio de la simulación
current_hour=$(date -u +"%H")
previous_hour=$(printf "%02d" $((10#$current_hour - 1)))
current_date=$(date -u +"%Y-%m-%d")
inicio_sim="${current_date}T${previous_hour}:00:00Z"

# Enviar el primer trabajo: Preprocesamiento
job1_id=$(sbatch --parsable <<EOF
#!/bin/bash
#SBATCH --job-name=preprocesamiento
#SBATCH --output=pre_%j_$inicio_sim.log
#SBATCH --time=00:120:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --nodelist=compute-0-[22-24]

source /share/apps/anaconda3/bin/activate
conda activate /share/apps/anaconda3/envs/swmm_env

echo "$inicio_sim"
# Exportar PYTHONPATH dentro del job
export PYTHONPATH=$PYTHONPATH

python PAQUETES/swmm_ssd_emas_ina/bin/preprocesamiento.py --inicio_sim "$inicio_sim"
EOF
)
echo "Preprocesamiento enviado con Job ID: $job1_id"

# Enviar el segundo trabajo: Ejecución del archivo run_swmm.sh (ya contiene requerimientos)
job2_id=$(sbatch --parsable --dependency=afterok:$job1_id PAQUETES/swmm_ssd_emas_ina/bin/run_swmm.sh)
echo "Ejecución del modelo enviada con Job ID: $job2_id"

# Enviar el tercer trabajo: Postprocesamiento
job3_id=$(sbatch --parsable --dependency=afterok:$job2_id <<EOF
#!/bin/bash
#SBATCH --job-name=postprocesamiento
#SBATCH --output=post_%j_$inicio_sim.log
#SBATCH --time=00:120:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --nodelist=compute-0-[22-24]

source /share/apps/anaconda3/bin/activate
conda activate /share/apps/anaconda3/envs/swmm_env

echo "$inicio_sim"
python PAQUETES/swmm_ssd_emas_ina/bin/postprocesamiento.py --inicio_sim "$inicio_sim"
EOF
)
echo "Postprocesamiento enviado con Job ID: $job3_id"

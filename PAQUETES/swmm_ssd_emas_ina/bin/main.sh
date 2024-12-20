#!/bin/bash

# Enviar el primer trabajo: Preprocesamiento
job1_id=$(sbatch --parsable <<EOF
#!/bin/bash
#SBATCH --job-name=preprocesamiento
#SBATCH --output=preprocesamiento.log
#SBATCH --time=00:120:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --nodelist=compute-0-[22-24]

source env_sistema_operativo/bin/activate
python preprocesamiento.py
EOF
)
echo "Preprocesamiento enviado con Job ID: $job1_id"

# Enviar el segundo trabajo: Ejecución del archivo run_swmm.sh (ya contiene requerimientos)
job2_id=$(sbatch --parsable --dependency=afterok:$job1_id run_swmm.sh)
echo "Ejecución del modelo enviada con Job ID: $job2_id"

# Enviar el tercer trabajo: Postprocesamiento
job3_id=$(sbatch --parsable <<EOF
#!/bin/bash
#SBATCH --job-name=postprocesamiento
#SBATCH --output=postprocesamiento.log
#SBATCH --time=00:120:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --nodelist=compute-0-[22-24]

source env_sistema_operativo/bin/activate
python postprocesamiento.py
EOF
)
echo "Postprocesamiento enviado con Job ID: $job3_id"

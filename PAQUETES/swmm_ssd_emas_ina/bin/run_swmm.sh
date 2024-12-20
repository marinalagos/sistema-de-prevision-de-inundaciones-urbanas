#!/bin/bash
#
#SBATCH --cpus-per-task=4
#SBATCH --job-name=swmm_ssd_emas_ina_202412190400
#SBATCH --output=data/HIST/ASIM/2024/12/19/040000/swmm_ssd_emas_ina/log.txt
#SBATCH --time=192:00:00
#SBATCH --nodelist=compute-0-[22-24]

srun MODELS/swmm5_1-011-cluster data/HIST/PREP/2024/12/19/040000/swmm_ssd_emas_ina//model.inp data/HIST/ASIM/2024/12/19/040000/swmm_ssd_emas_ina//model.rpt data/HIST/ASIM/2024/12/19/040000/swmm_ssd_emas_ina//model.out"

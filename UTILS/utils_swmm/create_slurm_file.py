def create_slurm_file(path_slurm_file, path_swmm, pathdir_model, pathdir_out, jobname, logfile, nodelist, cpupertask, errorfile):
    string = f"""#!/bin/bash
#
#SBATCH --cpus-per-task={cpupertask}
#SBATCH --job-name={jobname}
#SBATCH --output={logfile}
#SBATCH --error={errorfile}
#SBATCH --time=192:00:00
#SBATCH --nodelist={nodelist}

srun {path_swmm} {pathdir_model}/model.inp {pathdir_out}/model.rpt {pathdir_out}/model.out
"""

    with open(path_slurm_file, "w") as file:
        file.write(string)


def create_bash_file(path_bash_file, path_swmm, pathdir_model, pathdir_out):
    string = f"""#!/bin/bash

./{path_swmm} {pathdir_model}/model.inp {pathdir_out}/model.rpt {pathdir_out}/model.out
"""

    with open(path_bash_file, "w") as file:
        file.write(string)
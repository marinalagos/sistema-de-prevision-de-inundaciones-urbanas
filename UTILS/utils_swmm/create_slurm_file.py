def create_slurm_file(path_slurm_file, pathdir_model, path_swmm, jobname, logfile, nodelist, cpupertask):
    string = f"""#!/bin/bash
    #
    #SBATCH --cpus-per-task={cpupertask}
    #SBATCH --job-name={jobname}
    #SBATCH --output={logfile}
    #SBATCH --time=192:00:00
    #SBATCH --nodelist={nodelist}
    
    srun {path_swmm} {path_model}/model.inp {path_model}/model.rpt {path_model}/model.out"
    """

    # Escribir en el archivo
    with open(path_slurm_file, "w") as file:
        file.write(script)
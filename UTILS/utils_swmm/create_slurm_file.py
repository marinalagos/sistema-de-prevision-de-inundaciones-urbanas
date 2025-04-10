def create_slurm_file(path_slurm_file, path_swmm, pathdir_model, pathdir_out):
    string = f"""#!/bin/bash

pwd
./{path_swmm} {pathdir_model}/model.inp {pathdir_out}/model.rpt {pathdir_out}/model.out
"""

    with open(path_slurm_file, "w") as file:
        file.write(string)

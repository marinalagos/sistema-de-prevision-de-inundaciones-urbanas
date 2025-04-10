def create_slurm_file(path_slurm_file, path_swmm, dirpath_model, dirpath_out):
    string = f"""#!/bin/bash

pwd
./{path_swmm} {dirpath_model}/model.inp {dirpath_out}/model.rpt {dirpath_out}/model.out
"""

    with open(path_slurm_file, "w") as file:
        file.write(string)

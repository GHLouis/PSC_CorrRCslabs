import os
import csv
import sys


# set the working directory to the current directory of this script
# here d:\hku\Lin Project is the local path, please change it to your own local path
local_dir = r"d:\hku\Lin Project\-"
module_dir = local_dir + r"\Code\Batch_Dealing"

# old file path
# module_dir = r"E:\model"

# import modules for use in Diana
sys.path.append(module_dir)

import construct_diana_model
import export_output_to_csv
import get_reaction_force
import run_analysis

# share DIANA's built-in functions with all submodules, including run_analysis
for key, value in list(globals().items()):
    if not key.startswith('__'):
        if key != 'construct_diana_model':
            setattr(construct_diana_model, key, value)
        if key != 'get_reaction_force':
            setattr(get_reaction_force, key, value)
        if key != 'export_output_to_csv':
            setattr(export_output_to_csv, key, value)
        if key != 'run_analysis':
            setattr(run_analysis, key, value)


# read parameters from csv file
csv_path = module_dir + r"\parameters.csv"

# old one 
# csv_path = r"E:\model\parameters.csv"

X = []
with open(csv_path, 'r') as f:
    reader = csv.reader(f)
    next(reader, None)
    for row in reader:
        X.append([float(val) for val in row])
dpf_num = len(X)
print(f"successfully read {len(X)} sets of parameters from {csv_path}")

# ================== main function ==================
if __name__ == "__main__":
    for i in range(2):
        model_name = f"model_{i}"

        # create a new project for each set of parameters
        project_name = local_dir + rf'\model\{model_name}'
        
        # old one
        # project_name = rf'E:\model\{model_name}'

        print(f"successfully create a new project {project_name}")

        newProject(project_name, 1000.0)
        setModelAnalysisAspects( [ "STRUCT" ] )
        setModelDimension( "3D" )
        setDefaultMeshOrder( "LINEAR" )
        setDefaultMesherType( "HEXQUAD" )
        setUnit("Length", "mm")
        setUnit("Force", "N")
        # construct diana model according to the provided parameters
        print(X[i])
        construct_diana_model.construct_diana_model(X[i])
        saveProject()
        # build analysis file
        run_analysis.run_analysis()
        saveProject()
        # run diana analysis
        runSolver(analyses())
        # output the reaction force, and export to csv file
        force_result = get_reaction_force.get_reaction_force()
        print(f"successfully get the reaction force {force_result} for the {i}th model")

        export_output_to_csv.export_output_to_csv(csv_path, force_result, i)
        closeProject()
        print(f"successfully run the {i}th model")

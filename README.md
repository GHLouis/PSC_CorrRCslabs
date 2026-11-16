# Batch evaluation of DIANA models

This script runs prebuilt DIANA 10.3 project files and writes the calculated capacity for each model to a summary CSV. Model filenames must **strictly follow the naming convention and parameter bounds** specified in the opening comments of `run_diana_batch.py`.

## Running the script

1. Build and save the DIANA models as `.dpf` files. Place `run_diana_batch.py` in the same folder as the models.
2. Open a blank project in DIANA 10.3.
3. Select **File > Run Saved Script > Load Script** , then choose `run_diana_batch.py`.
4. The script scans that folder and runs each correctly named `.dpf` file in sequence. It writes the current model's result before opening the next model.

##

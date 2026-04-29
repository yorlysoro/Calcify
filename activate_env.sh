#!/bin/bash
conda deactivate
# Elimina cualquier rastro de Conda en las variables de entorno
unset CONDA_PREFIX
unset CONDA_DEFAULT_ENV
unset CONDA_EXE
unset CONDA_PYTHON_EXE

# Asegura que el PATH priorice los binarios del sistema
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
source .env/bin/activate
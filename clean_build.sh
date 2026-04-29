#/bin/bash
conda deactivate
# Limpia el directorio .env
if [ -d ".env" ]; then
    rm -rf .env
    echo "Directorio .env eliminado."
else
    echo "El directorio .env no existe."
fi

# Elimina cualquier rastro de Conda en las variables de entorno
unset CONDA_PREFIX
unset CONDA_DEFAULT_ENV
unset CONDA_EXE
unset CONDA_PYTHON_EXE

# Asegura que el PATH priorice los binarios del sistema
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games

python3 -m venv --system-site-packages .env
source .venv/bin/activate
pip install -r requirements.txt
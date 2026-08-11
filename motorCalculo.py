import os
import sys
import glob
import subprocess
import yaml


yaml_file_path = 'parameters.yaml'
with open(yaml_file_path, 'r') as file:
    config = yaml.safe_load(file)

for dimension in config['dimensions']:
    print(dimension['name'])
    folder = 'functions_module_ish_'+ dimension['name']
    if os.path.isdir(folder):
        script_path = os.path.join(folder, 'calcular_dimensao.py')
        if os.path.isfile(script_path):
            try:
                subprocess.run(['python3', script_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar {script_path}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Erro inesperado ao executar {script_path}: {e}", file=sys.stderr)
        else:
            print(f"Arquivo {script_path} não encontrado em {folder}", file=sys.stderr)

import yaml
import pandas as pd

yaml_file_path = 'scenario.yaml'
with open(yaml_file_path, 'r') as file:
    config = yaml.safe_load(file)

dimensions = config['dimensions']

# Encontra dimensão e já extrai os pesos
dimensao = next((d for d in dimensions if d['name'] == 'ire_cs_hum'), None)
dados_string = ['fid', 'COBACIA', 'cod_setor', 'cod_mun', 'bal_perc']
dtype_dict = {col: str for col in dados_string}

csv_path = dimensao['path']
tabela_central = pd.read_csv(f'{csv_path}', dtype=dtype_dict)

# Seleciona apenas as colunas desejadas
tabela_central = tabela_central[dados_string]

print(tabela_central.head())
print(dimensao['path'])
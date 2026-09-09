import pandas as pd
import yaml
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importa as funções de conversão
try:
    from convertion_functions import *
except ImportError as e:
    logger.error(f"Erro ao importar 'convertion_functions': {e}")
    sys.exit(1)

def normalize_path(path_str: str) -> Path:
    """
    Normaliza caminhos para funcionar em Linux e Windows
    
    Args:
        path_str: String do caminho
        
    Returns:
        Path: Objeto Path normalizado
    """
    # Substitui barras invertidas por barras normais
    path_str = path_str.replace('\\', '/')
    
    # Remove espaços em branco extras
    path_str = path_str.strip()
    
    # Expande variáveis de ambiente se existirem
    path_str = os.path.expandvars(path_str)
    
    # Expande ~ para diretório home (funciona em Linux e Windows)
    path_str = os.path.expanduser(path_str)
    
    return Path(path_str)

def detect_encoding(file_path: Path) -> str:
    """
    Detecta o encoding correto para o arquivo
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        str: Encoding a ser usado
    """
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read()
                logger.debug(f"Encoding detectado: {encoding}")
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Fallback para utf-8 com substituição de caracteres
    logger.warning(f"Não foi possível detectar encoding, usando utf-8 com fallback")
    return 'utf-8'

def safe_read_csv(file_path: Path, **kwargs) -> pd.DataFrame:
    """
    Lê CSV de forma segura com detecção automática de encoding
    
    Args:
        file_path: Caminho do arquivo CSV
        **kwargs: Argumentos adicionais para pd.read_csv
        
    Returns:
        pd.DataFrame: DataFrame lido
    """
    try:
        # Tenta ler com encoding detectado
        encoding = detect_encoding(file_path)
        return pd.read_csv(file_path, dtype='str', encoding=encoding, **kwargs)
    except Exception as e:
        logger.error(f"Erro ao ler CSV {file_path}: {e}")
        raise

def validate_yaml_config(config: Dict) -> bool:
    """
    Valida a estrutura do arquivo YAML
    
    Args:
        config: Dicionário com a configuração
        
    Returns:
        bool: True se válido, False caso contrário
    """
    required_keys = ['dimensions']
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Chave obrigatória '{key}' não encontrada no YAML")
            return False
    
    if not isinstance(config['dimensions'], list):
        logger.error("'dimensions' deve ser uma lista")
        return False
    
    for idx, dimension in enumerate(config['dimensions']):
        if 'path' not in dimension:
            logger.error(f"Dimensão {idx}: campo 'path' não encontrado")
            return False
        
        if 'indicadores' not in dimension:
            logger.warning(f"Dimensão {idx}: campo 'indicadores' não encontrado")
            dimension['indicadores'] = []
    
    return True

def functions_module_ish_hum(yaml_file_path: str) -> Optional[pd.DataFrame]:
    """
    Função principal que processa os dados
    
    Args:
        yaml_file_path: Caminho para o arquivo YAML de configuração
        
    Returns:
        pd.DataFrame: DataFrame com os resultados ou None em caso de erro
    """
    # Normaliza o caminho do YAML
    yaml_path = normalize_path(yaml_file_path)
    
    # Verifica se o arquivo existe
    if not yaml_path.exists():
        logger.error(f"Arquivo YAML não encontrado: {yaml_path}")
        logger.info(f"Diretório atual: {os.getcwd()}")
        return None
    
    # Carrega o YAML
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logger.info(f"YAML carregado com sucesso: {yaml_path}")
    except Exception as e:
        logger.error(f"Erro ao carregar YAML: {e}")
        return None
    
    # Valida a configuração
    if not validate_yaml_config(config):
        return None
    
    # Cria diretórios necessários se configurados
    if 'intermediario' in config:
        interm_path = normalize_path(config['intermediario'])
        interm_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório intermediário criado/verificado: {interm_path.parent}")
    
    if 'output' in config and 'path' in config['output']:
        output_path = normalize_path(config['output']['path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de saída criado/verificado: {output_path.parent}")
    
    dimensions = config['dimensions']
    dados_gerais = pd.DataFrame()
    
    # Processa cada arquivo
    for idx, dimension in enumerate(dimensions):
        try:
            # Normaliza o caminho do arquivo
            file_path = normalize_path(dimension['path'])
            logger.info(f"Processando dimensão {idx+1}/{len(dimensions)}: {file_path}")
            
            # Verifica se o arquivo existe
            if not file_path.exists():
                logger.warning(f"Arquivo não encontrado: {file_path}")
                continue
            
            # Lê o CSV com detecção automática de encoding
            df = safe_read_csv(file_path)
            
            if dados_gerais.empty:
                dados_gerais = df
                logger.info(f"DataFrame inicial criado com {len(df)} linhas e {len(df.columns)} colunas")
            else:
                # Encontra a chave de junção
                chave = None
                for possible_key in ['COBACIA', 'cod_mun']:
                    if possible_key in df.columns:
                        chave = possible_key
                        break
                
                if chave is None:
                    logger.warning(f"  ⚠️ Sem chave para junção! Pulando arquivo {file_path}")
                    continue
                
                # Verifica se a chave existe no DataFrame geral
                if chave not in dados_gerais.columns:
                    logger.warning(f"  ⚠️ Chave '{chave}' não encontrada no DataFrame geral!")
                    continue
                
                df = df.dropna(subset=[chave])
                
                # Cria dicionário de mapeamento
                mapping = {}
                for col in df.columns:
                    if col != chave:
                        unique_df = df.drop_duplicates(subset=[chave], keep='first')
                        mapping[col] = unique_df.set_index(chave)[col].to_dict()
                
                # Aplica o mapping
                for col in mapping:
                    if col not in dados_gerais.columns:
                        dados_gerais[col] = dados_gerais[chave].map(mapping[col])
                
                logger.info(f"  DataFrames mesclados usando chave '{chave}'")
            
            # Aplica as funções da dimensão
            if 'indicadores' in dimension:
                for item in dimension['indicadores']:
                    nome_funcao = item['name']
                    logger.debug(f"  Aplicando função: {nome_funcao}")
                    
                    if nome_funcao in globals() and callable(globals()[nome_funcao]):
                        funcao = globals()[nome_funcao]
                        try:
                            if 'pesos' in item:
                                pesos = item['pesos']
                                dados_gerais[nome_funcao] = funcao(dados_gerais, pesos=pesos)
                            else:
                                dados_gerais[nome_funcao] = funcao(dados_gerais)
                            logger.debug(f"  ✅ Função '{nome_funcao}' aplicada")
                        except Exception as e:
                            logger.error(f"  ❌ Erro ao aplicar função '{nome_funcao}': {e}")
                    else:
                        logger.warning(f"  ⚠️ Função '{nome_funcao}' não encontrada!")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar dimensão {idx}: {e}")
            continue
    
    # Verifica se há dados
    if dados_gerais.empty:
        logger.error("❌ Nenhum dado processado!")
        return None
    
    logger.info(f"DataFrame final tem {len(dados_gerais)} linhas e {len(dados_gerais.columns)} colunas")
    
    # Salva arquivo intermediário
    if 'intermediario' in config:
        interm_path = normalize_path(config['intermediario'])
        try:
            dados_gerais.to_csv(interm_path, index=False, encoding='utf-8')
            logger.info(f"✅ Arquivo intermediário salvo em: {interm_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar arquivo intermediário: {e}")
    
    # Processa pesos e calcula resultado final
    try:
        # Processar pesos
        pesos = {}
        if 'result' in config:
            for item in config['result']:
                if item.get('name') == 'ire_cs_hum' and 'depends_on' in item:
                    for dep in item['depends_on']:
                        pesos[dep['name']] = dep.get('peso', 0)
        
        # Verifica colunas necessárias
        colunas_necessarias = ['ire_hu_pop', 'ire_hu_cobred']
        colunas_faltando = [col for col in colunas_necessarias if col not in dados_gerais.columns]
        
        if colunas_faltando:
            logger.warning(f"⚠️ Colunas faltando: {colunas_faltando}")
            for col in colunas_faltando:
                dados_gerais[col] = 0
                logger.warning(f"  Criando coluna '{col}' com zeros")
        
        # Converte colunas para numérico
        for col in colunas_necessarias:
            if col in dados_gerais.columns:
                dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
                dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
                # Substitui NaN por 0
                dados_gerais[col] = dados_gerais[col].fillna(0)
        
        # Define pesos
        peso_ire_hu_pop = float(pesos.get('ire_hu_pop', 0.5))
        peso_ire_hu_cobred = float(pesos.get('ire_hu_cobred', 0.5))
        
        logger.info(f"Pesos usados: ire_hu_pop={peso_ire_hu_pop}, ire_hu_cobred={peso_ire_hu_cobred}")
        
        # Calcula ire_cs_hum
        if 'ire_cs_hum' in globals() and callable(globals()['ire_cs_hum']):
            dados_gerais['ire_cs_hum'] = dados_gerais.apply(
                lambda row: ire_cs_hum(
                    row['ire_hu_pop'], peso_ire_hu_pop,
                    row['ire_hu_cobred'], peso_ire_hu_cobred
                ), axis=1
            )
            logger.info("✅ Cálculo de 'ire_cs_hum' concluído")
        else:
            logger.error("❌ Função 'ire_cs_hum' não encontrada!")
            return None
        
        # Prepara resultado final
        if 'COBACIA' in dados_gerais.columns:
            dados_resultado = dados_gerais[['COBACIA', 'ire_cs_hum']]
            
            # Salva resultado final
            if 'output' in config and 'path' in config['output']:
                output_path = normalize_path(config['output']['path'])
                try:
                    dados_resultado.to_csv(output_path, index=False, encoding='utf-8')
                    logger.info(f"✅ Resultado final salvo em: {output_path}")
                except Exception as e:
                    logger.error(f"❌ Erro ao salvar resultado final: {e}")
            
            # Salva dados completos novamente
            if 'intermediario' in config:
                interm_path = normalize_path(config['intermediario'])
                try:
                    dados_gerais.to_csv(interm_path, index=False, encoding='utf-8')
                    logger.info(f"✅ Dados completos atualizados: {interm_path}")
                except Exception as e:
                    logger.error(f"❌ Erro ao atualizar dados completos: {e}")
            
            logger.info(f"✅ Processamento concluído com sucesso!")
            return dados_resultado
        else:
            logger.error("❌ Coluna 'COBACIA' não encontrada nos dados")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro no cálculo final: {e}")
        return None

def get_user_input() -> str:
    """
    Obtém o caminho do arquivo YAML do usuário
    """
    print("\n" + "="*60)
    print("Sistema de Processamento ISH - Humano")
    print("="*60)
    
    # Opções de caminho
    default_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_hum/parameters.yaml"
    
    # Detecta sistema operacional
    if sys.platform == 'win32':
        print("Sistema operacional: Windows")
        default_path = default_path.replace('/', '\\')
    else:
        print("Sistema operacional: Linux/Unix")
    
    print(f"\nCaminho padrão: {default_path}")
    user_input = input("\nDigite o caminho do arquivo YAML (ou Enter para usar o padrão): ").strip()
    
    if not user_input:
        return default_path
    return user_input

if __name__ == "__main__":
    # Configuração de logging
    logging.getLogger().setLevel(logging.INFO)
    
    try:
        # Pode usar caminho fixo ou solicitar ao usuário
        # yaml_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_hum/parameters.yaml"
        
        # Ou solicitar ao usuário
        yaml_path = get_user_input()
        
        # Verifica se o arquivo existe
        if not Path(yaml_path).exists():
            logger.error(f"Arquivo não encontrado: {yaml_path}")
            logger.info(f"Diretório atual: {os.getcwd()}")
            sys.exit(1)
        
        # Executa a função principal
        result = functions_module_ish_hum(yaml_path)
        
        if result is not None:
            print(f"\n✅ Processamento concluído!")
            print(f"✅ {len(result)} registros processados")
            print(f"✅ Primeiros 5 resultados:")
            print(result.head())
        else:
            print("\n❌ Processamento falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Processamento interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro não tratado: {e}")
        sys.exit(1)
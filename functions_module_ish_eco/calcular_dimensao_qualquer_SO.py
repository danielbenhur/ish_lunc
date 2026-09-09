import pandas as pd
import yaml
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from convertion_functions import *

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constantes
CHAVES_POSSIVEIS = ['COBACIA', 'cod_mun', 'mun_nm', 'Município', 'cod_ibge']

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
    required_keys = ['dimensions', 'intermediario', 'output']
    
    for key in required_keys:
        if key not in config:
            logger.error(f"Chave obrigatória '{key}' não encontrada no YAML")
            return False
    
    if not isinstance(config['dimensions'], list):
        logger.error("'dimensions' deve ser uma lista")
        return False
    
    if 'path' not in config['output']:
        logger.error("'output.path' não encontrado no YAML")
        return False
    
    for idx, dimension in enumerate(config['dimensions']):
        if 'path' not in dimension:
            logger.error(f"Dimensão {idx}: campo 'path' não encontrado")
            return False
        
        if 'indicadores' not in dimension:
            logger.warning(f"Dimensão {idx}: campo 'indicadores' não encontrado")
            dimension['indicadores'] = []
    
    return True

def aplicar_mapeamentos_com_merge(
    dados_gerais: pd.DataFrame, 
    df_novo: pd.DataFrame, 
    chave: str, 
    fillna_value: int = 0
) -> pd.DataFrame:
    """
    Aplica mapeamentos usando merge em vez de map.
    Mantém todas as cidades e trata novas cidades com fallback.
    
    Args:
        dados_gerais: DataFrame principal
        df_novo: Novo DataFrame para mesclar
        chave: Nome da coluna chave
        fillna_value: Valor para preencher NaN em colunas numéricas
        
    Returns:
        pd.DataFrame: DataFrame mesclado
    """
    if chave not in dados_gerais.columns:
        logger.warning(f"⚠️ Chave '{chave}' não encontrada em dados_gerais")
        logger.debug(f"   Colunas disponíveis: {dados_gerais.columns.tolist()}")
        return dados_gerais
    
    if chave not in df_novo.columns:
        logger.warning(f"⚠️ Chave '{chave}' não encontrada em df_novo")
        return dados_gerais
    
    # Remove duplicatas do novo DataFrame (mantém o primeiro valor)
    df_novo_unique = df_novo.drop_duplicates(subset=[chave], keep='first')
    
    # Seleciona apenas colunas que não existem em dados_gerais (exceto a chave)
    novas_colunas = [col for col in df_novo_unique.columns 
                     if col != chave and col not in dados_gerais.columns]
    
    if not novas_colunas:
        logger.debug(f"   ℹ️ Nenhuma nova coluna para adicionar")
        return dados_gerais
    
    logger.info(f"📋 Adicionando {len(novas_colunas)} colunas: {novas_colunas[:5]}{'...' if len(novas_colunas) > 5 else ''}")
    
    # Verifica quantas cidades serão afetadas
    cidades_dados_gerais = set(dados_gerais[chave].dropna())
    cidades_df_novo = set(df_novo_unique[chave])
    cidades_faltando = cidades_dados_gerais - cidades_df_novo
    
    if cidades_faltando:
        logger.debug(f"📌 {len(cidades_faltando)} cidades não encontradas no arquivo fonte")
        if len(cidades_faltando) <= 5:
            logger.debug(f"   Exemplos: {list(cidades_faltando)}")
        else:
            logger.debug(f"   Exemplos: {list(cidades_faltando)[:5]}...")
    
    # Faz o merge (LEFT JOIN mantém todas as cidades de dados_gerais)
    dados_gerais = dados_gerais.merge(
        df_novo_unique[[chave] + novas_colunas],
        on=chave,
        how='left'
    )
    
    # Preenche valores NaN para as novas colunas
    for col in novas_colunas:
        if col in dados_gerais.columns:
            # Verifica o tipo de dado da coluna no DataFrame original
            tipo_original = df_novo[col].dtype
            
            if pd.api.types.is_numeric_dtype(tipo_original):
                # Para colunas numéricas, preenche com 0 ou valor específico
                dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
                dados_gerais[col] = dados_gerais[col].fillna(fillna_value)
            else:
                # Para colunas não numéricas, preenche com 'N/A' ou string específica
                dados_gerais[col] = dados_gerais[col].fillna('N/A')
    
    return dados_gerais

def aplicar_funcoes_dimensionais(
    dados_gerais: pd.DataFrame, 
    dimension: Dict[str, Any]
) -> pd.DataFrame:
    """
    Aplica as funções específicas para cada dimensão
    
    Args:
        dados_gerais: DataFrame principal
        dimension: Dicionário com configurações da dimensão
        
    Returns:
        pd.DataFrame: DataFrame com funções aplicadas
    """
    for item in dimension['indicadores']:
        nome_funcao = item['name']
        
        # Verifica se a função existe
        if nome_funcao in globals() and callable(globals()[nome_funcao]):
            funcao = globals()[nome_funcao]
            try:
                # Executa a função aplicando pesos se necessário
                if 'pesos' in item and 'depends_on' in item:
                    pesos = item['pesos']
                    depends_on = item['depends_on']
                    resultado = funcao(dados_gerais, parametros=depends_on, pesos=pesos)
                else:
                    resultado = funcao(dados_gerais)
                
                # Verifica se retornou algo
                if resultado is not None:
                    dados_gerais[nome_funcao] = resultado
                    logger.debug(f"   ✅ Função '{nome_funcao}' aplicada com sucesso")
                else:
                    logger.warning(f"   ⚠️ Função '{nome_funcao}' retornou None!")
                    
            except Exception as e:
                logger.error(f"   ❌ Erro ao executar '{nome_funcao}': {e}")
        else:
            logger.warning(f"   ❌ Função '{nome_funcao}' não encontrada no escopo global!")
    
    return dados_gerais

def functions_module_ish_eco(yaml_file_path: str) -> Optional[pd.DataFrame]:
    """
    Função principal que processa os dados ecológicos
    
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
    
    # Cria diretórios necessários
    if 'intermediario' in config:
        interm_path = normalize_path(config['intermediario'])
        interm_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório intermediário criado/verificado: {interm_path.parent}")
    
    if 'output' in config and 'path' in config['output']:
        output_path = normalize_path(config['output']['path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de saída criado/verificado: {output_path.parent}")
    
    dimensions = config['dimensions']
    
    # Carrega dados gerais do arquivo intermediário
    interm_path = normalize_path(config['intermediario'])
    if not interm_path.exists():
        logger.error(f"Arquivo intermediário não encontrado: {interm_path}")
        return None
    
    try:
        dados_gerais = safe_read_csv(interm_path)
        logger.info(f"📊 dados_gerais carregado: {len(dados_gerais)} linhas, {len(dados_gerais.columns)} colunas")
        logger.debug(f"   Colunas: {dados_gerais.columns.tolist()}")
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo intermediário: {e}")
        return None
    
    # Lista de possíveis chaves (em ordem de preferência)
    CHAVES_POSSIVEIS = ['COBACIA', 'cod_mun', 'mun_nm', 'Município', 'cod_ibge']
    
    # Processar cada arquivo e aplicar as funções
    for idx, dimension in enumerate(dimensions, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"📁 Processando dimensão {idx}/{len(dimensions)}: {dimension.get('name', 'Sem nome')}")
        logger.info(f"{'='*60}")
        
        file_path = normalize_path(dimension['path'])
        
        # Verifica se o arquivo existe
        if not file_path.exists():
            logger.warning(f"   Arquivo não encontrado: {file_path}")
            continue
        
        try:
            df = safe_read_csv(file_path)
            logger.info(f"   Arquivo: {file_path}")
            logger.info(f"   Linhas: {len(df)}, Colunas: {len(df.columns)}")
        except Exception as e:
            logger.error(f"   Erro ao ler arquivo {file_path}: {e}")
            continue
        
        if dados_gerais.empty:
            dados_gerais = df
            logger.info("   📌 Primeiro DataFrame carregado como base")
            continue
        
        # Encontra a chave no DataFrame atual
        chave = None
        for possible_key in CHAVES_POSSIVEIS:
            if possible_key in df.columns:
                chave = possible_key
                break
        
        if chave is None:
            logger.warning(f"   ⚠️ Nenhuma chave encontrada! Pulando este arquivo...")
            continue
        
        logger.info(f"   🔑 Chave identificada: '{chave}'")
        
        # Remove linhas com valores nulos na chave
        df = df.dropna(subset=[chave])
        logger.info(f"   📊 Após remover nulos: {len(df)} linhas")
        
        # Verifica se a chave existe em dados_gerais
        if chave not in dados_gerais.columns:
            logger.warning(f"   ⚠️ Chave '{chave}' não encontrada em dados_gerais")
            logger.info(f"   Tentando encontrar chave alternativa em dados_gerais...")
            
            # Tenta encontrar uma chave alternativa
            chave_alternativa = None
            for key in CHAVES_POSSIVEIS:
                if key in dados_gerais.columns:
                    chave_alternativa = key
                    break
            
            if chave_alternativa:
                logger.info(f"   🔄 Usando chave alternativa: '{chave_alternativa}'")
                chave = chave_alternativa
            else:
                logger.warning(f"   ❌ Nenhuma chave compatível encontrada em dados_gerais!")
                continue
        
        # Aplica o merge para adicionar novas colunas
        dados_gerais = aplicar_mapeamentos_com_merge(dados_gerais, df, chave, fillna_value=0)
        
        # Aplica as funções específicas para cada dimensão
        dados_gerais = aplicar_funcoes_dimensionais(dados_gerais, dimension)
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 Verificando colunas necessárias...")
    logger.info(f"{'='*60}")
    
    # Verifica colunas necessárias
    colunas_necessarias = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    colunas_faltando = [col for col in colunas_necessarias if col not in dados_gerais.columns]
    
    if colunas_faltando:
        logger.error(f"❌ ERRO: Colunas faltando: {colunas_faltando}")
        logger.error(f"   Colunas disponíveis: {dados_gerais.columns.tolist()}")
        return None
    
    logger.info(f"✅ Todas as colunas necessárias estão presentes")
    
    # Carrega pesos
    logger.info(f"\n{'='*60}")
    logger.info("⚖️ Carregando pesos...")
    logger.info(f"{'='*60}")
    
    pesos = {}
    if 'result' in config:
        for item in config['result']:
            if item.get('name') == 'ire_cs_eco' and 'depends_on' in item:
                for dep in item['depends_on']:
                    pesos[dep['name']] = dep.get('peso', 0)
    
    logger.info(f"   Pesos carregados: {pesos}")
    
    # Verifica se todos os pesos necessários existem
    for col in colunas_necessarias:
        if col not in pesos:
            logger.warning(f"   ⚠️ Peso para '{col}' não encontrado, usando 0.333...")
            pesos[col] = 1/3
    
    peso_ind = float(pesos['ire_cs_ind_eco'])
    peso_irri = float(pesos['ire_cs_irri_eco'])
    peso_pec = float(pesos['ire_cs_pec_eco'])
    
    logger.info(f"   Peso Indústria: {peso_ind:.4f}")
    logger.info(f"   Peso Irrigação: {peso_irri:.4f}")
    logger.info(f"   Peso Pecuária: {peso_pec:.4f}")
    
    # Converter colunas para numérico
    logger.info(f"\n{'='*60}")
    logger.info("🔄 Convertendo colunas para numérico...")
    logger.info(f"{'='*60}")
    
    for col in colunas_necessarias:
        # Substitui vírgula por ponto e converte para numérico
        dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
        dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
        
        # Verifica se há valores nulos após conversão
        nulos = dados_gerais[col].isna().sum()
        if nulos > 0:
            logger.warning(f"   ⚠️ {nulos} valores nulos encontrados em '{col}', preenchendo com 0")
            dados_gerais[col] = dados_gerais[col].fillna(0)
        
        logger.info(f"   ✅ '{col}' convertido com sucesso")
    
    # Aplicar função de cálculo do resultado final
    logger.info(f"\n{'='*60}")
    logger.info("🧮 Calculando IRE_CS_ECO...")
    logger.info(f"{'='*60}")
    
    # Verifica se a função ire_cs_eco existe
    if 'ire_cs_eco' in globals() and callable(globals()['ire_cs_eco']):
        try:
            dados_gerais['ire_cs_eco'] = dados_gerais.apply(
                lambda row: ire_cs_eco(
                    row['ire_cs_ind_eco'], peso_ind,
                    row['ire_cs_irri_eco'], peso_irri,
                    row['ire_cs_pec_eco'], peso_pec
                ), axis=1
            )
            logger.info(f"   ✅ IRE_CS_ECO calculado com sucesso")
            logger.info(f"   Estatísticas:")
            logger.info(f"      Mínimo: {dados_gerais['ire_cs_eco'].min():.4f}")
            logger.info(f"      Máximo: {dados_gerais['ire_cs_eco'].max():.4f}")
            logger.info(f"      Média:  {dados_gerais['ire_cs_eco'].mean():.4f}")
            logger.info(f"      Nulos:  {dados_gerais['ire_cs_eco'].isna().sum()}")
        except Exception as e:
            logger.error(f"   ❌ Erro ao calcular IRE_CS_ECO: {e}")
            return None
    else:
        logger.error("❌ Função 'ire_cs_eco' não encontrada!")
        return None
    
    # Seleciona colunas para o resultado final
    colunas_resultado = ['COBACIA', 'ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco', 'ire_cs_eco']
    
    # Verifica se 'COBACIA' existe, senão usa a chave disponível
    if 'COBACIA' not in dados_gerais.columns:
        # Tenta encontrar uma coluna de identificação
        for col in ['cod_mun', 'mun_nm', 'Município', 'cod_ibge']:
            if col in dados_gerais.columns:
                colunas_resultado[0] = col
                logger.info(f"   ℹ️ Usando '{col}' como identificador (COBACIA não encontrado)")
                break
    
    # Verifica se todas as colunas existem
    colunas_faltando_resultado = [col for col in colunas_resultado if col not in dados_gerais.columns]
    if colunas_faltando_resultado:
        logger.warning(f"⚠️ Colunas faltando no resultado: {colunas_faltando_resultado}")
        # Remove colunas faltando
        colunas_resultado = [col for col in colunas_resultado if col in dados_gerais.columns]
        logger.info(f"   Usando colunas disponíveis: {colunas_resultado}")
    
    dados_resultado = dados_gerais[colunas_resultado]
    
    # Salvar resultado
    logger.info(f"\n{'='*60}")
    logger.info("💾 Salvando resultados...")
    logger.info(f"{'='*60}")
    
    try:
        # Salva resultado final
        output_path = normalize_path(config['output']['path'])
        dados_resultado.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"✅ Resultado salvo em: {output_path}")
        
        # Salva dados intermediários atualizados
        interm_path = normalize_path(config['intermediario'])
        dados_gerais.to_csv(interm_path, index=False, encoding='utf-8')
        logger.info(f"✅ Dados intermediários salvos em: {interm_path}")
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar arquivos: {e}")
        return None
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 Resumo do resultado final:")
    logger.info(f"{'='*60}")
    logger.info(dados_resultado.head(10))
    logger.info(f"\nTotal de registros: {len(dados_resultado)}")
    logger.info(f"Colunas: {dados_resultado.columns.tolist()}")
    
    logger.info(f"\n✅ Processamento concluído com sucesso!")
    return dados_resultado

def get_user_input() -> str:
    """
    Obtém o caminho do arquivo YAML do usuário
    """
    print("\n" + "="*60)
    print("Sistema de Processamento ISH - Ecológico")
    print("="*60)
    
    # Detecta sistema operacional
    if sys.platform == 'win32':
        print("Sistema operacional: Windows")
        default_path = "C:\\Users\\Usuario\\Desktop\\ish_lunc\\functions_module_ish_eco\\parameters.yaml"
    else:
        print("Sistema operacional: Linux/Unix")
        default_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/parameters.yaml"
    
    print(f"\nCaminho padrão: {default_path}")
    user_input = input("\nDigite o caminho do arquivo YAML (ou Enter para usar o padrão): ").strip()
    
    if not user_input:
        return default_path
    return user_input

def main():
    """
    Função principal com tratamento de erros e configuração
    """
    try:
        # Configuração de logging
        logging.getLogger().setLevel(logging.INFO)
        
        # Pode usar caminho fixo ou solicitar ao usuário
        # yaml_path = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/parameters.yaml"
        
        # Ou solicitar ao usuário
        yaml_path = get_user_input()
        
        # Verifica se o arquivo existe
        if not Path(yaml_path).exists():
            logger.error(f"Arquivo não encontrado: {yaml_path}")
            logger.info(f"Diretório atual: {os.getcwd()}")
            sys.exit(1)
        
        # Executa a função principal
        result = functions_module_ish_eco(yaml_path)
        
        if result is not None:
            print(f"\n✅ Processamento concluído!")
            print(f"✅ {len(result)} registros processados")
            print(f"✅ Colunas: {result.columns.tolist()}")
        else:
            print("\n❌ Processamento falhou!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Processamento interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro não tratado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
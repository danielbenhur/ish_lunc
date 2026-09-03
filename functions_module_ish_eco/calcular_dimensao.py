import pandas as pd
import yaml
from convertion_functions import *

def aplicar_mapeamentos_com_merge(dados_gerais, df_novo, chave, fillna_value=0):
    """
    Aplica mapeamentos usando merge em vez de map.
    Mantém todas as cidades e trata novas cidades com fallback.
    """
    if chave not in dados_gerais.columns:
        # print(f"⚠️ Chave '{chave}' não encontrada em dados_gerais")
        # print(f"   Colunas disponíveis: {dados_gerais.columns.tolist()}")
        return dados_gerais
    
    if chave not in df_novo.columns:
        # print(f"⚠️ Chave '{chave}' não encontrada em df_novo")
        return dados_gerais
    
    # Remove duplicatas do novo DataFrame (mantém o primeiro valor)
    df_novo_unique = df_novo.drop_duplicates(subset=[chave], keep='first')
    
    # Seleciona apenas colunas que não existem em dados_gerais (exceto a chave)
    novas_colunas = [col for col in df_novo_unique.columns 
                     if col != chave and col not in dados_gerais.columns]
    
    if not novas_colunas:
        # print(f"   ℹ️ Nenhuma nova coluna para adicionar")
        return dados_gerais
    
    # print(f"📋 Adicionando {len(novas_colunas)} colunas: {novas_colunas[:5]}{'...' if len(novas_colunas) > 5 else ''}")
    
    # Verifica quantas cidades serão afetadas
    cidades_dados_gerais = set(dados_gerais[chave].dropna())
    cidades_df_novo = set(df_novo_unique[chave])
    cidades_faltando = cidades_dados_gerais - cidades_df_novo
    
    # if cidades_faltando:
        # print(f"📌 {len(cidades_faltando)} cidades não encontradas no arquivo fonte")
        # print(f"   Exemplos: {list(cidades_faltando)[:5]}")
    
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

def aplicar_funcoes_dimensionais(dados_gerais, dimension):
    """
    Aplica as funções específicas para cada dimensão
    """
    for item in dimension['indicadores']:
        nome_funcao = item['name']
        
        # Verifica se a função existe
        if nome_funcao in globals() and callable(globals()[nome_funcao]):
            funcao = globals()[nome_funcao]
            try:
                # Executa a função aplicando pesos se necessário
                if 'pesos' in item:
                    pesos = item['pesos']
                    resultado = funcao(dados_gerais, pesos=pesos)
                else:
                    resultado = funcao(dados_gerais)
                
                # Verifica se retornou algo
                if resultado is not None:
                    dados_gerais[nome_funcao] = resultado
                    # print(f"   ✅ Função '{nome_funcao}' aplicada com sucesso")
                # else:
                    # print(f"   ⚠️ Função '{nome_funcao}' retornou None!")
                    
            except Exception as e:
                print(f"   ❌ Erro ao executar '{nome_funcao}': {e}")
        # else:
            # print(f"   ❌ Função '{nome_funcao}' não encontrada no escopo global!")
    
    return dados_gerais

def functions_module_ish_eco(yaml_file_path):
    with open(yaml_file_path, 'r') as file:
        config = yaml.safe_load(file)
    
    dimensions = config['dimensions']
    
    # Carrega dados gerais
    dados_gerais = pd.read_csv(config['intermediario'], dtype='str')
    # # print(f"📊 dados_gerais carregado: {len(dados_gerais)} linhas, {len(dados_gerais.columns)} colunas")
    # # print(f"   Colunas: {dados_gerais.columns.tolist()}")
    
    # Lista de possíveis chaves (em ordem de preferência)
    CHAVES_POSSIVEIS = ['COBACIA', 'cod_mun', 'mun_nm', 'Município', 'cod_ibge']
    
    # Processar cada arquivo e aplicar as funções
    for idx, dimension in enumerate(dimensions, 1):
        # # print(f"\n{'='*60}")
        # # print(f"📁 Processando dimensão {idx}/{len(dimensions)}: {dimension.get('name', 'Sem nome')}")
        # # print(f"{'='*60}")
        
        df = pd.read_csv(dimension['path'], dtype='str')
        # # print(f"   Arquivo: {dimension['path']}")
        # # print(f"   Linhas: {len(df)}, Colunas: {len(df.columns)}")
        
        if dados_gerais.empty:
            dados_gerais = df
            # # print("   📌 Primeiro DataFrame carregado como base")
            continue
        
        # Encontra a chave no DataFrame atual
        chave = None
        for possible_key in CHAVES_POSSIVEIS:
            if possible_key in df.columns:
                chave = possible_key
                break
        
        if chave is None:
            # # print(f"   ⚠️ Nenhuma chave encontrada! Pulando este arquivo...")
            continue
        
        # # print(f"   🔑 Chave identificada: '{chave}'")
        
        # Remove linhas com valores nulos na chave
        df = df.dropna(subset=[chave])
        # # print(f"   📊 Após remover nulos: {len(df)} linhas")
        
        # Verifica se a chave existe em dados_gerais
        if chave not in dados_gerais.columns:
            # # print(f"   ⚠️ Chave '{chave}' não encontrada em dados_gerais")
            # # print(f"   Tentando encontrar chave alternativa em dados_gerais...")
            
            # Tenta encontrar uma chave alternativa
            chave_alternativa = None
            for key in CHAVES_POSSIVEIS:
                if key in dados_gerais.columns:
                    chave_alternativa = key
                    break
            
            if chave_alternativa:
                # # print(f"   🔄 Usando chave alternativa: '{chave_alternativa}'")
                chave = chave_alternativa
            else:
                # # print(f"   ❌ Nenhuma chave compatível encontrada em dados_gerais!")
                continue
        
        # Aplica o merge para adicionar novas colunas
        dados_gerais = aplicar_mapeamentos_com_merge(dados_gerais, df, chave, fillna_value=0)
        
        # Aplica as funções específicas para cada dimensão
        dados_gerais = aplicar_funcoes_dimensionais(dados_gerais, dimension)
    
    # # print(f"\n{'='*60}")
    # # print("📊 Verificando colunas necessárias...")
    # # print(f"{'='*60}")
    
    # Verifica colunas necessárias
    colunas_necessarias = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    colunas_faltando = [col for col in colunas_necessarias if col not in dados_gerais.columns]
    
    if colunas_faltando:
        # # print(f"❌ ERRO: Colunas faltando: {colunas_faltando}")
        # # print(f"   Colunas disponíveis: {dados_gerais.columns.tolist()}")
        return
    
    # print(f"✅ Todas as colunas necessárias estão presentes")
    
    # Carrega pesos
    # # print(f"\n{'='*60}")
    # # print("⚖️ Carregando pesos...")
    # # print(f"{'='*60}")
    
    pesos = {}
    for item in config['result']:
        if item['name'] == 'ire_cs_eco':
            for dep in item['depends_on']:
                pesos[dep['name']] = dep['peso']
    
    # # print(f"   Pesos carregados: {pesos}")
    
    peso_ind = float(pesos['ire_cs_ind_eco'])
    peso_irri = float(pesos['ire_cs_irri_eco'])
    peso_pec = float(pesos['ire_cs_pec_eco'])
    
    # # print(f"   Peso Indústria: {peso_ind}")
    # # print(f"   Peso Irrigação: {peso_irri}")
    # # print(f"   Peso Pecuária: {peso_pec}")
    
    # Converter colunas para numérico
    # # print(f"\n{'='*60}")
    # # print("🔄 Convertendo colunas para numérico...")
    # # print(f"{'='*60}")
    
    colunas_numericas = ['ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco']
    for col in colunas_numericas:
        # Substitui vírgula por ponto e converte para numérico
        dados_gerais[col] = dados_gerais[col].astype(str).str.replace(',', '.')
        dados_gerais[col] = pd.to_numeric(dados_gerais[col], errors='coerce')
        
        # Verifica se há valores nulos após conversão
        nulos = dados_gerais[col].isna().sum()
        if nulos > 0:
            # # print(f"   ⚠️ {nulos} valores nulos encontrados em '{col}', preenchendo com 0")
            dados_gerais[col] = dados_gerais[col].fillna(0)
        
        # # print(f"   ✅ '{col}' convertido com sucesso")
    
    # Aplicar função de cálculo do resultado final
    # # print(f"\n{'='*60}")
    # # print("🧮 Calculando IRE_CS_ECO...")
    # # print(f"{'='*60}")
    
    dados_gerais['ire_cs_eco'] = dados_gerais.apply(
        lambda row: ire_cs_eco(
            row['ire_cs_ind_eco'], peso_ind,
            row['ire_cs_irri_eco'], peso_irri,
            row['ire_cs_pec_eco'], peso_pec
        ), axis=1
    )
    
    # print(f"   ✅ IRE_CS_ECO calculado com sucesso")
    # # print(f"   Estatísticas:")
    # # print(f"      Mínimo: {dados_gerais['ire_cs_eco'].min():.4f}")
    # # print(f"      Máximo: {dados_gerais['ire_cs_eco'].max():.4f}")
    # # print(f"      Média:  {dados_gerais['ire_cs_eco'].mean():.4f}")
    # # print(f"      Nulos:  {dados_gerais['ire_cs_eco'].isna().sum()}")
    
    # Seleciona colunas para o resultado final
    colunas_resultado = ['COBACIA','ire_cs_ind_eco', 'ire_cs_irri_eco', 'ire_cs_pec_eco', 'ire_cs_eco']
    
    # Verifica se 'COBACIA' existe, senão usa a chave disponível
    if 'COBACIA' not in dados_gerais.columns:
        # Tenta encontrar uma coluna de identificação
        for col in ['cod_mun', 'mun_nm', 'Município', 'cod_ibge']:
            if col in dados_gerais.columns:
                colunas_resultado[0] = col
                # print(f"   ℹ️ Usando '{col}' como identificador (COBACIA não encontrado)")
                break
    
    dados_resultado = dados_gerais[colunas_resultado]
    
    # Salvar resultado
    # # print(f"\n{'='*60}")
    # # print("💾 Salvando resultados...")
    # print(f"{'='*60}")
    
    dados_resultado.to_csv(config['output']['path'], index=False)
    dados_gerais.to_csv(config['intermediario'], index=False)
    
    print(f"✅ Resultado salvo em: {config['output']['path']}")
    # # print(f"✅ Dados intermediários salvos em: {config['intermediario']}")
    # 
    # # print(f"\n{'='*60}")
    # # print("📊 Resumo do resultado final:")
    # # print(f"{'='*60}")
    # # print(dados_resultado.head(10))
    # # print(f"\nTotal de registros: {len(dados_resultado)}")
    # # print(f"Colunas: {dados_resultado.columns.tolist()}")
    # 
    # # print(f"\n✅ Processamento concluído com sucesso!")

if __name__ == "__main__":
    functions_module_ish_eco("/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/functions_module_ish_eco/parameters.yaml")
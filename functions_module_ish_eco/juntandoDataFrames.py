import pandas as pd

def main_with_map():
    files_names = [
        'arquivo_intermediario.csv',
        'PAM - ES - Producao irrigada .csv', 
        './Indicador Industria - Bernardo - Ind_sc_otto.csv',
        './PPM - ES - Pec_otto.csv'
    ]
    
    dados_gerais = None
    
    for file in files_names:
        print(f"\nProcessando: {file}")
        
        df = pd.read_csv(file, dtype='str', low_memory=False)
        
        # Identifica chave
        chave = None
        for possible_key in ['COBACIA', 'cod_mun']:
            if possible_key in df.columns:
                chave = possible_key
                break
        
        if chave is None:
            print(f"  ⚠️ Sem chave! Pulando...")
            continue
        
        print(f"  Chave: {chave}")
        print(f"  Linhas: {len(df)}")
        
        # Remove nulos
        df = df.dropna(subset=[chave])
        
        # Primeiro arquivo = BASE
        if dados_gerais is None:
            dados_gerais = df
            print(f"  ✅ BASE: {len(dados_gerais)} linhas")
            continue
        
        # 🔥 CRIA UM DICIONÁRIO DE MAPPING (chave -> primeiro valor)
        # Isso garante que cada chave tenha APENAS UM valor
        mapping = {}
        for col in df.columns:
            if col != chave:
                # Pega o primeiro valor para cada chave
                mapping[col] = df.drop_duplicates(subset=[chave], keep='first').set_index(chave)[col].to_dict()
        
        # Aplica o mapping à base (sem multiplicar!)
        for col in mapping:
            if col not in dados_gerais.columns:
                dados_gerais[col] = dados_gerais[chave].map(mapping[col])
                print(f"  Adicionada coluna: {col}")
        
        print(f"  BASE agora tem {len(dados_gerais)} linhas")
    
    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL:")
    print(f"Shape: {dados_gerais.shape}")
    print(f"Linhas: {len(dados_gerais)}")
    print(f"Colunas: {len(dados_gerais.columns)}")
    print(f"\n{dados_gerais.head()}")
    dados_gerais.to_csv('arquivo_geral.csv')

if __name__ == "__main__":
    main_with_map()
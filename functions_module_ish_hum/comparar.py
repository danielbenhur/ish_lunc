# comparar.py
import pandas as pd

# ============================================================
# CONFIGURAÇÃO
# ============================================================
ARQUIVO_NOVO = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/dados_gerais/arquivo_intermediario20-10.csv"
ARQUIVO_ANTIGO   = "/home/luca_profissional/Desktop/BolsaLabgest/ish_lunc/dados_gerais/hum_sc_otto2017_ISH-2035v0.0.15 - hum_sc_otto.csv"
ARQUIVO_DELTA  = "diferencas_percentuais.csv"   # saída espelho

CHAVES_CANDIDATAS = ["cobacia"]
AGREGACAO = "mean"     # "sum", "mean" ou "first"
TOLERANCIA = 0.0       # ex.: 0.01 ignora variações < 1%
DECIMAIS   = 4         # casas decimais no CSV de saída

# ============================================================
# LEITURA
# ============================================================
def limpar_chave(serie):
    s = serie.astype(str).str.strip()
    s = s.str.replace(r"\.0$", "", regex=True)
    s = s.replace({"nan": "", "None": "", "NaN": "", "<NA>": ""})
    return s

a = pd.read_csv(ARQUIVO_ANTIGO, dtype=str)
b = pd.read_csv(ARQUIVO_NOVO,   dtype=str)

chaves_usadas = [c for c in CHAVES_CANDIDATAS if c in a.columns and c in b.columns]
if not chaves_usadas:
    raise SystemExit("❌ Nenhuma chave em comum entre os arquivos.")

print(f"🔑 Chaves usadas: {chaves_usadas}\n")

for c in chaves_usadas:
    a[c] = limpar_chave(a[c])
    b[c] = limpar_chave(b[c])

a = a[(a[chaves_usadas] != "").any(axis=1)]
b = b[(b[chaves_usadas] != "").any(axis=1)]

# ============================================================
# PREPARA (numérico + agrega se houver duplicata)
# ============================================================
def preparar(df, chaves):
    df = df.copy()

    def _to_num(col):
        return pd.to_numeric(
            col.astype(str).str.strip().str.replace(",", ".", regex=False),
            errors="coerce"
        )

    for col in df.columns:
        if col not in chaves:
            df[col] = _to_num(df[col])

    n_dup = df.duplicated(subset=chaves).sum()
    if n_dup > 0:
        print(f"  ℹ️  {n_dup} linha(s) duplicada(s) — agregando com '{AGREGACAO}'")
        df = df.groupby(chaves, as_index=False).agg(AGREGACAO)

    return df

a_prep = preparar(a, chaves_usadas)
b_prep = preparar(b, chaves_usadas)

# ============================================================
# ALINHA OS DOIS
# ============================================================
colunas_comuns = sorted(
    (set(a_prep.columns) & set(b_prep.columns)) - set(chaves_usadas)
)

a_prep = a_prep.set_index(chaves_usadas)
b_prep = b_prep.set_index(chaves_usadas)

chaves_comuns = a_prep.index.intersection(b_prep.index)
a_num = a_prep.loc[chaves_comuns, colunas_comuns]
b_num = b_prep.loc[chaves_comuns, colunas_comuns]

print(f"Comparando {len(chaves_comuns)} chaves em {len(colunas_comuns)} colunas comuns.\n")

# ============================================================
# DELTA %
# ============================================================
denom = a_num.where(a_num != 0, b_num)
delta = (b_num - a_num) / denom * 100.0
delta = delta.where(a_num.notna() & b_num.notna())

if TOLERANCIA > 0:
    delta = delta.where(delta.abs() > TOLERANCIA * 100)

# ============================================================
# 🔥 MONTA SAÍDA LADO A LADO: a | b | delta% por coluna
# ============================================================
# Renomeia as colunas de a_num e b_num para sufixos _a e _b
a_out = a_num.add_suffix("_a")
b_out = b_num.add_suffix("_b")
d_out = delta.add_suffix("_delta_%")

# Junta tudo (chaves + a + b + delta intercalados)
saida = pd.concat([a_out, b_out, d_out], axis=1)

# Reordena para ficar: col_a, col_b, col_delta_% | col2_a, col2_b, col2_delta_% ...
ordem = []
for col in colunas_comuns:
    ordem.extend([f"{col}_a", f"{col}_b", f"{col}_delta_%"])
saida = saida[ordem]

saida = saida.round(DECIMAIS).reset_index()
saida.columns = chaves_usadas + ordem

saida.to_csv(ARQUIVO_DELTA, index=False)
print(f"💾 Delta % salvo em: {ARQUIVO_DELTA}")
print(f"   Formato: {saida.shape[0]} linhas × {saida.shape[1]} colunas "
      f"({len(chaves_usadas)} chave(s) + {len(colunas_comuns)} indicadores × 3)")

# ============================================================
# RESUMO POR COLUNA (só pra você ver rápido no terminal)
# ============================================================
print("\n" + "=" * 60)
print("RESUMO POR COLUNA (delta %)")
print("=" * 60)

resumo = []
for col in colunas_comuns:
    d = delta[col].dropna()
    if d.empty:
        continue
    resumo.append({
        "coluna":          col,
        "n_alterados":     int((d != 0).sum()),
        "n_total":         int(len(d)),
        "delta_medio_%":   d.mean(),
        "delta_abs_max_%": d.abs().max(),
    })

resumo_df = pd.DataFrame(resumo).sort_values("delta_abs_max_%", ascending=False)

if resumo_df.empty:
    print("✅ Nenhuma diferença numérica encontrada.")
else:
    with pd.option_context("display.float_format", lambda x: f"{x:,.4f}"):
        print(resumo_df.to_string(index=False))

print("\n✅ Pronto.")
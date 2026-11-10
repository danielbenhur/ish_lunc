# run_pipeline.py
"""
Pipeline unificado: motorCalculo -> joinISH
Executa, na ordem:
  1) calcula cada dimensão (scripts em functions_module_ish_<name>/calcular_dimensao.py)
  2) faz o join/consolidação e gera CSV + GPKG finais
Uso:
    python3 run_pipeline.py [--yaml parameters.yaml]
"""
import argparse
import os
import sys
import subprocess

import yaml

# Importa o joinISH como módulo (precisa estar no mesmo diretório ou no PYTHONPATH)
import joinISH


# ---------------------------------------------------------------------------
# Etapa 1: motorCalculo
# ---------------------------------------------------------------------------
def run_motor_calculo(config, python_exe=None):
    """Executa o calcular_dimensao.py de cada dimensão definida no YAML."""
    python_exe = python_exe or sys.executable  # usa o mesmo Python atual
    falhas = []

    for dimension in config["dimensions"]:
        name = dimension["name"]
        folder = f"functions_module_ish_{name}"
        script_path = os.path.join(folder, "calcular_dimensao.py")

        if not os.path.isdir(folder):
            print(f"[motorCalculo] ⚠️  pasta '{folder}' não existe — pulando '{name}'")
            falhas.append(name)
            continue

        if not os.path.isfile(script_path):
            print(f"[motorCalculo] ⚠️  '{script_path}' não encontrado — pulando '{name}'")
            falhas.append(name)
            continue

        print(f"[motorCalculo] ▶ executando {script_path}")
        try:
            subprocess.run([python_exe, script_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[motorCalculo] ❌ erro em {script_path}: {e}", file=sys.stderr)
            falhas.append(name)
        except Exception as e:
            print(f"[motorCalculo] ❌ erro inesperado em {script_path}: {e}", file=sys.stderr)
            falhas.append(name)

    return falhas


# ---------------------------------------------------------------------------
# Etapa 2: joinISH
# ---------------------------------------------------------------------------
def run_join_ish():
    """Chama o main() do joinISH (que usa o mesmo parameters.yaml)."""
    print("[joinISH] ▶ consolidando dimensões e gerando saída")
    joinISH.main()
    print("[joinISH] ✅ concluído")


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Pipeline motorCalculo + joinISH")
    parser.add_argument("--yaml", default="parameters.yaml", help="caminho do YAML de configuração")
    parser.add_argument("--skip-motor", action="store_true", help="pula a etapa motorCalculo")
    parser.add_argument("--skip-join", action="store_true", help="pula a etapa joinISH")
    args = parser.parse_args()

    if not os.path.isfile(args.yaml):
        print(f"❌ YAML não encontrado: {args.yaml}", file=sys.stderr)
        sys.exit(1)

    with open(args.yaml, "r") as f:
        config = yaml.safe_load(f)

    falhas = []
    if not args.skip_motor:
        print("=" * 60)
        print("ETAPA 1/2 — motorCalculo")
        print("=" * 60)
        falhas = run_motor_calculo(config)

    if not args.skip_join:
        print("=" * 60)
        print("ETAPA 2/2 — joinISH")
        print("=" * 60)
        run_join_ish()

    if falhas:
        print(f"\n⚠️  Dimensões com falha no motorCalculo: {falhas}")
        print("   O joinISH tentou rodar mesmo assim — confira se os CSVs de entrada existem.")
        sys.exit(2)

    print("\n🎉 Pipeline concluído sem erros.")


if __name__ == "__main__":
    main()
"""CadU no terminal. Rode dentro da pasta assistente/:  python main.py"""
import os
import sys

from assistente import Assistente
from base_conhecimento import BaseConhecimento

PASTA = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(PASTA, "data")


def main():
    # Console do Windows às vezes não usa UTF-8: força, para os acentos saírem certos.
    for fluxo in (sys.stdout, sys.stdin):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")

    base = BaseConhecimento(os.path.join(DATA, "base_conhecimento.json"))
    if not base.carregar():
        print(f"Não consegui abrir a base de conhecimento: {base.erro}")
        print("Confira o arquivo data/base_conhecimento.json e tente de novo.")
        return

    assistente = Assistente("CadU - assistente do CadÚnico", base,
                            caminho_historico=os.path.join(DATA, "historico.json"))
    try:
        assistente.menu(os.path.join(DATA, "atendimentos.csv"))
    except (KeyboardInterrupt, EOFError):
        print("\nAté logo!")


if __name__ == "__main__":
    main()

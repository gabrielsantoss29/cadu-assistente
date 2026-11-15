"""Testes automáticos do assistente.
Rode dentro de assistente/:  py -3.12 -m unittest discover testes"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

PASTA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # assistente/
sys.path.insert(0, PASTA)

from assistente import Assistente  # noqa: E402
from base_conhecimento import BaseConhecimento, normalizar  # noqa: E402

BASE_TESTE = os.path.join(PASTA, "testes", "base_teste.json")
BASE_REAL = os.path.join(PASTA, "data", "base_conhecimento.json")


def base_teste():
    b = BaseConhecimento(BASE_TESTE)
    assert b.carregar(), b.erro
    return b


def roteiro(*respostas):
    """Simula o teclado: cada chamada de input devolve a próxima resposta."""
    fila = list(respostas)
    return lambda _msg="": fila.pop(0)


class TestNormalizar(unittest.TestCase):
    def test_tira_acento_pontuacao_e_maiuscula(self):
        self.assertEqual(normalizar("  Cartão do SUS?! "), " cartao do sus ")

    def test_hifen_vira_espaco(self):
        self.assertEqual(normalizar("Pé-de-Meia"), " pe de meia ")


class TestBase(unittest.TestCase):
    def test_exemplo_do_enunciado_da_7_pontos(self):
        b = base_teste()
        cartao = b.orientacoes[0]
        # +3 "cartao do sus", +3 "sus", +1 "cartao" no título = 7
        self.assertEqual(b.pontuar("Como faço o cartão do SUS?", cartao), 7)

    def test_buscar_devolve_tuplas_ordenadas(self):
        r = base_teste().buscar("cartao do sus e bolsa")
        self.assertTrue(all(isinstance(t, tuple) and len(t) == 2 for t in r))
        pontos = [p for p, _ in r]
        self.assertEqual(pontos, sorted(pontos, reverse=True))

    def test_palavra_chave_nao_casa_dentro_de_outra(self):
        b = base_teste()
        self.assertEqual(b.pontuar("susto", b.orientacoes[0]), 0)

    def test_categorias_e_por_categoria(self):
        b = base_teste()
        self.assertEqual(b.categorias(), ["Saúde", "Teste"])
        self.assertEqual(len(b.por_categoria("Teste")), 2)

    def test_arquivo_ausente_nao_trava(self):
        b = BaseConhecimento("nao_existe.json")
        self.assertFalse(b.carregar())
        self.assertIn("não encontrado", b.erro)

    def test_json_corrompido_nao_trava(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "b.json")
            with open(p, "w", encoding="utf-8") as f:
                f.write("[{ quebrado")
            self.assertFalse(BaseConhecimento(p).carregar())

    def test_campo_faltando(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "b.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump([{"id": 1}], f)
            self.assertFalse(BaseConhecimento(p).carregar())

    def test_base_real_cumpre_minimos(self):
        b = BaseConhecimento(BASE_REAL)
        self.assertTrue(b.carregar(), b.erro)
        self.assertEqual(b.conferir_qualidade(), [])


class TestAnalisar(unittest.TestCase):
    def setUp(self):
        self.a = Assistente("teste", base_teste())

    def test_alta(self):
        r = self.a.analisar("Como faço o cartão do SUS?")
        self.assertEqual((r["tipo"], r["confianca"], r["pontos"]), ("encontrada", "ALTA", 7))

    def test_media_com_alternativa(self):
        r = self.a.analisar("quero uma bolsa")
        self.assertEqual(r["confianca"], "MÉDIA")
        self.assertEqual(len(r["alternativas"]), 1)    # a outra "bolsa"

    def test_nao_encontrei_indica_121_e_cras(self):
        r = self.a.analisar("como tiro passaporte")
        self.assertEqual(r["tipo"], "nao_encontrei")
        self.assertIn("121", r["mensagem"])
        self.assertIn("CRAS", r["mensagem"])

    def test_fora_do_escopo(self):
        self.assertEqual(self.a.analisar("me conta uma piada")["tipo"], "fora_escopo")

    def test_saudacao(self):
        self.assertEqual(self.a.analisar("Oi!")["tipo"], "saudacao")

    def test_dado_pessoal(self):
        for t in ["meu cpf é 123.456.789-00", "joao@email.com", "fone 11987654321"]:
            self.assertEqual(self.a.analisar(t)["tipo"], "dado_pessoal", t)
        self.assertNotEqual(self.a.analisar("sus 1234567")["tipo"], "dado_pessoal")

    def test_vazia_e_longa(self):
        self.assertEqual(self.a.analisar("   ")["tipo"], "vazia")
        self.assertEqual(self.a.analisar("a" * 301)["tipo"], "longa")


class TestTerminal(unittest.TestCase):
    def rodar(self, metodo, *teclas, historico=None):
        a = Assistente("teste", base_teste(), caminho_historico=historico, entrada=roteiro(*teclas))
        with redirect_stdout(io.StringIO()) as saida:
            getattr(a, metodo)()
        return a, saida.getvalue()

    def test_pergunta_que_ajudou(self):
        a, saida = self.rodar("perguntar", "cartao do sus", "talvez", "s", "0")
        self.assertIn("Responda s (sim) ou n (não)", saida)       # s/n inválido não trava
        self.assertIn("NÃO é um canal oficial", saida)
        self.assertEqual(len(a.historico), 1)
        h = a.historico[0]
        self.assertEqual((h["origem"], h["encontrou"], h["ajudou"], h["tentativas"]),
                         ("pergunta", True, True, 1))

    def test_duas_tentativas(self):
        a, _ = self.rodar("perguntar", "bolsa", "n", "cartao do sus", "s", "0")
        self.assertEqual(a.historico[0]["tentativas"], 2)

    def test_nao_ajudou_e_voltou(self):
        a, _ = self.rodar("perguntar", "bolsa", "n", "0")
        self.assertEqual((a.historico[0]["encontrou"], a.historico[0]["ajudou"]), (True, False))

    def test_dado_pessoal_nao_e_registrado(self):
        a, saida = self.rodar("perguntar", "meu cpf é 123.456.789-00", "a@b.com", "0")
        self.assertIn("não digite CPF", saida)
        self.assertEqual(a.historico, [])

    def test_navegar_com_opcoes_invalidas(self):
        a, saida = self.rodar("navegar", "x", "9", "", "1", "1", "s", "0", "0")
        self.assertIn("Opção inválida", saida)
        self.assertEqual(a.historico[0]["origem"], "categoria")

    def test_menu_completo_com_nota(self):
        with tempfile.TemporaryDirectory() as t:
            hist = os.path.join(t, "historico.json")
            csv_ = os.path.join(t, "atendimentos.csv")
            a = Assistente("teste", base_teste(), caminho_historico=hist,
                           entrada=roteiro("1", "cartao do sus", "s", "como tiro passaporte", "0",
                                           "3", "4", "abc", "0", "7", "4"))
            with redirect_stdout(io.StringIO()):
                a.menu(csv_)
            with open(hist, encoding="utf-8") as f:
                salvo = json.load(f)
            self.assertEqual(len(salvo), 2)
            self.assertEqual([s["facilidade"] for s in salvo], [4, 4])
            with open(csv_, encoding="utf-8-sig", newline="") as f:
                linhas = list(csv.DictReader(f, delimiter=";"))
            self.assertEqual(len(linhas), 2)

    def test_historico_corrompido_nao_trava(self):
        with tempfile.TemporaryDirectory() as t:
            hist = os.path.join(t, "historico.json")
            with open(hist, "w") as f:
                f.write("{{{")
            with redirect_stdout(io.StringIO()):
                a = Assistente("teste", base_teste(), caminho_historico=hist)
            self.assertEqual(a.historico, [])


class TestIndicadores(unittest.TestCase):
    def test_contas(self):
        a = Assistente("teste", base_teste())
        a.registrar("pergunta", "x", 3, True, True, 1, 2.0)
        a.registrar("pergunta", "y", 3, True, False, 3, 4.0)
        a.registrar("pergunta", "sem resposta", None, False, False, 1, 1.0)
        a.historico[0]["facilidade"] = 5
        a.historico[1]["facilidade"] = 3
        ind = a.indicadores()
        self.assertEqual(ind["total"], 3)
        self.assertEqual(ind["encontrada_pct"], 66.7)
        self.assertEqual(ind["ajudou_pct"], 33.3)
        self.assertEqual(ind["tempo_medio_s"], 3.0)
        self.assertEqual(ind["tentativas_media"], 1.7)
        self.assertEqual(ind["facilidade_media"], 4.0)
        self.assertEqual(ind["sem_solucao"], ["y", "sem resposta"])

    def test_csv_neutraliza_formula(self):
        a = Assistente("teste", base_teste())
        a.registrar("pergunta", "=1+1", None, False, False, 1, 0.5)
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "a.csv")
            a.exportar_csv(p)
            with open(p, encoding="utf-8-sig", newline="") as f:
                linha = next(csv.DictReader(f, delimiter=";"))
        self.assertEqual(linha["pergunta"], "'=1+1")


if __name__ == "__main__":
    unittest.main()

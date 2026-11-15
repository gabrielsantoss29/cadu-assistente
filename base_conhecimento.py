"""Classe BaseConhecimento: o conjunto de todas as orientações."""
import json

from orientacao import Orientacao

ACENTOS = {"á": "a", "à": "a", "ã": "a", "â": "a", "é": "e", "ê": "e",
           "í": "i", "ó": "o", "õ": "o", "ô": "o", "ú": "u", "ü": "u", "ç": "c"}
SINAIS = "?!.,;:()-/'\"" + "“”"   # pontuação que vira espaço


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem pontuação e com espaço nas pontas.
    Ex.: 'Cartão do SUS?' -> ' cartao do sus '.
    O espaço nas pontas faz ' sus ' não casar dentro de outra palavra."""
    texto = texto.lower().strip()
    for letra, troca in ACENTOS.items():
        texto = texto.replace(letra, troca)
    for sinal in SINAIS:
        texto = texto.replace(sinal, " ")
    return " " + " ".join(texto.split()) + " "


class BaseConhecimento:
    def __init__(self, caminho: str):
        self.caminho = caminho
        self.orientacoes = []          # lista de objetos Orientacao (composição)
        self.erro = ""                 # mensagem do último problema ao carregar

    def carregar(self) -> bool:
        """Lê o JSON e cria os objetos Orientacao.
        Devolve True se deu certo; se o arquivo faltar ou estiver quebrado,
        devolve False e guarda o motivo em self.erro (o programa não trava)."""
        try:
            with open(self.caminho, encoding="utf-8") as f:
                dados = json.load(f)
        except FileNotFoundError:
            self.erro = f"Arquivo não encontrado: {self.caminho}"
            return False
        except json.JSONDecodeError as e:
            self.erro = f"JSON corrompido ({e})"
            return False
        if not isinstance(dados, list):
            self.erro = "O JSON deve ser uma lista de orientações."
            return False
        try:
            self.orientacoes = [Orientacao(d) for d in dados]
        except (ValueError, TypeError) as e:
            self.erro = f"Registro inválido: {e}"
            self.orientacoes = []
            return False
        return True

    def categorias(self) -> list:
        """Categorias sem repetir, na ordem em que aparecem no JSON."""
        vistas = []
        for o in self.orientacoes:
            if o.categoria not in vistas:
                vistas.append(o.categoria)
        return vistas

    def por_categoria(self, categoria: str) -> list:
        return [o for o in self.orientacoes if o.categoria == categoria]

    def pontuar(self, pergunta: str, orientacao: Orientacao) -> int:
        """Regra de pontos:
        +3 para cada palavra-chave da orientação que aparece na pergunta;
        +1 para cada palavra da pergunta (4+ letras) que aparece no título."""
        p = normalizar(pergunta)
        pontos = 0
        for chave in orientacao.palavras_chave:
            if normalizar(chave) in p:
                pontos += 3
        titulo = normalizar(orientacao.titulo)
        for palavra in set(p.split()):          # set: palavra repetida conta 1 vez
            if len(palavra) >= 4 and f" {palavra} " in titulo:
                pontos += 1
        return pontos

    def buscar(self, pergunta: str) -> list:
        """Lista de tuplas (pontos, orientacao), da maior para a menor.
        Só entram orientações com pelo menos 1 ponto. Em empate, vale a ordem do JSON."""
        resultado = []
        for o in self.orientacoes:
            pontos = self.pontuar(pergunta, o)
            if pontos > 0:
                resultado.append((pontos, o))
        resultado.sort(key=lambda tupla: tupla[0], reverse=True)
        return resultado

    def conferir_qualidade(self) -> list:
        """Mínimos do enunciado. Lista vazia = base ok."""
        problemas = []
        if len(self.orientacoes) < 10:
            problemas.append(f"só {len(self.orientacoes)} orientações (mínimo 10)")
        if len(self.categorias()) < 3:
            problemas.append(f"só {len(self.categorias())} categorias (mínimo 3)")
        for o in self.orientacoes:
            if len(o.palavras_chave) < 3:
                problemas.append(f"orientação {o.id}: menos de 3 palavras-chave")
            if not str(o.fonte).startswith(("https://", "http://")):
                problemas.append(f"orientação {o.id}: fonte sem link")
        return problemas

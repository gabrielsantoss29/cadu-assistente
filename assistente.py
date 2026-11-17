"""Classe Assistente: quem conversa com a pessoa."""
import csv
import json
import time
from datetime import datetime

from base_conhecimento import BaseConhecimento, normalizar

LIMITE_ALTA = 6        # 6 pontos ou mais = confiança ALTA
LIMITE_MEDIA = 3       # 3 a 5 pontos = MÉDIA; menos de 3 = não encontrei
TAMANHO_MAXIMO = 300   # letras por pergunta

AVISO_DADOS = ("Atenção: não digite CPF, NIS, telefone, cartão nem e-mail. "
               "Eu não preciso desses dados. Reescreva sem eles.")
AVISO_LONGA = f"Sua pergunta ficou muito longa. Use até {TAMANHO_MAXIMO} letras."
AVISO_VAZIA = "Escreva sua dúvida, por favor."
TEXTO_FORA = ("Eu só ajudo com CadÚnico e benefícios sociais (Bolsa Família, "
              "Pé-de-Meia, Tarifa Social, BPC, Gás do Povo e outros).")
TEXTO_SAUDACAO = ("Oi, eu sou o CadU! Explico benefícios do CadÚnico, prazos e o que fazer. "
                  "Qual é a sua dúvida?")
TEXTO_NAO_ACHEI = ("Não encontrei uma orientação para isso e não vou inventar. "
                   "Tente outras palavras ou veja as categorias. "
                   "Para atendimento oficial, ligue 121 ou procure o CRAS da sua cidade.")

# Palavras que mostram assunto de fora (lista curta e simples)
PALAVRAS_FORA = {"futebol", "piada", "receita", "bolo", "filme", "musica", "novela",
                 "jogo", "namorado", "namorada", "horoscopo", "bitcoin", "eleicao",
                 "time", "celebridade", "clima", "carro", "programar"}
SAUDACOES = {" oi ", " ola ", " bom dia ", " boa tarde ", " boa noite ", " e ai "}

# Perguntas sobre o próprio CadU (frases-chave sem acento; vale se a frase aparece na pergunta)
SOBRE = [
    (("quem e voce", "quem e vc", "quem e o cadu", "quem e cadu", "quem eh voce", "voce e quem",
      "qual seu nome", "qual e o seu nome", "como voce se chama", "voce e um robo",
      "voce e uma pessoa", "voce e humano", "voce e real", "voce e uma ia"),
     "Eu sou o CadU, um assistente virtual que explica o CadÚnico e os benefícios sociais em "
     "linguagem simples: quem tem direito, o que levar, onde ir e como não cair em golpe. "
     "Não sou uma pessoa: respondo com orientações de fontes oficiais (gov.br). Pergunte, por exemplo, "
     "\"Como atualizo o CadÚnico?\"."),
    (("o que e o cadu", "o que e cadu", "o que e esse app", "o que e esse aplicativo", "o que e este app",
      "pra que serve o cadu", "para que serve o cadu", "que app e esse", "que aplicativo e esse"),
     "O CadU é um aplicativo de apoio para famílias do CadÚnico. Ele explica benefícios, prazos e "
     "documentos, ajuda a achar o CRAS mais perto no mapa e mostra como economizar na conta de luz. "
     "Ele não é um canal oficial do governo e não pede dados pessoais."),
    (("o que voce faz", "o que voce sabe", "o que voce pode", "como voce funciona", "como funciona o cadu",
      "como voce pode ajudar", "como pode me ajudar", "em que voce ajuda", "voce serve pra que",
      "pra que voce serve", "para que voce serve", "o que posso perguntar", "o que da pra perguntar"),
     "Eu respondo dúvidas sobre o CadÚnico e benefícios como Bolsa Família, Pé-de-Meia, Tarifa Social, "
     "BPC e Gás do Povo: quem pode receber, documentos, prazos e onde procurar atendimento. "
     "Escreva sua dúvida do seu jeito ou veja as categorias na aba Benefícios."),
    (("voce e oficial", "e do governo", "voce e do governo", "app oficial", "posso confiar no cadu", "o cadu e seguro"),
     "Não, o CadU não é um canal oficial do governo. Eu só reúno orientações de fontes oficiais, "
     "como o gov.br. Para atendimento oficial, ligue 121 ou procure o CRAS da sua cidade. "
     "Nunca passe senha ou código por mensagem."),
    (("guarda meus dados", "voce guarda", "privacidade", "voce pede dados", "coleta dados",
      "usa meus dados"),
     "Eu não peço nem guardo dados pessoais. Não digite CPF, NIS, telefone, e-mail nem cartão. "
     "Só uso contadores anônimos de uso, sem identificar ninguém."),
    (("quem criou", "quem fez", "quem desenvolveu", "quem te criou", "quem te fez", "quem e seu criador",
      "quem programou", "quem e o dono"),
     "Fui criado por estudantes de Ciência da Computação da FIAP como projeto da Global Solution "
     "2026 (CitizenTech), para ajudar famílias do CadÚnico a entender seus direitos."),
    (("obrigado", "obrigada", "valeu", "muito obrigado", "brigado"),
     "De nada! Se tiver mais alguma dúvida sobre o CadÚnico ou benefícios, é só perguntar."),
    (("tchau", "ate logo", "ate mais", "ate a proxima"),
     "Até mais! Quando precisar, é só chamar. Para atendimento oficial, ligue 121."),
]


class Assistente:
    def __init__(self, nome: str, base: BaseConhecimento, caminho_historico: str | None = None,
                 entrada=input):
        self.nome = nome
        self.base = base                      # composição: o assistente TEM uma base
        self.historico = []                   # lista de dicionários (um por atendimento)
        self.caminho_historico = caminho_historico   # None = não grava em disco (app web)
        self.entrada = entrada                # função de leitura (trocada nos testes)
        self._desta_sessao = []               # atendimentos feitos agora (para a nota)
        if caminho_historico:
            self._ler_historico()

    # ================= regras (sem input/print: o app web usa isto) =================
    @staticmethod
    def tem_dado_pessoal(texto: str) -> bool:
        """8 ou mais dígitos (CPF, NIS, telefone) ou '@' (e-mail)."""
        return "@" in texto or sum(c.isdigit() for c in texto) >= 8

    @staticmethod
    def responder_sobre(pergunta: str) -> str | None:
        """Responde perguntas sobre o próprio CadU (quem é, o que faz, se é oficial...)."""
        normal = " " + " ".join(normalizar(pergunta).replace("?", " ").replace("!", " ").split()) + " "
        for frases, texto in SOBRE:
            if any(f" {f} " in normal for f in frases):
                return texto
        return None

    def analisar(self, pergunta: str) -> dict:
        """Aplica as regras e devolve um dicionário com o resultado.
        tipo: vazia | longa | dado_pessoal | saudacao | fora_escopo | nao_encontrei | encontrada"""
        pergunta = (pergunta or "").strip()
        if not pergunta:
            return {"tipo": "vazia", "mensagem": AVISO_VAZIA}
        if len(pergunta) > TAMANHO_MAXIMO:
            return {"tipo": "longa", "mensagem": AVISO_LONGA}
        if self.tem_dado_pessoal(pergunta):
            return {"tipo": "dado_pessoal", "mensagem": AVISO_DADOS}

        resposta_sobre = self.responder_sobre(pergunta)
        if resposta_sobre:
            return {"tipo": "saudacao", "mensagem": resposta_sobre}

        resultados = self.base.buscar(pergunta)        # lista de tuplas (pontos, orientacao)
        if resultados and resultados[0][0] >= LIMITE_MEDIA:
            pontos, melhor = resultados[0]
            alternativas = [o for p, o in resultados[1:3] if p >= LIMITE_MEDIA]
            return {"tipo": "encontrada",
                    "confianca": "ALTA" if pontos >= LIMITE_ALTA else "MÉDIA",
                    "pontos": pontos, "orientacao": melhor, "alternativas": alternativas}

        normal = normalizar(pergunta)
        if normal in SAUDACOES:
            return {"tipo": "saudacao", "mensagem": TEXTO_SAUDACAO}
        if set(normal.split()) & PALAVRAS_FORA:
            return {"tipo": "fora_escopo", "mensagem": TEXTO_FORA}
        return {"tipo": "nao_encontrei", "mensagem": TEXTO_NAO_ACHEI,
                "categorias": self.base.categorias()}

    # ================= histórico =================
    def registrar(self, origem, pergunta, orientacao_id, encontrou, ajudou, tentativas, tempo):
        """Guarda um atendimento. NUNCA é chamado para pergunta com dado pessoal."""
        atendimento = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "origem": origem,                      # "pergunta" ou "categoria"
            "pergunta": pergunta,
            "orientacao_id": orientacao_id,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_s": tempo,
            "facilidade": None,                    # nota 1 a 5, pedida ao sair
        }
        self.historico.append(atendimento)
        self._desta_sessao.append(atendimento)
        self._salvar_historico()

    def _ler_historico(self):
        try:
            with open(self.caminho_historico, encoding="utf-8") as f:
                dados = json.load(f)
            self.historico = dados if isinstance(dados, list) else []
        except FileNotFoundError:
            self.historico = []
        except json.JSONDecodeError:
            print("Aviso: historico.json estava corrompido; começando um histórico novo.")
            self.historico = []

    def _salvar_historico(self):
        if not self.caminho_historico:
            return
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"Aviso: não consegui salvar o histórico ({e}).")

    # ================= indicadores e CSV =================
    def indicadores(self) -> dict:
        h = self.historico
        total = len(h)

        def media(valores):
            return round(sum(valores) / len(valores), 1) if valores else 0

        achados = [a for a in h if a["encontrou"]]
        notas = [a["facilidade"] for a in h if a.get("facilidade")]
        return {
            "total": total,
            "encontrada_pct": round(100 * len(achados) / total, 1) if total else 0,
            "ajudou_pct": round(100 * sum(1 for a in h if a["ajudou"]) / total, 1) if total else 0,
            "tempo_medio_s": media([a["tempo_s"] for a in achados]),
            "tentativas_media": media([a["tentativas"] for a in h]),
            "facilidade_media": media(notas),
            "sem_solucao": [a["pergunta"] for a in h if not a["ajudou"] and a["origem"] == "pergunta"],
        }

    def exportar_csv(self, caminho: str) -> int:
        """Exporta o histórico com csv.DictWriter. Devolve quantas linhas gravou."""
        campos = ["data", "origem", "pergunta", "orientacao_id", "encontrou",
                  "ajudou", "tentativas", "tempo_s", "facilidade"]
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:   # -sig: abre bem no Excel
            escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
            escritor.writeheader()
            for a in self.historico:
                linha = dict(a)
                # Evita fórmula maliciosa no Excel (texto que começa com = + - @)
                if str(linha["pergunta"])[:1] in ("=", "+", "-", "@"):
                    linha["pergunta"] = "'" + linha["pergunta"]
                escritor.writerow(linha)
        return len(self.historico)

    # ================= leitura segura do teclado =================
    def ler_opcao(self, mensagem: str, minimo: int, maximo: int) -> int:
        """Repete até a pessoa digitar um número entre minimo e maximo."""
        while True:
            texto = self.entrada(mensagem).strip()
            if texto.isdigit() and minimo <= int(texto) <= maximo:
                return int(texto)
            print(f"Opção inválida. Digite um número de {minimo} a {maximo}.")

    def ler_sim_nao(self, mensagem: str) -> bool:
        while True:
            texto = normalizar(self.entrada(mensagem)).strip()
            if texto in ("s", "sim"):
                return True
            if texto in ("n", "nao"):
                return False
            print("Responda s (sim) ou n (não).")

    # ================= telas do terminal =================
    def mostrar_encontrada(self, r: dict):
        print(f"\nConfiança da resposta: {r['confianca']} ({r['pontos']} pontos)\n")
        r["orientacao"].exibir()
        if r["alternativas"]:
            print("\nTalvez também ajude:")
            for o in r["alternativas"]:
                print(f"  - {o.titulo} [{o.categoria}]")
        print()

    def perguntar(self):
        """Pergunta em texto livre. Um atendimento termina quando a pessoa diz que
        ajudou, quando nada é encontrado ou quando ela volta com 0."""
        tentativas, inicio, pendente = 0, None, None
        while True:
            pergunta = self.entrada("\nDigite sua dúvida (0 para voltar): ").strip()
            if pergunta == "0":
                if pendente:   # tinha resposta que não ajudou: fecha o atendimento
                    self.registrar("pergunta", *pendente, False, tentativas,
                                   round(time.time() - inicio, 1))
                return
            r = self.analisar(pergunta)
            if r["tipo"] in ("vazia", "longa", "dado_pessoal", "saudacao"):
                print(r["mensagem"])          # não conta e não registra
                continue
            if inicio is None:
                inicio = time.time()
            tentativas += 1
            tempo = round(time.time() - inicio, 1)

            if r["tipo"] != "encontrada":     # nao_encontrei ou fora_escopo
                print(r["mensagem"])
                if r["tipo"] == "nao_encontrei":
                    print("Categorias: " + ", ".join(r["categorias"]))
                self.registrar("pergunta", pergunta, None, False, False, tentativas, tempo)
                tentativas, inicio, pendente = 0, None, None
                continue

            self.mostrar_encontrada(r)
            o = r["orientacao"]
            if self.ler_sim_nao("Essa orientação respondeu sua dúvida? (s/n): "):
                self.registrar("pergunta", pergunta, o.id, True, True, tentativas,
                               round(time.time() - inicio, 1))
                tentativas, inicio, pendente = 0, None, None
            else:
                print("Tente escrever de outro jeito, ou digite 0 para voltar.")
                pendente = (pergunta, o.id, True)

    def navegar(self):
        """Navegação por categorias numeradas, com 0 para voltar em todas as telas."""
        while True:
            cats = self.base.categorias()
            print("\nCATEGORIAS")
            for i, c in enumerate(cats, 1):
                print(f"  {i}. {c}")
            print("  0. Voltar")
            n = self.ler_opcao("Escolha: ", 0, len(cats))
            if n == 0:
                return
            inicio = time.time()
            while True:
                itens = self.base.por_categoria(cats[n - 1])
                print(f"\n{cats[n - 1].upper()}")
                for i, o in enumerate(itens, 1):
                    print(f"  {i}. {o.titulo}")
                print("  0. Voltar")
                k = self.ler_opcao("Escolha: ", 0, len(itens))
                if k == 0:
                    break
                o = itens[k - 1]
                print()
                o.exibir()
                ajudou = self.ler_sim_nao("\nEssa orientação respondeu sua dúvida? (s/n): ")
                self.registrar("categoria", o.titulo, o.id, True, ajudou, 1,
                               round(time.time() - inicio, 1))
                inicio = time.time()

    def mostrar_indicadores(self):
        ind = self.indicadores()
        print("\nINDICADORES")
        print(f"  Atendimentos: {ind['total']}")
        print(f"  Resposta encontrada: {ind['encontrada_pct']}%")
        print(f"  Taxa de acerto (ajudou): {ind['ajudou_pct']}%")
        print(f"  Tempo médio para encontrar: {ind['tempo_medio_s']} s")
        print(f"  Tentativas por atendimento: {ind['tentativas_media']}")
        print(f"  Facilidade de uso (1 a 5): {ind['facilidade_media']}")
        print("  Dúvidas sem solução:")
        for p in ind["sem_solucao"] or ["(nenhuma)"]:
            print(f"    - {p}")

    def pedir_nota(self):
        """Ao sair, pede a nota de facilidade e grava nos atendimentos desta sessão."""
        if not self._desta_sessao:
            return
        nota = self.ler_opcao("De 1 a 5, quão fácil foi usar o assistente? ", 1, 5)
        for a in self._desta_sessao:
            a["facilidade"] = nota
        self._salvar_historico()

    def menu(self, caminho_csv: str):
        print(f"\n=== {self.nome} ===")
        print("Tiro dúvidas sobre CadÚnico e benefícios. Não sou canal oficial")
        print("e nunca peço nome, CPF, telefone ou e-mail.")
        while True:
            print("\nMENU")
            print("  1. Fazer uma pergunta")
            print("  2. Ver por categoria")
            print("  3. Ver indicadores")
            print("  4. Exportar atendimentos (CSV)")
            print("  0. Sair")
            op = self.ler_opcao("Escolha: ", 0, 4)
            if op == 1:
                self.perguntar()
            elif op == 2:
                self.navegar()
            elif op == 3:
                self.mostrar_indicadores()
            elif op == 4:
                try:
                    n = self.exportar_csv(caminho_csv)
                    print(f"{n} atendimentos exportados para {caminho_csv}")
                except OSError as e:
                    print(f"Não consegui exportar ({e}).")
            else:
                self.pedir_nota()
                print("Até logo! Em caso de dúvida, ligue 121 ou procure o CRAS.")
                return

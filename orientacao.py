"""Classe Orientacao: uma informação da base (um registro do JSON)."""


class Orientacao:
    # Campos que o enunciado exige em todo registro do JSON.
    OBRIGATORIOS = ("id", "categoria", "titulo", "palavras_chave", "resposta",
                    "documentos", "onde", "fonte", "verificado_em")

    def __init__(self, dados: dict):
        """Recebe um dicionário do JSON. Se faltar campo, levanta ValueError."""
        faltando = [c for c in self.OBRIGATORIOS if c not in dados]
        if faltando:
            raise ValueError(f"registro {dados.get('id', '?')} sem: {', '.join(faltando)}")
        if not isinstance(dados["palavras_chave"], list) or not isinstance(dados["documentos"], list):
            raise ValueError(f"registro {dados['id']}: palavras_chave e documentos devem ser listas")

        # Atributos obrigatórios
        self.id = dados["id"]
        self.categoria = dados["categoria"]
        self.titulo = dados["titulo"]
        self.palavras_chave = dados["palavras_chave"]
        self.resposta = dados["resposta"]
        self.documentos = dados["documentos"]
        self.onde = dados["onde"]
        self.fonte = dados["fonte"]
        self.verificado_em = dados["verificado_em"]

        # Atributos extras do CadU (opcionais no JSON)
        self.fonte_nome = dados.get("fonte_nome", "")
        self.quem_pode = dados.get("quem_pode", "")
        self.como_pedir = dados.get("como_pedir", "")
        self.renovacao = dados.get("renovacao", "")
        self.se_bloquear = dados.get("se_acabar_ou_bloquear", "")
        self.conferido_por_humano = dados.get("conferido_por_humano", False)
        self.codigo = dados.get("codigo", str(self.id))     # nome curto usado pelo app
        self.pode_combinar = dados.get("pode_combinar", [])  # códigos que podem ser recebidos juntos

    def texto(self) -> str:
        """Monta o texto da orientação (usado no terminal e no app)."""
        linhas = [f">> {self.titulo}  [{self.categoria}]", self.resposta]
        if self.quem_pode:
            linhas.append(f"Quem pode: {self.quem_pode}")
        if self.como_pedir:
            linhas.append(f"Como pedir: {self.como_pedir}")
        if self.documentos:
            linhas.append("Documentos necessários:")
            linhas += [f"  - {d}" for d in self.documentos]
        linhas.append(f"Onde: {self.onde}")
        if self.renovacao:
            linhas.append(f"Prazo/renovação: {self.renovacao}")
        if self.se_bloquear:
            linhas.append(f"Se bloquear ou acabar: {self.se_bloquear}")
        linhas.append(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        if not self.conferido_por_humano:
            linhas.append("(Rascunho: esta informação ainda não foi conferida pela equipe.)")
        linhas.append("Aviso: este assistente NÃO é um canal oficial.")
        return "\n".join(linhas)

    def exibir(self) -> None:
        """Mostra a orientação na tela."""
        print(self.texto())

    def para_dict(self) -> dict:
        """Versão em dicionário, para o app web devolver em JSON."""
        return {
            "id": self.id, "codigo": self.codigo, "pode_combinar": self.pode_combinar,
            "categoria": self.categoria, "titulo": self.titulo,
            "resposta": self.resposta, "quem_pode": self.quem_pode,
            "como_pedir": self.como_pedir, "documentos": self.documentos,
            "onde": self.onde, "renovacao": self.renovacao, "se_bloquear": self.se_bloquear,
            "fonte": self.fonte, "fonte_nome": self.fonte_nome,
            "verificado_em": self.verificado_em, "conferido_por_humano": self.conferido_por_humano,
        }

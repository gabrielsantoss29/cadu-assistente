# CadU: assistente de terminal (PCP)

Assistente **por regras** (sem IA generativa) que tira dúvidas sobre o CadÚnico e benefícios sociais. Responde só com o que está em `data/base_conhecimento.json`, sempre com fonte oficial, data de verificação e o aviso de que **não é canal oficial**. Quando não encontra, diz que não sabe e indica o **121** e o **CRAS**.

O mesmo assistente roda também no app web do CadU (https://cadu-app.vercel.app), que importa estas mesmas classes, sem código duplicado.

## Integrantes

- Gabriel de Almeida Santos, RM 569395
- Guilherme Henrique Garbelini Alberto, RM 571150
- Herbert Soares de Jesus, RM 571507

## Público e problema

Famílias de baixa renda inscritas no CadÚnico (ou que querem entrar). A informação sobre benefícios existe, mas está espalhada e em linguagem técnica; muita gente perde benefício por não atualizar o cadastro ou não saber o que fazer quando ele bloqueia.

## ODS relacionados

- ODS 1 (Erradicação da pobreza)
- ODS 10 (Redução das desigualdades)
- ODS 16 (Instituições eficazes: acesso à informação)

## Como executar

Precisa de Python 3.10 ou mais novo. Não usa bibliotecas externas.

```bash
cd assistente
python main.py
```

No Windows, se `python` não existir, use `py -3.12 main.py`.

Testes automáticos (dentro de `assistente/`):

```bash
py -3.12 -m unittest discover testes
```

## Arquivos

- `main.py`: cria a base e o assistente e abre o menu.
- `orientacao.py`: classe `Orientacao` (um registro do JSON). Método `exibir()`.
- `base_conhecimento.py`: classe `BaseConhecimento` e a função `normalizar()`. Métodos `carregar()`, `categorias()`, `por_categoria()`, `pontuar()`, `buscar()`.
- `assistente.py`: classe `Assistente`. Métodos `perguntar()`, `navegar()`, `registrar()`, `indicadores()`, `exportar_csv()`, além de `analisar()` (as regras, sem tela, usada também pelo app web).
- `data/base_conhecimento.json`: a base. `data/historico.json` e `data/atendimentos.csv` são criados ao usar.

Composição: `Assistente` tem uma `BaseConhecimento`, que tem uma lista de objetos `Orientacao`.

## Regra de pontuação

Pergunta, palavras-chave e título são comparados depois de `normalizar()` (minúsculas, sem acento, sem pontuação; hífen vira espaço, então "Pé-de-Meia" = "pe de meia").

- +3 para cada palavra-chave da orientação que aparece na pergunta (como palavra inteira: "sus" não casa dentro de "susto");
- +1 para cada palavra da pergunta com 4 ou mais letras que aparece no título (palavra repetida conta uma vez).

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` da maior para a menor (empate: vale a ordem do JSON). O assistente mostra a melhor e até 2 alternativas com 3 pontos ou mais.

- 6 pontos ou mais: confiança **ALTA**;
- 3 a 5: **MÉDIA**;
- menos de 3: "Não encontrei" + sugestão de outras palavras, lista de categorias, 121 e CRAS.

Exemplo do enunciado (testado em `testes/`): "Como faço o cartão do SUS?" = +3 `cartao do sus` +3 `sus` +1 `cartao` no título = 7, ALTA.

Respostas extras (quando não há orientação): saudação ("oi") ganha apresentação; assunto de fora (futebol, piada...) ganha "só ajudo com CadÚnico e benefícios".

## Regras de atendimento

- Menu e categorias numerados, com **0 para voltar** em todas as telas.
- Opção fora da faixa, letras, resposta vazia ou s/n inválido: o programa avisa e pergunta de novo.
- Pergunta com **8 ou mais dígitos** ou com **@** é recusada e **não é registrada**. Pergunta com mais de 300 letras também é recusada.
- `base_conhecimento.json` ausente ou corrompido: mostra o motivo e fecha sem erro. `historico.json` corrompido: avisa e começa um histórico novo.

## Histórico, indicadores e CSV

Cada atendimento vai para `data/historico.json` com: `data`, `origem` (pergunta ou categoria), `pergunta`, `orientacao_id`, `encontrou`, `ajudou`, `tentativas`, `tempo_s` e `facilidade`.

Um atendimento por pergunta termina quando a pessoa responde "s" (ajudou), quando nada é encontrado, ou quando ela digita 0 depois de um "n". Cada nova pergunta depois de um "n" conta mais uma tentativa. O tempo é medido com `time.time()` desde a primeira pergunta do atendimento. Ao sair, o assistente pede uma nota de facilidade (1 a 5) e grava nos atendimentos daquela sessão.

Indicadores (menu 3): resposta encontrada (%), taxa de acerto: ajudou (%), tempo médio para encontrar, tentativas por atendimento, facilidade média e lista de dúvidas sem solução.

Exportação (menu 4): `data/atendimentos.csv` com `csv.DictWriter` (separador `;`, abre direto no Excel).

## Base de conhecimento

Formato do enunciado (lista de dicionários). Obrigatórios: `id`, `categoria`, `titulo`, `palavras_chave`, `resposta`, `documentos`, `onde`, `fonte`, `verificado_em`. Extras do CadU: `codigo`, `fonte_nome`, `quem_pode`, `como_pedir`, `renovacao`, `se_acabar_ou_bloquear`, `status_verificacao`, `conferido_por_humano`.

A base é gerada a partir da pesquisa em `dados/rascunho/beneficios.json`:

```bash
py -3.12 ferramentas/importar_base.py
```

(rodar na raiz do repositório). Fichas `nao_verificado` ficam de fora. Enquanto `conferido_por_humano` for `false`, a resposta mostra "Rascunho: ainda não conferida".

## Integração com outras disciplinas

O app web do CadU (`app/`) importa estas classes e usa `Assistente.analisar()` no chat. (completar com DSA e CS quando estiverem prontos)

## Fontes consultadas

Todas as fontes estão no campo `fonte` de cada orientação (gov.br/MDS, ANEEL, INSS, MEC, Capes, Planalto).

## Teste com usuários

(preencher depois do teste com 3 pessoas de fora da equipe e 10+ atendimentos: indicadores do menu 3, dúvidas sem solução e uma melhoria feita, por exemplo uma palavra-chave nova)

## Limitações

- Só entende palavras que estão na base: sinônimos e erros de digitação não previstos não são encontrados.
- A informação muda (valores, datas); a base precisa ser conferida de tempos em tempos.
- Não consulta a situação da pessoa (isso é feito no app oficial do Cadastro Único, no 121 ou no CRAS).

## Vídeo

(link do YouTube, não listado)

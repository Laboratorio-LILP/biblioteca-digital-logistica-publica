"""
Coleções v6 (canônicas, §7) com o vocabulário de Tipos de Informação da
taxonomia v12 (set/2026) e o de-para de grafias legadas.

As 4 Coleções são definidas pelo *Tipo de Informação*. Os mapas abaixo:
  - COLECOES_V6 / _TIPOS_POR_COLECAO: vocabulário EXATO v12 (e-mail "ALTERAÇÕES
    BIBLIOTECA", Lina, 11/09/2026): Jurisprudência = Súmulas, Boletins, Acórdãos,
    Deliberações; Doutrina ganha Enunciados; Instrução perde Vídeos. "Pareceres"
    entrou em 11/09 e saiu em 23/09/2026 (v12.1 — procurador consultado pela
    chefia: não é doutrina nem jurisprudência).
  - TIPO_V5_TO_V6: normaliza grafias legadas (singular, sem acento, nomes do
    acervo v5) para o tipo canônico — usado pelo front (colecao_v6_for_tipo) e
    pelo importador (tipo_canonico).
  - TIPOS_LEGADOS: tipos RETIRADOS do vocabulário (Documentos Normativos, Vídeos,
    Pareceres)
    → coleção em que ainda devem ser EXIBIDOS enquanto documentos antigos os
    referenciarem (janela entre a subida do código e a recarga v12). Só
    colecao_v6_for_tipo usa; o importador recusa esses tipos.
Os de-para de Categoria/Assunto v5→v6 foram removidos: a migração v8 lê esses
campos diretamente da planilha (ver migrate_spreadsheet.py).
"""

import unicodedata


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()


# 4 coleções v6 — identidade visual (ícone Feather + classe de cor) e descrição
# curta em Linguagem Simples (usada na aba Curadoria e nos cards de coleção).
COLECOES_V6 = [
    {"nome": "Jurisprudência", "slug": "jurisprudencia", "icon": "fi-shield", "color": "c-petrol",
     "descricao": "Acórdãos, deliberações, súmulas e boletins de tribunais que orientam como aplicar a lei."},
    {"nome": "Trabalhos Acadêmicos", "slug": "trabalhos-academicos", "icon": "fi-graduation-cap", "color": "c-blue",
     "descricao": "Teses, dissertações, monografias e TCCs produzidos em universidades."},
    {"nome": "Doutrina e Conteúdo Técnico", "slug": "doutrina", "icon": "fi-book-open", "color": "c-red",
     "descricao": "Livros, artigos, relatórios, notas técnicas e enunciados que analisam e "
                  "explicam o tema."},
    {"nome": "Instrução e Capacitação", "slug": "instrucao", "icon": "fi-file-text", "color": "c-yellow",
     "descricao": "Manuais, guias, cursos e materiais para aprender na prática."},
]
COLECOES_BY_NOME = {c["nome"]: c for c in COLECOES_V6}
COLECOES_BY_SLUG = {c["slug"]: c for c in COLECOES_V6}

# Temas em destaque — buscas temáticas que NÃO são coleções formais (não se
# encaixam na taxonomia v6 por Tipo de Informação). Fonte única para os dois
# usos na Home: os cards de atalho em "Explorar o acervo" e os blocos de
# "Temas em Alta". `tema_busca` (facets.py) define o filtro do tema — por
# Assunto curado (`assunto_nome`, quando existe no banco) ou busca full-text
# (`query`). O MESMO filtro alimenta o link "Ver tema", a contagem do card e os
# documentos de preview dos "Temas em Alta", então tudo bate com o que o usuário
# vê ao clicar. Descrições em Linguagem Simples (público: comprador público —
# termos do campo são mantidos de propósito).
TEMAS_DESTAQUE = [
    {
        "slug": "lei-14133",
        "label": "Lei 14.133/21",
        "query": "14.133",
        "icon": "fi-scale",
        "color": "c-petrol",
        "card_desc": "A nova Lei de Licitações e Contratos: o que muda nas regras, "
                     "prazos e modalidades das compras públicas.",
        "alta_intro": "Materiais selecionados para entender e aplicar a nova Lei de "
                      "Licitações e Contratos (Lei 14.133/21) nas contratações públicas.",
    },
    {
        "slug": "sustentabilidade",
        "label": "Sustentabilidade e ODS",
        "query": "Sustentabilidade",
        # Tem Assunto curado correspondente: a busca do card/tema filtra por Assunto
        # (contagem bate com a faceta lateral e com a lista ao clicar), em vez de texto.
        "assunto_nome": "Sustentabilidade e ODS",
        "icon": "fi-leaf",
        "color": "c-green",
        "card_desc": "Compras públicas que protegem o meio ambiente e seguem os "
                     "Objetivos de Desenvolvimento Sustentável (ODS).",
        "alta_intro": "Materiais indicados para apoiar compras públicas sustentáveis, "
                      "desenvolvimento responsável e inovação aplicada à cadeia de suprimentos.",
    },
    {
        "slug": "compras-diretas",
        "label": "Compras Diretas",
        "query": "Compras Diretas",
        "icon": "fi-package",
        "color": "c-red",
        "card_desc": "Compras sem licitação — dispensa e inexigibilidade: "
                     "quando cabem e quais os limites.",
        "alta_intro": "Materiais para entender quando e como contratar sem "
                      "licitação — por dispensa ou inexigibilidade — dentro dos "
                      "limites e cuidados da Lei 14.133/21.",
    },
    {
        "slug": "pregao",
        "label": "Pregão",
        "query": "Pregão",
        "icon": "fi-trending-up",
        "color": "c-blue",
        "card_desc": "A modalidade para comprar bens e serviços comuns pelo "
                     "menor preço.",
        "alta_intro": "Materiais sobre o pregão: a modalidade usada para comprar "
                      "bens e serviços comuns pelo menor preço, em geral na forma "
                      "eletrônica.",
    },
    {
        "slug": "registro-precos",
        "label": "Registro de Preços",
        "query": "Registro de Preços",
        "icon": "fi-bookmark",
        "color": "c-yellow",
        "card_desc": "O Sistema de Registro de Preços (SRP): registrar preços "
                     "para contratar quando precisar.",
        "alta_intro": "Materiais sobre o Sistema de Registro de Preços (SRP) e a "
                      "ata: registrar preços para contratar aos poucos, conforme "
                      "a necessidade.",
    },
]

# Tipos de Informação EXATOS por coleção — vocabulário v12.1 (11/09/2026;
# Pareceres retirado em 23/09/2026).
_TIPOS_POR_COLECAO = {
    "Jurisprudência": ["Súmulas", "Boletins", "Acórdãos", "Deliberações"],
    "Trabalhos Acadêmicos": ["Teses", "Dissertações", "Monografias", "TCCs", "Memoriais Docentes"],
    "Doutrina e Conteúdo Técnico": [
        "Livros digitais", "Artigos", "Notas Técnicas", "Relatórios",
        "Textos de Discussão", "Resumos", "Resumos expandidos", "Enunciados",
    ],
    "Instrução e Capacitação": [
        "Manuais", "Guias", "Tutoriais", "Apostilas", "Aulas", "Cursos", "Slides",
    ],
}

# nome-normalizado do tipo → coleção; e nome-normalizado → grafia canônica
TIPO_TO_COLECAO = {}
_TIPO_CANONICO_POR_NORM = {}
for _col, _tipos in _TIPOS_POR_COLECAO.items():
    for _t in _tipos:
        TIPO_TO_COLECAO[_norm(_t)] = _col
        _TIPO_CANONICO_POR_NORM[_norm(_t)] = _t

_FALLBACK = "Doutrina e Conteúdo Técnico"

# Tipos retirados do vocabulário na v12 (e Pareceres na v12.1, 23/09/2026),
# ainda exibidos na coleção antiga
# enquanto houver documento carregado com eles (só colecao_v6_for_tipo usa).
TIPOS_LEGADOS = {
    "Documentos Normativos": "Jurisprudência",
    "Vídeos": "Instrução e Capacitação",
    "Pareceres": "Doutrina e Conteúdo Técnico",
}
_TIPOS_LEGADOS_NORM = {_norm(k): v for k, v in TIPOS_LEGADOS.items()}
_TIPOS_LEGADOS_NORM.update({
    "documento normativo": "Jurisprudência",
    "video": "Instrução e Capacitação",
    "parecer": "Doutrina e Conteúdo Técnico",
})

# Normalização de tipos do acervo v5 → tipo canônico v6.
# Chaves = valores REAIS da coluna "Tipo de informação" do v5 (normalizados).
TIPO_V5_TO_V6 = {
    # Doutrina e Conteúdo Técnico
    "artigo de periodico": "Artigos",
    "artigo de evento": "Artigos",
    "artigos de periodicos": "Artigos",
    "artigos": "Artigos",
    "pagina web": "Artigos",            # conteúdo on-line → Artigos (sem tipo web na v6)
    "relatorio": "Relatórios",
    "relatorios": "Relatórios",
    "nota tecnica": "Notas Técnicas",
    "notas tecnicas": "Notas Técnicas",
    "policy brief": "Notas Técnicas",
    "white paper": "Notas Técnicas",
    "livro": "Livros digitais",
    "livros": "Livros digitais",
    "livros digitais": "Livros digitais",
    "livro no todo": "Livros digitais",
    "capitulo de livro": "Livros digitais",
    "publicacao digital": "Livros digitais",
    "e-books": "Livros digitais",
    "textos de discussao": "Textos de Discussão",
    "estudo de caso": "Textos de Discussão",
    "resumos": "Resumos",
    "resumo": "Resumos",
    "resumos expandidos": "Resumos expandidos",
    "apresentacao de evento": "Resumos expandidos",
    "resumo expandido de evento": "Resumos expandidos",
    # Trabalhos Acadêmicos
    "dissertacao": "Dissertações",
    "dissertacoes": "Dissertações",
    "tese": "Teses",
    "teses": "Teses",
    "tcc": "TCCs",
    "tccs": "TCCs",
    "monografia": "Monografias",
    "monografia de especializacao": "Monografias",
    "monografias": "Monografias",
    "memoriais docentes": "Memoriais Docentes",
    # Instrução e Capacitação
    "material pedagogico": "Apostilas",
    "apostila": "Apostilas",
    "apostilas": "Apostilas",
    "manuais": "Manuais",
    "manual": "Manuais",
    "guias": "Guias",
    "guia": "Guias",
    "guia pratico": "Guias",
    "tutoriais": "Tutoriais",
    "aulas": "Aulas",
    "aula": "Aulas",
    "cursos": "Cursos",
    "curso": "Cursos",
    "apresentacoes": "Slides",
    "slides": "Slides",
    # Jurisprudência (v12: Acórdãos e Deliberações entram; Enunciados vai p/ Doutrina)
    "sumula": "Súmulas",
    "sumulas": "Súmulas",
    "boletim": "Boletins",
    "boletins": "Boletins",
    "acordao": "Acórdãos",
    "acordaos": "Acórdãos",
    "deliberacao": "Deliberações",
    "deliberacoes": "Deliberações",
    # Doutrina e Conteúdo Técnico (v12)
    "enunciado": "Enunciados",
    "enunciados": "Enunciados",
}


def tipo_retirado(type_name):
    """True para os tipos RETIRADOS do vocabulário na v12 (Documentos Normativos,
    Vídeos, e grafias legadas) — o importador os recusa mesmo com --allow-new-types."""
    return _norm(type_name) in _TIPOS_LEGADOS_NORM


def tipo_canonico(type_name):
    """Grafia canônica v12 de um Tipo de Informação, ou None se fora do vocabulário.

    Aceita as grafias legadas de TIPO_V5_TO_V6 (singular, sem acento, nomes v5)
    e devolve o nome EXATO do vocabulário. É o critério do importador estrito:
    tipos retirados (Documentos Normativos, Vídeos) e tipos desconhecidos → None.
    """
    key = _norm(type_name)
    if not key:
        return None
    v6 = TIPO_V5_TO_V6.get(key)
    lookup = _norm(v6) if v6 else key
    return _TIPO_CANONICO_POR_NORM.get(lookup)


def colecao_v6_for_tipo(type_name):
    """Coleção v6 (dict) para um nome de Tipo de Informação (v5, v8 ou v12).

    Tipos retirados na v12 (TIPOS_LEGADOS) continuam exibidos na coleção antiga
    — um documento carregado antes da recarga não pode "cair" em Doutrina.
    """
    key = _norm(type_name)
    # normaliza grafia legada → canônica antes de buscar a coleção
    v6 = TIPO_V5_TO_V6.get(key)
    lookup = _norm(v6) if v6 else key
    nome = TIPO_TO_COLECAO.get(lookup) or _TIPOS_LEGADOS_NORM.get(lookup) or _FALLBACK
    return COLECOES_BY_NOME[nome]


def tipos_de_colecao(slug_or_nome):
    """Tipos de Informação v6 que compõem uma coleção (para o filtro colecao_v6)."""
    col = COLECOES_BY_SLUG.get(slug_or_nome) or COLECOES_BY_NOME.get(slug_or_nome)
    if not col:
        return []
    return list(_TIPOS_POR_COLECAO.get(col["nome"], []))


# ---------------------------------------------------------------------------
# Descrições dos Assuntos — TEXTO DA CURADORIA (Lina Nakata, 11/09/2026,
# Caracterizacao_Assuntos_Taxonomia_BDLP.xlsx; tabela no Teams). Chave = nome
# canônico do seed (06-taxonomia.sql); "curta" = Caracterização (uma frase),
# "longa" = Explicação (um parágrafo), copiadas verbatim — só erros de
# digitação evidentes corrigidos ("melhoriua", "públicos..", espaço duplo,
# ponto final). Regra: texto da curadoria; mudanças vêm dela, não do código.
# Vive aqui, e não em nr_assunto, porque a tabela não tem coluna de descrição,
# o portal é somente leitura e não há migrations Django — mesmo padrão de
# COLECOES_V6["descricao"]. A "página de metodologia" (Eduardo) consumirá o
# mesmo dado. Exposto ao front por descricao_assunto(), facets.assuntos_glossario()
# e pelos filtros assunto_curta/assunto_longa (catalog_tags).
# ---------------------------------------------------------------------------
ASSUNTOS_DESCRICAO = {
    "Aspectos Jurídicos e Regulatórios": {
        "curta": "Sobre a base normativa e legal das contratações públicas.",
        "longa": "Reúne publicações sobre a legislação aplicável às compras públicas, com destaque para a "
                 "Lei nº 14.133/2021, pareceres jurídicos e interpretações normativas. Quando o foco for "
                 "como o assunto é tratado na norma.",
    },
    "Governança": {
        "curta": "Estruturas, princípios e práticas de gestão pública.",
        "longa": "Implementação de mecanismos e instrumentos que permitam planejar, executar e monitorar as "
                 "contratações. Abrange modelos de governança aplicados à logística e às contratações, "
                 "incluindo definição de papéis, tomada de decisão, accountability e alinhamento estratégico "
                 "das compras aos objetivos institucionais. Estrutura de gestão como um todo.",
    },
    "Inovação e Tecnologia": {
        "curta": "Novas soluções, ferramentas e transformação digital.",
        "longa": "Trata de inovação nos processos de compras, adoção de novas tecnologias, digitalização, "
                 "inteligência artificial, automação, modernização e melhoria dos processos da gestão "
                 "pública. Foco é a inovação e a transformação em si e as novas soluções.",
    },
    "Sustentabilidade e ODS": {
        "curta": "Compras sustentáveis e agenda ambiental/social.",
        "longa": "Aborda critérios de sustentabilidade nas contratações, licitações sustentáveis, os Objetivos "
                 "de Desenvolvimento Sustentável (ODS), impacto ambiental e responsabilidade social nos "
                 "processos de compra.",
    },
    "Controle, Auditoria e Combate à Corrupção": {
        "curta": "Fiscalização, auditoria e prevenção de irregularidades.",
        "longa": "Reúne conteúdo sobre controle interno e externo, auditoria de contratações, prevenção e "
                 "combate à corrupção, responsabilização e mecanismos de fiscalização dos atos "
                 "administrativos. Quando o foco for o ato de fiscalizar, auditar ou responsabilizar.",
    },
    "Gestão de Competências": {
        "curta": "Desenvolvimento de pessoas e capacidades da equipe.",
        "longa": "Trata das competências necessárias aos agentes públicos envolvidos em contratações, "
                 "capacitação, desenvolvimento de habilidades e gestão do conhecimento organizacional.",
    },
    "Logística e Gestão de Suprimentos": {
        "curta": "Operação logística e cadeia de suprimentos.",
        "longa": "Aborda armazenagem, distribuição, transporte, gestão de estoques e a cadeia de suprimentos "
                 "no setor público. Foco é a operação.",
    },
    "Compras Centralizadas/compartilhadas": {
        "curta": "Modelos de aquisição conjunta e centralizada.",
        "longa": "Trata de compras compartilhadas, centrais de compras, consórcios públicos e modelos de "
                 "aquisição centralizada entre órgãos. Foco no modelo de aquisição.",
    },
    "Transparência": {
        "curta": "Publicidade e acesso à informação.",
        "longa": "Aborda divulgação de dados de contratações, portais da transparência, Lei de Acesso à "
                 "Informação e publicidade dos atos administrativos. Controle social. Foco na divulgação e "
                 "acesso à informação.",
    },
    "Integridade": {
        "curta": "Ética, prevenção de conflitos e compliance.",
        "longa": "Trata de programas de integridade, prevenção de conflitos de interesse, compliance e "
                 "conduta ética dos agentes públicos. Foco na conduta ética e o compliance.",
    },
    "Micro e Pequenas Empresas": {
        "curta": "Tratamento diferenciado a MPEs nas compras.",
        "longa": "Aborda o tratamento favorecido a micro e pequenas empresas nas licitações, reserva de "
                 "mercado, simplificação de exigências e estímulo à participação.",
    },
    "Uso de Sistemas": {
        "curta": "Sistemas operacionais e plataformas de compras.",
        "longa": "Trata do uso de sistemas informatizados de compras, plataformas eletrônicas, sistemas de "
                 "registro de preços e ferramentas operacionais já adotadas. Específico sobre sistemas em uso.",
    },
    "Sanções Administrativas": {
        "curta": "Penalidades e responsabilização de fornecedores e agentes públicos.",
        "longa": "Aborda sanções aplicáveis a fornecedores e contratados, impedimentos de licitar, declaração "
                 "de inidoneidade e processos sancionatórios. Responsabilização dos Agentes públicos. Foca "
                 "na penalização.",
    },
    "Catálogo eletrônico de Padronização": {
        "curta": "Instrumento de padronização de itens de compra.",
        "longa": "Trata do catálogo eletrônico de padronização de materiais e serviços, instrumento previsto "
                 "na Lei nº 14.133/2021 para uniformizar especificações.",
    },
    "Gestão Estratégica e Desempenho das Contratações": {
        "curta": "Operação e resultados.",
        "longa": "Trata da operação e resultados dos processos: prazos, economicidade, produtividade, "
                 "indicadores, qualidade.",
    },
    "Logística Pública Internacional": {
        "curta": "Compras internacionais e cooperação.",
        "longa": "Marcos, comparações e cooperação internacional em contratações públicas.",
    },
}

_SEM_DESCRICAO = {"curta": "", "longa": ""}

# ---------------------------------------------------------------------------
# Definições de Subcategorias e Microcategorias (glossário de Coleções, "Saiba
# mais" de cada Categoria — 17/09/2026).
#
# STATUS: RASCUNHO TÉCNICO, A VALIDAR PELA CURADORIA (Lina). Ao contrário de
# ASSUNTOS_DESCRICAO (texto da curadoria, verbatim), a curadoria ainda não
# escreveu estas definições — nem a planilha (aba "Árvore de Classificação",
# só nomes), nem nr_subcategoria/nr_microcategoria (só nome e ordem) as têm.
# Cada frase abaixo foi escrita em Linguagem Simples a partir do dispositivo da
# Lei nº 14.133/2021 indicado no comentário; nada de valor-limite em reais (os
# tetos são atualizados por decreto). Quando a curadoria entregar o texto dela,
# substituir aqui, mantendo o padrão.
#
# Chave = nome canônico normalizado (caixa alta, espaços simples), o mesmo
# critério de catalog_tags.rotulo_sub — cobre subcategorias e microcategorias
# (os nomes são únicos entre os dois níveis; test_glossario_arvore garante a
# cobertura exata do seed 07-categories.sql).
ARVORE_DESCRICAO = {
    # PLANEJAMENTO/FASE PREPARATÓRIA
    "ETP": (                                                          # art. 6º, XX; art. 18, I e § 1º
        "O documento que abre o planejamento da contratação. Descreve a necessidade, compara as "
        "soluções possíveis e mostra se a contratação é viável."
    ),
    "TR": (                                                           # art. 6º, XXIII
        "O documento que descreve o que será contratado e como. Traz o objeto, os requisitos, o modelo "
        "de execução e de gestão, os critérios de pagamento e a estimativa de preço."
    ),
    "GESTÃO DE RISCOS": (                                             # art. 18, X; art. 22
        "Identificação dos riscos que podem prejudicar a licitação ou a execução do contrato, e das "
        "medidas para tratá-los."
    ),
    "MAPA DE RISCOS": (                                               # instrumento do art. 18, X
        "Lista dos riscos da contratação, com a probabilidade, o impacto e as ações para evitar ou "
        "reduzir cada um."
    ),
    "MATRIZ DE ALOCAÇÃO DE RISCOS": (                                 # art. 6º, XXVII; art. 22
        "Cláusula do contrato que define quais riscos ficam com a Administração e quais ficam com o "
        "contratado."
    ),
    "PESQUISA DE PREÇOS": (                                           # art. 23
        "Levantamento dos preços praticados no mercado para estimar o valor da contratação e avaliar "
        "as propostas."
    ),
    # SELEÇÃO DO FORNECEDOR
    "LICITAÇÃO": (                                                    # art. 28 (modalidades)
        "Disputa pública entre fornecedores, em uma das modalidades da lei, para escolher a proposta "
        "mais vantajosa."
    ),
    "CONCORRÊNCIA": (                                                 # art. 6º, XXXVIII
        "Modalidade de licitação para bens e serviços especiais e para obras e serviços de engenharia, "
        "comuns ou especiais."
    ),
    "PREGÃO": (                                                       # art. 6º, XLI
        "Modalidade de licitação obrigatória para bens e serviços comuns, julgada por menor preço ou "
        "maior desconto."
    ),
    "LEILÃO": (                                                       # art. 6º, XL
        "Modalidade de licitação para vender bens da Administração, como imóveis ou bens sem uso, a "
        "quem oferecer o maior lance."
    ),
    "DIÁLOGO COMPETITIVO": (                                          # art. 6º, XLII; art. 32
        "Modalidade em que a Administração conversa com fornecedores pré-selecionados para construir a "
        "solução antes de receber as propostas. Usada em contratações complexas ou inovadoras."
    ),
    "CONTRATAÇÃO DIRETA": (                                           # arts. 72 a 75
        "Contratação sem licitação, nos casos que a lei permite: por inexigibilidade ou por dispensa."
    ),
    "INEXIGIBILIDADE": (                                              # art. 74
        "Contratação direta quando não há como haver disputa — por exemplo, com fornecedor exclusivo ou "
        "com profissional de notória especialização."
    ),
    "EMERGÊNCIA - INCISO VIII": (                                     # art. 75, VIII
        "Dispensa de licitação em situação de emergência ou de calamidade pública, para atender uma "
        "urgência que possa causar prejuízo ou interromper um serviço público."
    ),
    "DISPENSA POR VALOR (ART 75 - INCISOS I E II)": (                 # art. 75, I e II
        "Dispensa de licitação para contratações de pequeno valor, até os limites que a lei fixa e "
        "atualiza para obras, serviços e compras."
    ),
    "CONTRATAÇÃO DIRETA OUTROS INCISOS": (                            # art. 75, III a XVIII
        "Os demais casos de dispensa previstos no art. 75, como licitação deserta ou fracassada, "
        "contratação de outro órgão público e situações específicas."
    ),
    "PROCEDIMENTOS AUXILIARES": (                                     # art. 78
        "Procedimentos que apoiam as licitações e as contratações: credenciamento, pré-qualificação, "
        "manifestação de interesse, registro de preços e registro cadastral."
    ),
    "CREDENCIAMENTO": (                                               # art. 6º, XLIII; art. 79
        "Chamamento público em que todos os interessados que cumprem os requisitos se cadastram para "
        "fornecer quando convocados, sem disputa entre eles."
    ),
    "REGISTRO DE PREÇOS (RP)": (                                      # art. 6º, XLV; arts. 82 a 86
        "Registro formal de preços de fornecedores, obtido por licitação, para contratações futuras "
        "conforme a necessidade."
    ),
    "PRÉ-QUALIFICAÇÃO": (                                             # art. 80
        "Seleção feita antes da licitação para verificar se os interessados ou os produtos atendem aos "
        "requisitos."
    ),
    "PMI": (                                                          # art. 81
        "Procedimento de Manifestação de Interesse: a Administração pede à iniciativa privada estudos e "
        "projetos de soluções inovadoras para uma necessidade."
    ),
    "REGISTRO CADASTRAL": (                                           # art. 87
        "Cadastro de fornecedores que antecipa a verificação de habilitação para as licitações futuras."
    ),
    # GESTÃO CONTRATUAL
    "GESTÃO DE CONTRATOS": (                                          # art. 117; art. 104 e seguintes
        "Acompanhamento do contrato pelo gestor: prazos, pagamentos, aditivos, prorrogações e "
        "encerramento."
    ),
    "FISCALIZAÇÃO DE CONTRATOS": (                                    # art. 117
        "Verificação, pelo fiscal, de que o contratado entrega o objeto como combinado, com registro "
        "das ocorrências."
    ),
}


def descricao_arvore(nome):
    """Definição de uma Subcategoria ou Microcategoria pelo nome canônico
    (normalizado como rotulo_sub); string vazia quando não há texto — um nó
    novo sem definição não quebra nada."""
    chave = " ".join(str(nome or "").upper().split())
    return ARVORE_DESCRICAO.get(chave, "")



def descricao_assunto(nome):
    """{"curta", "longa"} do Assunto pelo nome canônico; strings vazias quando
    não há descrição (um Assunto novo sem texto da curadoria não quebra nada)."""
    d = ASSUNTOS_DESCRICAO.get(str(nome or "").strip())
    return dict(d) if d else dict(_SEM_DESCRICAO)


# ---------------------------------------------------------------------------
# Metodologia de classificação — conteúdo das páginas de Coleções (Estrutura da
# classificação · Categorias · Assuntos). Porte do protótipo do Eduardo Cappia
# (github.com/dudyfarias/biblioteca, branch codex/biblioteca-home-acervo-filtros,
# src/lib/metodologia.ts, commits de 10 a 15/09/2026), reconciliado com a árvore
# canônica desta plataforma (seeds 07-categories.sql, v12.1) e com a terminologia
# fixada em 17/09/2026 (o eixo é "Categoria"; "etapa da contratação" explica).
#
# Divergências do protótipo resolvidas a favor da árvore da curadoria:
#   • o protótipo tratava "Procedimentos Auxiliares" como CATEGORIA própria, com
#     Registro de Preços como subcategoria; na árvore da BDLP Procedimentos
#     Auxiliares é SUBCATEGORIA de Seleção do Fornecedor e Registro de Preços (RP)
#     é microcategoria — os exemplos abaixo seguem a árvore;
#   • "Fase Preparatória - ETP" e "Contratação Todas as Fases" são grafias
#     anteriores (v12: "ETP"; v9: "Ciclo Completo da Contratação");
#   • a natureza usa os valores gravados no acervo (NATUREZA_CHOICES), não os
#     rótulos curtos do protótipo ("Material", "Serviços"...);
#   • "Pareceres" saiu do vocabulário na v12.1 (23/09) — a lista de tipos de cada
#     coleção vem de _TIPOS_POR_COLECAO, não do protótipo.
# ---------------------------------------------------------------------------

# Os seis campos, na ordem da fórmula da curadoria. `legenda` = frase curta do
# cartão; `pergunta` e `descricao` = painel de explicação.
CAMPOS_CLASSIFICACAO = [
    {
        "id": "colecao", "nome": "Coleção", "obrigatorio": True, "icon": "fi-book-open",
        "resumo": "Tipo de informação",
        "legenda": "Define a coleção a partir do tipo de informação.",
        "pergunta": "Em que forma ou tipo o material se apresenta?",
        "descricao": "É definida pelo tipo de informação do material. Um artigo, uma dissertação e um "
                     "manual podem tratar do mesmo tema e pertencer a coleções diferentes.",
    },
    {
        "id": "categoria", "nome": "Categoria", "obrigatorio": True, "icon": "fi-layers",
        "resumo": "Etapa da contratação",
        "legenda": "Situa o conteúdo no ciclo da contratação.",
        "pergunta": "A que etapa do ciclo da contratação o conteúdo se refere?",
        "descricao": "Situa o conteúdo no ciclo da contratação pública, do planejamento à gestão do "
                     "contrato. É o ponto de partida para identificar uma subcategoria e, quando "
                     "existir, uma microcategoria.",
    },
    {
        "id": "subcategoria", "nome": "Subcategoria", "obrigatorio": False, "icon": "fi-folder",
        "resumo": "Tópico da etapa",
        "legenda": "Detalha um tópico dentro da categoria.",
        "pergunta": "Qual tópico específico daquela etapa?",
        "descricao": "Detalha um tópico dentro da categoria escolhida. É preenchida quando esse "
                     "desdobramento existe na árvore e corresponde ao conteúdo do material.",
    },
    {
        "id": "microcategoria", "nome": "Microcategoria", "obrigatorio": False, "icon": "fi-file-text",
        "resumo": "Modalidade, regime ou hipótese",
        "legenda": "Especifica a modalidade, o regime ou a hipótese.",
        "pergunta": "Qual modalidade, regime ou hipótese?",
        "descricao": "Especifica o recorte previsto dentro da subcategoria, como uma modalidade de "
                     "licitação ou uma hipótese de contratação direta. Depende da categoria e da "
                     "subcategoria selecionadas.",
    },
    {
        "id": "assunto", "nome": "Assunto", "obrigatorio": True, "icon": "fi-tag",
        "resumo": "Tema central",
        "legenda": "Identifica o tema principal do conteúdo.",
        "pergunta": "Sobre qual tema o conteúdo trata?",
        "descricao": "Identifica o foco temático do material entre os assuntos da biblioteca. O "
                     "assunto pode aparecer em diferentes coleções e etapas da contratação.",
    },
    {
        "id": "natureza", "nome": "Natureza", "obrigatorio": False, "icon": "fi-grid",
        "resumo": "Objeto da contratação",
        "legenda": "Identifica o objeto da contratação.",
        "pergunta": "Qual é o objeto da contratação?",
        "descricao": "Identifica o objeto da contratação: materiais, serviços, obras e serviços de "
                     "engenharia ou tecnologia da informação e comunicação (TIC). É informada quando "
                     "esse recorte se aplica ao conteúdo; nos demais casos, recebe \"Não se aplica\".",
    },
]

# Exemplos ilustrativos (não são registros do acervo). `valores` segue a ordem de
# CAMPOS_CLASSIFICACAO. O primeiro também é o "Exemplo prático" da página.
EXEMPLOS_CLASSIFICACAO = [
    {
        "titulo": "Artigo sobre Registro de Preços para aquisição de cadeiras de escritório",
        "intro": "Um artigo que discute aspectos normativos, procedimentos, limitações e cuidados "
                 "sobre Registro de Preços para aquisição de cadeiras de escritório.",
        "valores": ["Doutrina e Conteúdo Técnico", "Seleção do Fornecedor", "Procedimentos Auxiliares",
                    "Registro de Preços (RP)", "Aspectos Jurídicos e Regulatórios",
                    "Contratação de Materiais"],
        "nota": "Coleção, categoria e assunto são obrigatórios. Neste artigo, subcategoria, "
                "microcategoria e natureza também se aplicam: Seleção do Fornecedor é a categoria, "
                "Procedimentos Auxiliares é a subcategoria e Registro de Preços (RP) é a "
                "microcategoria. Aspectos Jurídicos e Regulatórios identifica o foco do artigo, e "
                "Contratação de Materiais identifica as cadeiras de escritório que serão adquiridas.",
    },
    {
        "titulo": "Manual de elaboração do Estudo Técnico Preliminar para serviços",
        "intro": "O manual orienta a aplicação das normas na elaboração de um ETP para a "
                 "contratação de serviços.",
        "valores": ["Instrução e Capacitação", "Planejamento/Fase Preparatória",
                    "Estudo Técnico Preliminar (ETP)", "Não se aplica",
                    "Aspectos Jurídicos e Regulatórios", "Contratação de Serviços"],
        "nota": "A subcategoria já identifica o tópico. Sem um desdobramento aplicável, a "
                "microcategoria não é preenchida.",
    },
    {
        "titulo": "Artigo sobre governança ao longo do ciclo da contratação",
        "intro": "O artigo discute papéis e tomada de decisão em todo o ciclo, sem se restringir a "
                 "uma etapa ou a um objeto contratado.",
        "valores": ["Doutrina e Conteúdo Técnico", "Ciclo Completo da Contratação", "Não se aplica",
                    "Não se aplica", "Governança", "Não se aplica"],
        "nota": "Coleção, categoria e assunto continuam presentes. Os demais campos não se aplicam "
                "ao recorte deste exemplo.",
    },
]

# Ícones das coleções na página de metodologia (escolha do Eduardo para esta
# página: martelo para Jurisprudência e apresentação para Instrução; as demais
# usam o mesmo ícone de COLECOES_V6).
COLECOES_ICONE_METODOLOGIA = {
    "Jurisprudência": "fi-gavel",
    "Instrução e Capacitação": "fi-presentation",
}

# "Foco da classificação" de cada Assunto — TRANSCRITO DO PROTÓTIPO DO EDUARDO
# (metodologia.ts, 15/09/2026): reformulação, em uma frase, do critério que a
# Lina escreveu no fim da explicação longa ("Quando o foco for…"). Não é texto
# da curadoria; a validar por ela junto com ARVORE_DESCRICAO.
ASSUNTOS_FOCO = {
    "Aspectos Jurídicos e Regulatórios": "Como o assunto é tratado na norma.",
    "Governança": "A estrutura de gestão como um todo.",
    "Inovação e Tecnologia": "A inovação e a transformação em si e as novas soluções.",
    "Sustentabilidade e ODS": "Os critérios ambientais e sociais das contratações.",
    "Controle, Auditoria e Combate à Corrupção": "O ato de fiscalizar, auditar ou responsabilizar.",
    "Gestão de Competências": "As pessoas, suas habilidades e sua formação.",
    "Logística e Gestão de Suprimentos": "A operação logística.",
    "Compras Centralizadas/compartilhadas": "O modelo de aquisição.",
    "Transparência": "A divulgação e o acesso à informação.",
    "Integridade": "A conduta ética e o compliance.",
    "Micro e Pequenas Empresas": "A participação e o tratamento favorecido às MPEs.",
    "Uso de Sistemas": "Os sistemas que já estão em uso.",
    "Sanções Administrativas": "A penalização.",
    "Catálogo eletrônico de Padronização": "A padronização das especificações de materiais e serviços.",
    "Gestão Estratégica e Desempenho das Contratações": "A operação e os resultados dos processos de contratação.",
    "Logística Pública Internacional": "Os marcos, as comparações e a cooperação internacional em "
                                       "contratações públicas.",
}

# Ícone de cada Assunto (methodology-icons.tsx do protótipo; sprite _feather.html).
ASSUNTOS_ICONE = {
    "Aspectos Jurídicos e Regulatórios": "fi-scale",
    "Governança": "fi-building",
    "Inovação e Tecnologia": "fi-settings",
    "Sustentabilidade e ODS": "fi-leaf",
    "Controle, Auditoria e Combate à Corrupção": "fi-chart",
    "Gestão de Competências": "fi-users",
    "Logística e Gestão de Suprimentos": "fi-truck",
    "Compras Centralizadas/compartilhadas": "fi-link",
    "Transparência": "fi-eye",
    "Integridade": "fi-shield",
    "Micro e Pequenas Empresas": "fi-store",
    "Uso de Sistemas": "fi-monitor",
    "Sanções Administrativas": "fi-gavel",
    "Catálogo eletrônico de Padronização": "fi-list",
    "Gestão Estratégica e Desempenho das Contratações": "fi-trending-up",
    "Logística Pública Internacional": "fi-globe",
}

# "Como diferenciar assuntos próximos" (protótipo do Eduardo; a validar pela curadoria).
ASSUNTOS_COMPARACOES = [
    ("Inovação e Tecnologia / Uso de Sistemas",
     "O primeiro trata de transformação e novas soluções. O segundo trata da operação de "
     "sistemas e plataformas já adotados."),
    ("Governança / Integridade",
     "Governança aborda papéis, decisões e a estrutura de gestão. Integridade aborda conduta "
     "ética, conflitos de interesse e compliance."),
    ("Controle, Auditoria e Combate à Corrupção / Sanções Administrativas",
     "O primeiro tem foco em fiscalização e auditoria. Sanções Administrativas tem foco nas "
     "penalidades e nos processos sancionatórios."),
]


def ordenar_como_a_curadoria(assuntos):
    """Ordena dicts de assunto (chave "nome") na sequência da caracterização da
    curadoria (11/09/2026) — a mesma numeração 01–16 da página de Assuntos do
    protótipo do Eduardo. Nome fora da lista vai para o fim, em ordem alfabética."""
    posicao = {nome: i for i, nome in enumerate(ASSUNTOS_DESCRICAO)}
    return sorted(assuntos, key=lambda a: (posicao.get(a["nome"], len(posicao)), a["nome"]))

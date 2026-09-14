"""
Coleções v6 (canônicas, §7) com o vocabulário de Tipos de Informação da
taxonomia v12 (set/2026) e o de-para de grafias legadas.

As 4 Coleções são definidas pelo *Tipo de Informação*. Os mapas abaixo:
  - COLECOES_V6 / _TIPOS_POR_COLECAO: vocabulário EXATO v12 (e-mail "ALTERAÇÕES
    BIBLIOTECA", Lina, 11/09/2026): Jurisprudência = Súmulas, Boletins, Acórdãos,
    Deliberações; Doutrina ganha Enunciados e Pareceres; Instrução perde Vídeos.
  - TIPO_V5_TO_V6: normaliza grafias legadas (singular, sem acento, nomes do
    acervo v5) para o tipo canônico — usado pelo front (colecao_v6_for_tipo) e
    pelo importador (tipo_canonico).
  - TIPOS_LEGADOS: tipos RETIRADOS do vocabulário (Documentos Normativos, Vídeos)
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
     "descricao": "Livros, artigos, relatórios, notas técnicas, pareceres e enunciados que analisam e "
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

# Tipos de Informação EXATOS por coleção — vocabulário v12 (11/09/2026).
_TIPOS_POR_COLECAO = {
    "Jurisprudência": ["Súmulas", "Boletins", "Acórdãos", "Deliberações"],
    "Trabalhos Acadêmicos": ["Teses", "Dissertações", "Monografias", "TCCs", "Memoriais Docentes"],
    "Doutrina e Conteúdo Técnico": [
        "Livros digitais", "Artigos", "Notas Técnicas", "Relatórios",
        "Textos de Discussão", "Resumos", "Resumos expandidos", "Enunciados", "Pareceres",
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

# Tipos retirados do vocabulário na v12, ainda exibidos na coleção antiga
# enquanto houver documento carregado com eles (só colecao_v6_for_tipo usa).
TIPOS_LEGADOS = {
    "Documentos Normativos": "Jurisprudência",
    "Vídeos": "Instrução e Capacitação",
}
_TIPOS_LEGADOS_NORM = {_norm(k): v for k, v in TIPOS_LEGADOS.items()}
_TIPOS_LEGADOS_NORM.update({
    "documento normativo": "Jurisprudência",
    "video": "Instrução e Capacitação",
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
    "parecer": "Pareceres",
    "pareceres": "Pareceres",
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


def descricao_assunto(nome):
    """{"curta", "longa"} do Assunto pelo nome canônico; strings vazias quando
    não há descrição (um Assunto novo sem texto da curadoria não quebra nada)."""
    d = ASSUNTOS_DESCRICAO.get(str(nome or "").strip())
    return dict(d) if d else dict(_SEM_DESCRICAO)

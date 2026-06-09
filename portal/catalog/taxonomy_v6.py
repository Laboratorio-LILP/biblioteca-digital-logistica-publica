"""
Coleções v6 (canônicas, §7 / planilha BDLP_Template_Insercao_v6.xlsx) e o de-para
da classificação v5 → v6.

A v6 define 4 Coleções pelo *Tipo de Informação*. Os mapas abaixo:
  - COLECOES_V6 / _TIPOS_POR_COLECAO: vocabulário EXATO da planilha v6.
  - TIPO_V5_TO_V6: normaliza nomes de tipo do acervo legado para os tipos v8
    (usado só pelo front, em colecao_v6_for_tipo, p/ resiliência de exibição).
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
    {"nome": "Jurisprudência", "slug": "jurisprudencia", "icon": "fi-shield", "color": "c-bluedark",
     "descricao": "Decisões, súmulas, enunciados e documentos normativos que orientam como aplicar a lei."},
    {"nome": "Trabalhos Acadêmicos", "slug": "trabalhos-academicos", "icon": "fi-layers", "color": "c-blue",
     "descricao": "Teses, dissertações, monografias e TCCs produzidos em universidades."},
    {"nome": "Doutrina e Conteúdo Técnico", "slug": "doutrina", "icon": "fi-book-open", "color": "c-red",
     "descricao": "Livros, artigos, relatórios e notas técnicas que analisam e explicam o tema."},
    {"nome": "Instrução e Capacitação", "slug": "instrucao", "icon": "fi-file-text", "color": "c-green",
     "descricao": "Manuais, guias, cursos e materiais para aprender na prática."},
]
COLECOES_BY_NOME = {c["nome"]: c for c in COLECOES_V6}
COLECOES_BY_SLUG = {c["slug"]: c for c in COLECOES_V6}

# Tipos de Informação EXATOS por coleção (planilha v6, aba "Coleção, Assunto e Natureza")
_TIPOS_POR_COLECAO = {
    "Jurisprudência": ["Enunciados", "Súmulas", "Boletins", "Documentos Normativos"],
    "Trabalhos Acadêmicos": ["Teses", "Dissertações", "Monografias", "TCCs", "Memoriais Docentes"],
    "Doutrina e Conteúdo Técnico": [
        "Livros digitais", "Artigos", "Notas Técnicas", "Relatórios",
        "Textos de Discussão", "Resumos", "Resumos expandidos",
    ],
    "Instrução e Capacitação": [
        "Manuais", "Guias", "Tutoriais", "Apostilas", "Aulas", "Cursos", "Vídeos", "Slides",
    ],
}

# nome-normalizado do tipo v6 → coleção
TIPO_TO_COLECAO = {}
for _col, _tipos in _TIPOS_POR_COLECAO.items():
    for _t in _tipos:
        TIPO_TO_COLECAO[_norm(_t)] = _col

_FALLBACK = "Doutrina e Conteúdo Técnico"

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
    "videos": "Vídeos",
    "video": "Vídeos",
    "apresentacoes": "Slides",
    "slides": "Slides",
    # Jurisprudência
    "documento normativo": "Documentos Normativos",
    "documentos normativos": "Documentos Normativos",
    "enunciados": "Enunciados",
    "sumulas": "Súmulas",
    "boletins": "Boletins",
}


def colecao_v6_for_tipo(type_name):
    """Coleção v6 (dict) para um nome de Tipo de Informação (v5 ou v6)."""
    key = _norm(type_name)
    # normaliza nome v5 → v6 antes de buscar a coleção
    v6 = TIPO_V5_TO_V6.get(key)
    lookup = _norm(v6) if v6 else key
    nome = TIPO_TO_COLECAO.get(lookup, _FALLBACK)
    return COLECOES_BY_NOME[nome]


def tipos_de_colecao(slug_or_nome):
    """Tipos de Informação v6 que compõem uma coleção (para o filtro colecao_v6)."""
    col = COLECOES_BY_SLUG.get(slug_or_nome) or COLECOES_BY_NOME.get(slug_or_nome)
    if not col:
        return []
    return list(_TIPOS_POR_COLECAO.get(col["nome"], []))

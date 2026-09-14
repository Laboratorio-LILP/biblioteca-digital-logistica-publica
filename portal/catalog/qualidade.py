"""Verificações de redundância e de qualidade para a curadoria — só relatório.

Funções puras (sem banco, sem Django), usadas por `validate_import` (acervo
carregado) e por `migrate_spreadsheet --dry-run` (linhas da planilha, como
AVISOS — nunca recusam uma linha nem alteram dados). Cada achado tem um
código, as referências (linha da planilha ou `code` do documento), um título
curto e, quando ajuda, um detalhe.

Origem (Lina, 14/09/2026): resumos que são trechos copiados ("começa com
letra minúscula e termina com três pontinhos"), citações "[4]" no meio do
texto, introduções do Scribd no lugar do resumo, e duplicidades "caracterizadas
de forma diferente". Publicações do subsecretário compartilham a URL de uma
estante (fliphtml5): URL igual com título diferente NÃO é duplicata.

Códigos:
  DUPLICATA_TITULO        mesmo título normalizado (sem acento, caixa, pontuação
                          e espaços múltiplos) em duas ou mais linhas.
  DUPLICATA_DOI           mesmo DOI normalizado (sem prefixo doi.org/"doi:").
  DUPLICATA_DIVERGENTE    duplicata (por título ou DOI) cujas linhas divergem em
                          Coleção, Tipo, Assunto, Categoria ou Subcategoria —
                          "duplicidade caracterizada de forma diferente", o caso
                          mais perigoso; o detalhe lista os campos divergentes.
  ENDERECO_COMPARTILHADO  mesmo acesso_eletronico normalizado (sem #fragmento,
                          sem parâmetros utm_*, sem barra final, host em caixa
                          baixa) com títulos DIFERENTES — "estante/coletânea?
                          confirmar endereço individual". Não é duplicata.
  RESUMO_VAZIO            sem resumo.
  RESUMO_MINUSCULA        resumo começa com letra minúscula (trecho do meio do texto).
  RESUMO_RETICENCIAS      resumo termina com "..." ou "…" (trecho cortado).
  RESUMO_CITACAO          marcador de citação [n] ou [n, m] no resumo (um ano
                          entre colchetes, como [2024], não conta).
  RESUMO_CURTO            menos de 300 caracteres (mínimo da planilha-modelo).
  RESUMO_IGUAL_TITULO     resumo começa repetindo o título.
  RESUMO_SCRIBD           endereço em scribd.com — a página traz uma introdução,
                          não o resumo: "conferir se é resumo de fato".
  AUTORIA_SERIE           mesmo autor pessoa em todos os volumes de uma série com
                          "Caderno", "Manual" ou "Guia" no título — aponta, não julga.

Um resumo pode acumular vários códigos. O relatório da curadoria usa
`resumir()` (contagem por código) e `formatar_relatorio()` (linhas prontas).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit

RESUMO_MINIMO = 300
_CAMPOS_CARACTERIZACAO = (
    ("colecao", "Coleção"), ("tipo", "Tipo"), ("assunto", "Assunto"),
    ("categoria", "Categoria"), ("subcategoria", "Subcategoria"),
)
_CITACAO_RE = re.compile(r"\[\d{1,3}(?:\s*[,;–-]\s*\d{1,3})*\]")
_SERIE_RE = re.compile(r"\b(caderno|cadernos|manual|manuais|guia|guias)\b")
_SEPARADOR_SUBTITULO_RE = re.compile(r"\s*[:—–]\s+|\s+-\s+")
# Numeral romano na gramática estrita (não casa "civil", "mil", "vil").
_ROMANO_RE = re.compile(r"^(?=[ivxlcdm])m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$")
# DOI de verdade: prefixo 10.NNNN/… — placeholders ("Não possui", "-", "n/a") não agrupam.
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
# Fechos que podem vir depois das reticências ("...", "…") no fim do resumo.
_FECHOS_FINAIS = "\"'”’)]»"
_TOKENS_VOLUME = {"vol", "volume", "volumes", "parte", "n", "no", "num", "numero", "edicao", "ed", "tomo", "fasciculo"}


@dataclass
class Achado:
    """Um achado de qualidade: código, referências (linhas/codes), título curto e detalhe."""

    codigo: str
    refs: list = field(default_factory=list)
    titulo: str = ""
    detalhe: str = ""


def _texto(v) -> str:
    return " ".join(str(v if v is not None else "").split())


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalizar_titulo(s) -> str:
    """Sem acento, minúsculas, sem pontuação, espaços colapsados — chave de duplicata."""
    t = _sem_acento(_texto(s)).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def normalizar_doi(s) -> str:
    """DOI em minúsculas, sem prefixos https://doi.org/, doi.org/ e 'doi:'."""
    d = _texto(s).lower()
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d).strip()
    return d if _DOI_RE.match(d) else ""


def _host(u: str) -> str:
    """Host (caixa baixa, sem www.) de um endereço; '' se não for URL."""
    if not u:
        return ""
    if "://" not in u:
        u = "http://" + u
    try:
        host = (urlsplit(u).hostname or "").lower()
    except ValueError:  # ex.: "[Acesso restrito]" (colchetes viram IPv6 inválido)
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host if "." in host else ""   # placeholders ("n/a", "-", "Não possui") não são endereço


def normalizar_url(s) -> str:
    """Chave de endereço: sem esquema, host em caixa baixa, sem #fragmento, sem
    parâmetros utm_*, sem barra final; '' para o que não é URL."""
    u = _texto(s)
    host = _host(u)
    if not host:
        return ""
    if "://" not in u:
        u = "http://" + u
    partes = urlsplit(u)
    caminho = partes.path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    chave = host + caminho
    if query:
        chave += "?" + urlencode(sorted(query))
    return chave


def registro(ref, titulo, doi="", url="", resumo="", colecao="", tipo="", assunto="", categoria="",
             subcategoria="", autor="") -> dict:
    """Um item a verificar (linha da planilha ou documento do banco), com os campos normalizados a texto."""
    return {
        "ref": str(ref), "titulo": _texto(titulo), "doi": _texto(doi), "url": _texto(url),
        "resumo": " ".join(str(resumo if resumo is not None else "").split()), "colecao": _texto(colecao),
        "tipo": _texto(tipo), "assunto": _texto(assunto), "categoria": _texto(categoria),
        "subcategoria": _texto(subcategoria), "autor": _texto(autor),
    }


def _titulo_curto(s: str, n: int = 80) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _agrupar(registros, chave):
    grupos: "OrderedDict[str, list]" = OrderedDict()
    for r in registros:
        k = chave(r)
        if k:
            grupos.setdefault(k, []).append(r)
    return [g for g in grupos.values() if len(g) > 1]


def _divergencia(grupo) -> list[str]:
    """Campos de caracterização com mais de um valor distinto dentro do grupo."""
    campos = []
    for campo, rotulo in _CAMPOS_CARACTERIZACAO:
        valores = {_sem_acento(r[campo]).casefold() for r in grupo}
        if len(valores) > 1:
            distintos = sorted({r[campo] or "(vazio)" for r in grupo})
            campos.append(f"{rotulo} ({' ≠ '.join(distintos)})")
    return campos


def duplicatas(registros) -> list[Achado]:
    """Duplicatas por título normalizado e por DOI; grupos que divergem na
    caracterização ganham também DUPLICATA_DIVERGENTE (uma vez por grupo)."""
    achados: list[Achado] = []
    divergentes_vistos = set()
    for codigo, chave in (("DUPLICATA_TITULO", lambda r: normalizar_titulo(r["titulo"])),
                          ("DUPLICATA_DOI", lambda r: normalizar_doi(r["doi"]))):
        for grupo in _agrupar(registros, chave):
            refs = [r["ref"] for r in grupo]
            titulo = _titulo_curto(grupo[0]["titulo"])
            achados.append(Achado(codigo, refs, titulo, f"{len(grupo)} linhas"))
            campos = _divergencia(grupo)
            marca = frozenset(refs)
            if campos and marca not in divergentes_vistos:
                divergentes_vistos.add(marca)
                achados.append(Achado(
                    "DUPLICATA_DIVERGENTE", refs, titulo,
                    "duplicidade caracterizada de forma diferente — campos divergentes: " + "; ".join(campos),
                ))
    return achados


def enderecos_compartilhados(registros) -> list[Achado]:
    """Mesmo endereço normalizado com títulos diferentes — estante/coletânea, não duplicata."""
    achados = []
    for grupo in _agrupar(registros, lambda r: normalizar_url(r["url"])):
        titulos = {normalizar_titulo(r["titulo"]) for r in grupo}
        if len(titulos) < 2:
            continue  # títulos iguais no mesmo endereço → é DUPLICATA_TITULO
        achados.append(Achado(
            "ENDERECO_COMPARTILHADO", [r["ref"] for r in grupo], _titulo_curto(grupo[0]["url"]),
            f"{len(titulos)} títulos diferentes no mesmo endereço — estante/coletânea? confirmar endereço individual",
        ))
    return achados


def resumo_suspeito(reg) -> list[str]:
    """Códigos de resumo suspeito para um registro (pode acumular vários)."""
    resumo = reg["resumo"]
    codigos = []
    if not resumo:
        codigos.append("RESUMO_VAZIO")
    else:
        if resumo[0].islower():
            codigos.append("RESUMO_MINUSCULA")
        fim = resumo.rstrip(_FECHOS_FINAIS)          # "(...)", "[...]", '..."' também são corte
        if fim.endswith("...") or fim.endswith("…"):
            codigos.append("RESUMO_RETICENCIAS")
        if _CITACAO_RE.search(resumo):
            codigos.append("RESUMO_CITACAO")
        if len(resumo) < RESUMO_MINIMO:
            codigos.append("RESUMO_CURTO")
        t = normalizar_titulo(reg["titulo"])
        if len(t) >= 10 and normalizar_titulo(resumo).startswith(t):
            codigos.append("RESUMO_IGUAL_TITULO")
    host = _host(reg["url"])
    if host == "scribd.com" or host.endswith(".scribd.com"):
        codigos.append("RESUMO_SCRIBD")
    return codigos


def _chave_serie(titulo: str) -> str:
    base = _SEPARADOR_SUBTITULO_RE.split(_texto(titulo), maxsplit=1)[0]
    tokens = [t for t in normalizar_titulo(base).split()
              if not t.isdigit() and not _ROMANO_RE.match(t) and t not in _TOKENS_VOLUME]
    return " ".join(tokens)


def _autor_pessoa(autor: str) -> bool:
    """'Sobrenome, Nome' (ABNT) — a vírgula é o sinal mais barato de autor pessoa."""
    return "," in autor


def autoria_institucional_suspeita(registros) -> list[Achado]:
    """Séries (Caderno/Manual/Guia) cujos volumes têm todos o MESMO autor pessoa."""
    candidatos = [r for r in registros if _SERIE_RE.search(normalizar_titulo(r["titulo"]))]
    achados = []
    for grupo in _agrupar(candidatos, lambda r: _chave_serie(r["titulo"])):
        autores = {_sem_acento(r["autor"]).casefold() for r in grupo}
        if len(autores) != 1:
            continue
        autor = grupo[0]["autor"]
        if not autor or not _autor_pessoa(autor):
            continue
        achados.append(Achado(
            "AUTORIA_SERIE", [r["ref"] for r in grupo], _titulo_curto(grupo[0]["titulo"]),
            f"{len(grupo)} volumes com o mesmo autor pessoa ({autor}) — autoria institucional? aponta, não julga",
        ))
    return achados


def analisar(registros) -> list[Achado]:
    """Todos os achados, na ordem: duplicatas, endereços compartilhados, resumos, autoria."""
    registros = list(registros)
    achados = duplicatas(registros) + enderecos_compartilhados(registros)
    for r in registros:
        for codigo in resumo_suspeito(r):
            achados.append(Achado(codigo, [r["ref"]], _titulo_curto(r["titulo"])))
    achados += autoria_institucional_suspeita(registros)
    return achados


def resumir(achados) -> Counter:
    """Contagem de achados por código."""
    return Counter(a.codigo for a in achados)


def formatar_relatorio(achados, limite: int = 10) -> list[str]:
    """Linhas do relatório: contagem por código e até `limite` exemplos por código."""
    if not achados:
        return ["  nenhum achado"]
    linhas = []
    contagem = resumir(achados)
    por_codigo: dict[str, list[Achado]] = {}
    for a in achados:
        por_codigo.setdefault(a.codigo, []).append(a)
    for codigo, n in contagem.most_common():
        linhas.append(f"  {codigo}: {n}")
        for a in por_codigo[codigo][:limite]:
            detalhe = f" — {a.detalhe}" if a.detalhe else ""
            linhas.append(f"      {', '.join(a.refs)}: {a.titulo}{detalhe}")
        if n > limite:
            linhas.append(f"      … e mais {n - limite}")
    return linhas

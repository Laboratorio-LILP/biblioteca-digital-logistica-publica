"""Vetor da busca textual — fonte única para o Django e para o SQL.

A busca casa `vetor @@ consulta`, onde o vetor é a soma dos campos abaixo, com
peso, nas configurações `portuguese` (radicalizador oficial) e
`portuguese_unaccent` (a mesma, com unaccent antes do radical — "pregao" acha
"pregão"). Até 23/09/2026 o Django montava esse vetor a cada consulta e o
Postgres varria a tabela inteira (Seq Scan): a home, com 5 buscas, levava
~2,8 s (achado F2-02). Agora o vetor vive na coluna GERADA
`nr_document.busca`, com índice GIN, e o Django só a lê.

Para que a coluna dê exatamente o mesmo resultado que o vetor calculado, os
dois nascem daqui: `expressao_vetor()` é o vetor que o Django montava (e ainda
monta, quando o banco não tem a coluna); `sql_coluna_gerada()` é o texto da
coluna nos arquivos SQL — o teste confere que o seed e a migração o trazem
igual. Mudou um campo ou um peso? Muda aqui, regrava o SQL nos dois arquivos e
a migração recria a coluna.
"""

from django.contrib.postgres.search import SearchVector

# Campos e pesos. Inclui campos LILP (complexidade, uso_futuro, metodo,
# resultado) além dos clássicos title/keywords/author/abstract.
FTS_CAMPOS = (
    ("title", "A"),
    ("keywords", "A"),
    ("author", "B"),
    ("autor_principal", "B"),
    ("abstract", "C"),
    ("uso_futuro", "C"),
    ("metodo", "D"),
    ("resultado", "D"),
    ("complexidade", "D"),
)

# Ordem importa só para o texto do SQL ser estável; o tsvector resultante é o
# mesmo em qualquer ordem.
CONFIGS = ("portuguese", "portuguese_unaccent")


def vetor(config):
    """Soma dos SearchVector dos campos numa configuração de busca (Django)."""
    total = None
    for campo, peso in FTS_CAMPOS:
        sv = SearchVector(campo, weight=peso, config=config)
        total = sv if total is None else total + sv
    return total


def expressao_vetor():
    """O vetor completo (as duas configurações), como expressão do Django."""
    return vetor(CONFIGS[0]) + vetor(CONFIGS[1])


def sql_coluna_gerada():
    """Definição da coluna gerada, no SQL do Postgres. Espelha SearchVector:
    setweight(to_tsvector(config, coalesce(campo, '')), peso), somados com ||."""
    partes = [
        f"setweight(to_tsvector('{config}', coalesce({campo}, '')), '{peso}')"
        for config in CONFIGS
        for campo, peso in FTS_CAMPOS
    ]
    corpo = " ||\n        ".join(partes)
    return f"GENERATED ALWAYS AS (\n        {corpo}\n    ) STORED"

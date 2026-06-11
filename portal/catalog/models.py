import unicodedata

from django.db import models


def _author_key(s):
    """Normaliza nome de autor para comparação (sem acento, minúsculo, espaços colapsados)."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


class Topic(models.Model):
    """Coleções/subcoleções — mapeia tabela 'topic' do Nou-Rau."""

    name = models.CharField(max_length=300)
    description = models.CharField(max_length=300, blank=True)
    parent_id = models.IntegerField(default=0)
    maintainer_id = models.IntegerField(null=True, blank=True)
    options = models.CharField(max_length=2000, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)
    tipo_acesso = models.IntegerField(default=0)
    archieve = models.CharField(max_length=1, default="s")
    url = models.CharField(max_length=150, blank=True)
    remote = models.CharField(max_length=1, default="n")

    class Meta:
        managed = False
        db_table = "topic"

    def __str__(self):
        return self.name

    @property
    def is_root(self):
        return self.parent_id == 0

    @property
    def children(self):
        return Topic.objects.filter(parent_id=self.id)

    @property
    def parent(self):
        if self.parent_id == 0:
            return None
        return Topic.objects.filter(id=self.parent_id).first()


class TopicPath(models.Model):
    """Caminho hierárquico das coleções — mapeia tabela 'topic_path'."""

    topic_id = models.IntegerField(primary_key=True)
    parent_ids = models.CharField(max_length=200, blank=True)
    parent_names = models.CharField(max_length=2000, blank=True)
    changed = models.CharField(max_length=1, default="n")

    class Meta:
        managed = False
        db_table = "topic_path"


class NrCategory(models.Model):
    """Categorias temáticas — mapeia tabela 'nr_category'."""

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=150, blank=True)
    max_size = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "nr_category"

    def __str__(self):
        return self.name


class NrFormat(models.Model):
    """Formatos de arquivo — mapeia tabela 'nr_format'."""

    name = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, blank=True)
    subtype = models.CharField(max_length=100, blank=True)
    extension = models.CharField(max_length=10, blank=True)
    icon = models.CharField(max_length=3, blank=True)
    compress = models.CharField(max_length=1, blank=True)
    verify = models.CharField(max_length=1, blank=True)
    name_pt = models.CharField(max_length=50, blank=True)

    class Meta:
        managed = False
        db_table = "nr_format"

    def __str__(self):
        return self.name


class TypeInformation(models.Model):
    """Tipos de informação (artigo, tese, etc.) — mapeia tabela 'type_information'."""

    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = "type_information"

    def __str__(self):
        return self.name


class Assunto(models.Model):
    """Eixo temático transversal (16 valores) — mapeia tabela 'nr_assunto'."""

    nome = models.CharField(max_length=255, unique=True)
    slug = models.CharField(max_length=255, unique=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "nr_assunto"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Subcategoria(models.Model):
    """Subcategoria sob uma Categoria (~47 valores) — mapeia tabela 'nr_subcategoria'."""

    nome = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    category_id = models.IntegerField()
    ordem = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "nr_subcategoria"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome

    @property
    def category(self):
        if self.category_id:
            return NrCategory.objects.filter(id=self.category_id).first()
        return None


class Microcategoria(models.Model):
    """Microcategoria sob uma Subcategoria (~80 valores) — mapeia tabela 'nr_microcategoria'."""

    nome = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    subcategoria_id = models.IntegerField()
    ordem = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "nr_microcategoria"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome

    @property
    def subcategoria(self):
        if self.subcategoria_id:
            return Subcategoria.objects.filter(id=self.subcategoria_id).first()
        return None


# Natureza do objeto da contratação — taxonomia v6 (5 valores canônicos, §7).
# Obrigatória na captura/curadoria; nullable no schema para não quebrar os
# registros legados até o de-para v5→v6 (P2).
NATUREZA_CHOICES = [
    ("Contratação de Materiais", "Contratação de Materiais"),
    ("Contratação de Obras e Serviços de Engenharia", "Contratação de Obras e Serviços de Engenharia"),
    ("Contratação de Serviços", "Contratação de Serviços"),
    ("Contratação de TIC", "Contratação de TIC"),
    ("Não se aplica", "Não se aplica"),
]


class Document(models.Model):
    """Documento digital — mapeia tabela 'nr_document' do Nou-Rau."""

    STATUS_CHOICES = [
        ("i", "Incoming"),
        ("w", "Waiting"),
        ("a", "Archived"),
        ("d", "Denied"),
        ("v", "Verified"),
    ]

    title = models.CharField(max_length=1500)
    title_en = models.CharField(max_length=1500, blank=True)
    author = models.CharField(max_length=3000, blank=True)
    autor_principal = models.CharField(max_length=800, blank=True)
    email = models.CharField(max_length=150, blank=True)
    keywords = models.TextField(blank=True)
    keywords_en = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    abstract_en = models.TextField(blank=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=50, unique=True)
    info = models.TextField(blank=True)
    topic_id = models.IntegerField(null=True, blank=True)
    owner_id = models.IntegerField(null=True, blank=True)
    category_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="i")
    filename = models.CharField(max_length=950, blank=True)
    size = models.IntegerField(null=True, blank=True)
    format_id = models.IntegerField(null=True, blank=True)
    visits = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    remote = models.CharField(max_length=1, default="n")
    curso = models.CharField(max_length=100, blank=True)
    disciplina = models.CharField(max_length=100, blank=True)
    professor = models.CharField(max_length=100, blank=True)
    departamento = models.CharField(max_length=100, blank=True)
    typeinformation = models.IntegerField(null=True, blank=True)
    doi = models.CharField(max_length=180, blank=True)
    capa = models.CharField(max_length=65, blank=True)
    descricao_fisica = models.CharField(max_length=500, blank=True)
    acesso_eletronico = models.CharField(max_length=800, blank=True)
    source = models.CharField(max_length=900, blank=True)
    nlspi = models.CharField(max_length=200, blank=True)
    typeinform_id = models.IntegerField(null=True, blank=True)
    nota_versao_ori = models.CharField(max_length=1000, blank=True)
    tacesso = models.IntegerField(default=0)
    edicao = models.CharField(max_length=900, blank=True)
    event_description = models.CharField(max_length=5000, blank=True)
    avulso = models.CharField(max_length=1, default="n")
    view_document = models.CharField(max_length=1, default="0")
    dados_pesquisa = models.CharField(max_length=800, blank=True)

    # Campos customizados SGGD/LILP
    # Tipologia foi removida do modelo na taxonomia v6. A coluna física
    # `tipologia` é preservada no banco para o de-para v5→v6 (ver
    # docker/postgres/init/07-natureza.sql); apenas não é mais mapeada aqui.
    etapa_processo_licitatorio = models.CharField(max_length=255, blank=True)
    complexidade = models.CharField(max_length=50, blank=True)
    uso_futuro = models.TextField(blank=True)
    metodo = models.TextField(blank=True)
    resultado = models.TextField(blank=True)
    referencias = models.TextField(blank=True)
    publicacao = models.CharField(max_length=500, blank=True)

    # Taxonomia hierárquica (template BDLP_Template_Insercao)
    assunto_id = models.IntegerField(null=True, blank=True)
    subcategoria_id = models.IntegerField(null=True, blank=True)
    microcategoria_id = models.IntegerField(null=True, blank=True)
    ano = models.IntegerField(null=True, blank=True)
    PERMISSAO_CHOICES = [("Aberto", "Aberto"), ("Restrito", "Restrito")]
    permissao = models.CharField(max_length=20, blank=True, choices=PERMISSAO_CHOICES)
    # Natureza do objeto da contratação (v6, obrigatória na captura)
    natureza = models.CharField(max_length=80, blank=True, choices=NATUREZA_CHOICES)

    class Meta:
        managed = False
        db_table = "nr_document"

    def __str__(self):
        return self.title or f"Document #{self.pk}"

    @property
    def topic(self):
        if self.topic_id:
            return Topic.objects.filter(id=self.topic_id).first()
        return None

    @property
    def category(self):
        if self.category_id:
            return NrCategory.objects.filter(id=self.category_id).first()
        return None

    @property
    def format(self):
        if self.format_id:
            return NrFormat.objects.filter(id=self.format_id).first()
        return None

    @property
    def type_info(self):
        if self.typeinform_id:
            return TypeInformation.objects.filter(id=self.typeinform_id).first()
        return None

    @property
    def assunto(self):
        if self.assunto_id:
            return Assunto.objects.filter(id=self.assunto_id).first()
        return None

    @property
    def subcategoria(self):
        if self.subcategoria_id:
            return Subcategoria.objects.filter(id=self.subcategoria_id).first()
        return None

    @property
    def microcategoria(self):
        if self.microcategoria_id:
            return Microcategoria.objects.filter(id=self.microcategoria_id).first()
        return None

    @property
    def is_remote(self):
        return self.remote == "y"

    @property
    def is_archived(self):
        return self.status == "a"

    @property
    def display_authors(self):
        """Autores para exibição a partir de 'Autor Principal' (`author`), um por
        item (separador ';'), deduplicados por nome normalizado. Fonte canônica
        única — não cruza com 'Autoridade Intelectual' (`autor_principal`), o que
        eliminava a duplicação quando o mesmo autor vinha em formatos diferentes
        (ex.: 'Souza, R. de' × 'de Souza, R.'). Fallback para `autor_principal`
        só quando `author` está vazio."""
        bruto = (self.author or "").strip() or (self.autor_principal or "").strip()
        vistos, saida = set(), []
        for parte in bruto.split(";"):
            nome = parte.strip()
            chave = _author_key(nome)
            if nome and chave not in vistos:
                vistos.add(chave)
                saida.append(nome)
        return saida


class NrOds(models.Model):
    """Objetivos de Desenvolvimento Sustentável — mapeia tabela 'nr_ods'."""

    description = models.CharField(max_length=100)
    ordem = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = "nr_ods"

    def __str__(self):
        return self.description


class SupplementaryFile(models.Model):
    """Arquivos suplementares — mapeia tabela 'supplementary_files'."""

    filename = models.CharField(max_length=150)
    size = models.IntegerField(null=True)
    document_id = models.IntegerField()
    category_id = models.IntegerField()
    owner_id = models.IntegerField()
    format_id = models.IntegerField()
    remote = models.CharField(max_length=1, default="n")
    topic_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "supplementary_files"


class VisitasDownloads(models.Model):
    """Registro de visitas e downloads — mapeia tabela 'visitas_downloads'."""

    ip = models.CharField(max_length=15, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    code = models.CharField(max_length=50, blank=True)
    tipo = models.CharField(max_length=1, blank=True)
    topic_id = models.IntegerField(null=True)
    country = models.CharField(max_length=100, blank=True)
    user_id = models.IntegerField(null=True)
    origem = models.CharField(max_length=2, blank=True)
    idsf = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = "visitas_downloads"

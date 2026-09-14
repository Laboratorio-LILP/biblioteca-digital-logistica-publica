"""
Management command para validar a importação de dados.

Uso:
    python manage.py validate_import
"""

from django.core.management.base import BaseCommand
from django.db import connection

from catalog import qualidade
from catalog.taxonomy_v6 import COLECOES_V6, colecao_v6_for_tipo, tipo_canonico


class Command(BaseCommand):
    help = "Valida integridade dos dados importados no Nou-Rau"

    def handle(self, *args, **options):
        checks = [
            ("Documentos arquivados", "SELECT COUNT(*) FROM nr_document WHERE status = 'a'"),
            ("Documentos totais", "SELECT COUNT(*) FROM nr_document"),
            ("Coleções (raiz)", "SELECT COUNT(*) FROM topic WHERE parent_id = 0"),
            ("Subcoleções", "SELECT COUNT(*) FROM topic WHERE parent_id != 0"),
            ("Categorias", "SELECT COUNT(*) FROM nr_category"),
            ("Tipos de informação", "SELECT COUNT(*) FROM type_information"),
            ("Formatos", "SELECT COUNT(*) FROM nr_format"),
            ("Assuntos", "SELECT COUNT(*) FROM nr_assunto"),
            ("Subcategorias", "SELECT COUNT(*) FROM nr_subcategoria"),
            ("Microcategorias", "SELECT COUNT(*) FROM nr_microcategoria"),
            ("Documentos com assunto",
             "SELECT COUNT(*) FROM nr_document WHERE assunto_id IS NOT NULL AND status = 'a'"),
            ("Documentos com subcategoria",
             "SELECT COUNT(*) FROM nr_document WHERE subcategoria_id IS NOT NULL AND status = 'a'"),
            ("Documentos com microcategoria",
             "SELECT COUNT(*) FROM nr_document WHERE microcategoria_id IS NOT NULL AND status = 'a'"),
            ("Documentos com ano", "SELECT COUNT(*) FROM nr_document WHERE ano IS NOT NULL AND status = 'a'"),
            ("Documentos com permissão",
             "SELECT COUNT(*) FROM nr_document WHERE permissao IS NOT NULL AND permissao != '' AND status = 'a'"),
        ]

        self.stdout.write(self.style.SUCCESS("=== Validação de Importação ===\n"))

        with connection.cursor() as cursor:
            for label, sql in checks:
                cursor.execute(sql)
                count = cursor.fetchone()[0]
                self.stdout.write(f"  {label}: {count}")

        # Verificar documentos sem coleção
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM nr_document WHERE topic_id IS NULL AND status = 'a'")
            orphans = cursor.fetchone()[0]
            if orphans:
                self.stdout.write(self.style.WARNING(f"\n  Documentos sem coleção: {orphans}"))

            # Verificar documentos sem categoria
            cursor.execute("SELECT COUNT(*) FROM nr_document WHERE category_id IS NULL AND status = 'a'")
            no_cat = cursor.fetchone()[0]
            if no_cat:
                self.stdout.write(self.style.WARNING(f"  Documentos sem categoria: {no_cat}"))

            # Verificar códigos duplicados
            cursor.execute(
                "SELECT code, COUNT(*) FROM nr_document GROUP BY code HAVING COUNT(*) > 1"
            )
            dupes = cursor.fetchall()
            if dupes:
                self.stdout.write(self.style.ERROR(f"\n  Códigos duplicados: {len(dupes)}"))
                for code, count in dupes[:10]:
                    self.stdout.write(f"    {code}: {count}x")
            else:
                self.stdout.write(self.style.SUCCESS("\n  Sem códigos duplicados."))

            # Documentos por coleção v6 — derivada do Tipo de Informação com o
            # MESMO mapeamento do portal (colecao_v6_for_tipo); a árvore de
            # tópicos do Nou-Rau (topic) não reflete a coleção exibida.
            cursor.execute(
                """
                SELECT ti.name, COUNT(d.id)
                FROM nr_document d
                JOIN type_information ti ON ti.id = d.typeinform_id
                WHERE d.status = 'a'
                GROUP BY ti.name
                """
            )
            por_colecao = {c["nome"]: 0 for c in COLECOES_V6}
            for tipo_nome, count in cursor.fetchall():
                por_colecao[colecao_v6_for_tipo(tipo_nome)["nome"]] += count
            self.stdout.write("\n  Documentos por coleção:")
            for nome, count in por_colecao.items():
                self.stdout.write(f"    {nome}: {count}")
            cursor.execute(
                "SELECT COUNT(*) FROM nr_document WHERE typeinform_id IS NULL AND status = 'a'"
            )
            sem_tipo = cursor.fetchone()[0]
            if sem_tipo:
                self.stdout.write(self.style.WARNING(f"    (sem tipo de informação: {sem_tipo})"))

            # Taxonomia v12 — tipos em uso fora do vocabulário canônico (nome +
            # contagem): grafias legadas ("Acórdão") e tipos retirados
            # ("Documentos Normativos", "Vídeos") aparecem aqui.
            cursor.execute(
                """
                SELECT ti.name, COUNT(d.id)
                FROM nr_document d
                JOIN type_information ti ON ti.id = d.typeinform_id
                WHERE d.status = 'a'
                GROUP BY ti.name
                ORDER BY COUNT(d.id) DESC, ti.name
                """
            )
            fora = [(nome, n) for nome, n in cursor.fetchall() if tipo_canonico(nome) != nome]
            self.stdout.write("\n  Tipos de informação em uso fora do vocabulário canônico v12:")
            if fora:
                for nome, n in fora:
                    self.stdout.write(self.style.WARNING(f"    {nome}: {n}"))
            else:
                self.stdout.write("    nenhum")

            # Aviso explícito: documento ativo com tipo retirado (Documentos
            # Normativos, Vídeos) ou na subcoleção Enunciados sob Jurisprudência
            # — impede a seção 2 do script de migração de remover esses nós.
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM nr_document d
                LEFT JOIN type_information ti ON ti.id = d.typeinform_id
                LEFT JOIN topic t ON t.id = d.topic_id
                LEFT JOIN topic r ON r.id = t.parent_id
                WHERE d.status = 'a'
                  AND (ti.name IN ('Documentos Normativos', 'Vídeos')
                       OR (t.name = 'Enunciados' AND r.name = 'Jurisprudência'))
                """
            )
            retirados = cursor.fetchone()[0]
            if retirados:
                self.stdout.write(self.style.WARNING(
                    f"\n  AVISO v12: {retirados} documento(s) ativo(s) com tipo retirado da taxonomia "
                    "(Documentos Normativos/Vídeos) ou em Jurisprudência/Enunciados — recarregue o "
                    "acervo v12 antes da seção 2 do script de migração."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\n  Nenhum documento ativo com tipo retirado na v12 (Documentos Normativos/Vídeos/"
                    "Enunciados sob Jurisprudência)."
                ))

            # Contagem por subcoleção de Jurisprudência e de Doutrina (as duas
            # coleções que mudaram de vocabulário na v12).
            cursor.execute(
                """
                SELECT r.name, t.name, COUNT(d.id)
                FROM topic r
                JOIN topic t ON t.parent_id = r.id
                LEFT JOIN nr_document d ON d.topic_id = t.id AND d.status = 'a'
                WHERE r.parent_id = 0
                  AND r.name IN ('Jurisprudência', 'Doutrina e Conteúdo Técnico')
                GROUP BY r.name, t.name
                ORDER BY r.name, COUNT(d.id) DESC, t.name
                """
            )
            self.stdout.write("\n  Documentos por subcoleção (Jurisprudência e Doutrina):")
            for raiz, sub, n in cursor.fetchall():
                self.stdout.write(f"    {raiz} / {sub}: {n}")

            # Documentos por categoria
            cursor.execute(
                """
                SELECT c.name, COUNT(d.id)
                FROM nr_category c
                LEFT JOIN nr_document d ON d.category_id = c.id AND d.status = 'a'
                GROUP BY c.name
                ORDER BY COUNT(d.id) DESC
                """
            )
            self.stdout.write("\n  Documentos por categoria:")
            for name, count in cursor.fetchall():
                self.stdout.write(f"    {name}: {count}")

            # Documentos por assunto — TODOS os assuntos do seed (LEFT JOIN), na
            # ordem canônica, inclusive os dois novos da v12 ainda com zero.
            cursor.execute(
                """
                SELECT a.nome, COUNT(d.id)
                FROM nr_assunto a
                LEFT JOIN nr_document d ON d.assunto_id = a.id AND d.status = 'a'
                GROUP BY a.id, a.nome, a.ordem
                ORDER BY a.ordem, a.nome
                """
            )
            rows_assunto = cursor.fetchall()
            self.stdout.write(f"\n  Documentos por assunto ({len(rows_assunto)} assuntos no seed):")
            for name, count in rows_assunto:
                self.stdout.write(f"    {name}: {count}")

            # Distribuição por permissão
            cursor.execute(
                """
                SELECT COALESCE(permissao, '(vazio)') AS perm, COUNT(*)
                FROM nr_document
                WHERE status = 'a'
                GROUP BY perm
                ORDER BY perm
                """
            )
            self.stdout.write("\n  Documentos por permissão:")
            for perm, count in cursor.fetchall():
                self.stdout.write(f"    {perm}: {count}")

            # Documentos por ano (top 10)
            cursor.execute(
                """
                SELECT ano, COUNT(*)
                FROM nr_document
                WHERE status = 'a' AND ano IS NOT NULL
                GROUP BY ano
                ORDER BY ano DESC
                LIMIT 10
                """
            )
            self.stdout.write("\n  Documentos por ano (top 10 mais recentes):")
            for ano, count in cursor.fetchall():
                self.stdout.write(f"    {ano}: {count}")

            # Documentos sem ano
            cursor.execute(
                "SELECT COUNT(*) FROM nr_document WHERE ano IS NULL AND status = 'a'"
            )
            sem_ano = cursor.fetchone()[0]
            if sem_ano:
                self.stdout.write(self.style.WARNING(f"\n  Documentos sem ano: {sem_ano}"))

            # Possíveis redundâncias e problemas de qualidade (catalog.qualidade,
            # só relatório): duplicatas, endereços compartilhados, resumos suspeitos,
            # autoria de série. Insumo da curadoria — nada é alterado.
            cursor.execute(
                """
                SELECT d.code, d.title, d.doi, d.acesso_eletronico, d.abstract,
                       r.name, ti.name, a.nome, c.name, s.nome, d.author
                FROM nr_document d
                LEFT JOIN topic t ON t.id = d.topic_id
                LEFT JOIN topic r ON r.id = CASE WHEN t.parent_id = 0 THEN t.id ELSE t.parent_id END
                LEFT JOIN type_information ti ON ti.id = d.typeinform_id
                LEFT JOIN nr_assunto a ON a.id = d.assunto_id
                LEFT JOIN nr_category c ON c.id = d.category_id
                LEFT JOIN nr_subcategoria s ON s.id = d.subcategoria_id
                WHERE d.status = 'a'
                ORDER BY d.id
                """
            )
            registros = [
                qualidade.registro(
                    code, title, doi=doi, url=url, resumo=resumo, colecao=colecao, tipo=tipo,
                    assunto=assunto, categoria=categoria, subcategoria=subcategoria, autor=autor,
                )
                for code, title, doi, url, resumo, colecao, tipo, assunto, categoria, subcategoria, autor
                in cursor.fetchall()
            ]
            achados = qualidade.analisar(registros)
            self.stdout.write(
                f"\n  Possíveis redundâncias e problemas de qualidade "
                f"({len(achados)} achados em {len(registros)} documentos; semântica em catalog/qualidade.py):"
            )
            for linha in qualidade.formatar_relatorio(achados, limite=5):
                self.stdout.write(linha)

        self.stdout.write(self.style.SUCCESS("\n=== Validação concluída ==="))

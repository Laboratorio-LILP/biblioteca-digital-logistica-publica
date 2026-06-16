"""
Management command para validar a importação de dados.

Uso:
    python manage.py validate_import
"""

from django.core.management.base import BaseCommand
from django.db import connection


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

            # Documentos por coleção
            cursor.execute(
                """
                SELECT t.name, COUNT(d.id)
                FROM topic t
                LEFT JOIN nr_document d ON d.topic_id = t.id AND d.status = 'a'
                WHERE t.parent_id = 0
                GROUP BY t.name
                ORDER BY t.name
                """
            )
            self.stdout.write("\n  Documentos por coleção:")
            for name, count in cursor.fetchall():
                self.stdout.write(f"    {name}: {count}")

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

            # Documentos por assunto
            cursor.execute(
                """
                SELECT a.nome, COUNT(d.id)
                FROM nr_assunto a
                LEFT JOIN nr_document d ON d.assunto_id = a.id AND d.status = 'a'
                GROUP BY a.nome
                ORDER BY COUNT(d.id) DESC
                """
            )
            self.stdout.write("\n  Documentos por assunto:")
            for name, count in cursor.fetchall():
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

        self.stdout.write(self.style.SUCCESS("\n=== Validação concluída ==="))

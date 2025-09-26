import os
import subprocess
from django.core.management.base import BaseCommand
from decouple import config
import psycopg2

class Command(BaseCommand):
    help = "Importe les couches GeoJSON et crée un index spatial"

    def handle(self, *args, **kwargs):
        # Params DB depuis .env
        db = config("DATABASE_NAME", default="andp_db")
        user = config("DATABASE_USER", default="postgres")
        password = config("DATABASE_PASSWORD", default="")
        host = config("DATABASE_HOST", default="localhost")
        port = config("DATABASE_PORT", default="5432")

        couche_dir = os.path.join(os.getcwd(), "couche")
        if not os.path.exists(couche_dir):
            self.stdout.write(self.style.ERROR(f"Dossier {couche_dir} introuvable"))
            return

        # Connexion à Postgres pour créer les index
        conn = psycopg2.connect(dbname=db, user=user, password=password, host=host, port=port)
        cur = conn.cursor()

        for file in os.listdir(couche_dir):
            if file.endswith(".geojson"):
                table = os.path.splitext(file)[0].replace(" ", "_")
                filepath = os.path.join(couche_dir, file)

                # Import GeoJSON
                cmd = [
                    "ogr2ogr",
                    "-f", "PostgreSQL",
                    f"PG:dbname={db} user={user} password={password} host={host} port={port}",
                    filepath,
                    "-nln", table,
                    "-nlt", "PROMOTE_TO_MULTI",
                    "-lco", "GEOMETRY_NAME=geom",
                    "-overwrite",
                ]
                subprocess.run(cmd, check=True)
                self.stdout.write(self.style.SUCCESS(f"{file} importé dans {table}"))

                # Créer l'index spatial
                index_name = f"{table}_geom_idx"
                cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING GIST (geom);")
                self.stdout.write(self.style.SUCCESS(f"Index spatial {index_name} créé"))

        conn.commit()
        cur.close()
        conn.close()

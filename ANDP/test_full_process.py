#!/usr/bin/env python3
"""
Test du processus complet pour leve3.jpg
"""

import os
import sys
import tempfile

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.models import PublicUpload
from ANDP_app.services.ocr_integration import OCRSpatialIntegrator

def test_full_process():
    """Test du processus complet"""

    print("🔍 TEST PROCESSUS COMPLET - leve3.jpg")
    print("="*50)

    file_path = "Testing Data/leve3.jpg"

    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return

    try:
        # Créer un upload
        with open(file_path, 'rb') as f:
            upload = PublicUpload.objects.create(
                file=f,
                original_filename="leve3.jpg"
            )

        print(f"✅ Upload créé: {upload.id}")

        # Lancer le processus complet
        integrator = OCRSpatialIntegrator()
        result = integrator.process_upload_complete(upload)

        print("✅ PROCESSUS RÉUSSI!")
        print(f"Résultat: {result.keys()}")

        return result

    except Exception as e:
        print(f"❌ ERREUR: {str(e)}")
        print(f"Type: {type(e).__name__}")

        # Plus de détails sur l'erreur
        import traceback
        traceback.print_exc()

        return None

if __name__ == "__main__":
    result = test_full_process()

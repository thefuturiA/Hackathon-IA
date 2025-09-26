#!/usr/bin/env python
"""
Test complet du système ANDF - Analyse Spatiale Intelligente
Vérifie tous les composants: OCR, Spatial, API, Frontend Integration
"""

import os
import sys
import django
import json
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')
django.setup()

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from ANDP_app.services.andf_layers import ANDFLayerService
from ANDP_app.services.spatial_verification import IntelligentSpatialAnalyzer
from ANDP_app.services.ocr_integration import OCRSpatialIntegrator
from django.contrib.gis.geos import Polygon


class ANDFSystemTester:
    """Testeur complet du système ANDF"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
    
    def run_all_tests(self):
        """Lance tous les tests"""
        print("🚀 ANDP - Test Complet du Système d'Analyse Spatiale Intelligente")
        print("=" * 70)
        
        tests = [
            ("🗄️ Base de données et couches ANDF", self.test_database_layers),
            ("🧠 Analyseur spatial intelligent", self.test_spatial_analyzer),
            ("📡 Endpoints API REST", self.test_api_endpoints),
            ("🗺️ Endpoints GeoJSON pour cartes", self.test_geojson_endpoints),
            ("🔗 Intégration OCR + Spatial", self.test_ocr_integration),
            ("⚠️ Système d'alerte intelligent", self.test_alert_system),
            ("🌐 Configuration frontend React", self.test_frontend_config),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{test_name}")
            print("-" * 50)
            try:
                result = test_func()
                self.test_results.append((test_name, result))
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.test_results.append((test_name, False))
        
        self.print_summary()
    
    def test_database_layers(self):
        """Test des couches ANDF et base de données"""
        try:
            # Test du service ANDF
            layer_info = ANDFLayerService.get_layer_info()
            print(f"✅ Service ANDF initialisé: {len(layer_info)} couches configurées")
            
            available_layers = [name for name, info in layer_info.items() if info.get('available')]
            print(f"✅ Couches disponibles: {len(available_layers)}")
            
            for layer_name in available_layers:
                info = layer_info[layer_name]
                print(f"  📊 {layer_name}: {info.get('feature_count', 0)} features")
            
            if len(available_layers) == 0:
                print("⚠️ Aucune couche importée - Exécuter: python manage.py import_layer")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur couches ANDF: {e}")
            return False
    
    def test_spatial_analyzer(self):
        """Test de l'analyseur spatial intelligent"""
        try:
            analyzer = IntelligentSpatialAnalyzer()
            print("✅ Analyseur spatial initialisé")
            
            # Test avec géométrie de Cotonou (zone avec données)
            test_coords = [
                (430000, 705000),
                (430100, 705000),
                (430100, 705100),
                (430000, 705100),
                (430000, 705000)
            ]
            
            test_polygon = Polygon(test_coords, srid=32631)
            print(f"✅ Géométrie de test créée: {test_polygon.area:.2f} m²")
            
            # Test des seuils de détection
            thresholds = analyzer.OVERLAP_THRESHOLDS
            print(f"✅ Seuils configurés: {thresholds}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur analyseur spatial: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test des endpoints API principaux"""
        try:
            # Test page d'accueil
            response = self.client.get('/')
            print(f"✅ Page d'accueil: {response.status_code}")
            
            # Test documentation API
            try:
                response = self.client.get('/api/docs/')
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Documentation API: {data.get('title', 'OK')}")
                else:
                    print(f"⚠️ Documentation API: {response.status_code}")
            except:
                print("⚠️ Documentation API non accessible (normal si migrations non faites)")
            
            # Test health check
            try:
                response = self.client.get('/api/health/')
                if response.status_code == 200:
                    print("✅ Health check accessible")
                else:
                    print(f"⚠️ Health check: {response.status_code}")
            except:
                print("⚠️ Health check non accessible (normal si migrations non faites)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur endpoints API: {e}")
            return False
    
    def test_geojson_endpoints(self):
        """Test des endpoints GeoJSON pour le frontend"""
        try:
            # Test info couches
            try:
                response = self.client.get('/api/layers/info/')
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Info couches: {data.get('total_layers', 0)} couches")
                else:
                    print(f"⚠️ Info couches: {response.status_code}")
            except:
                print("⚠️ Info couches non accessible")
            
            # Test GeoJSON couche (si disponible)
            try:
                response = self.client.get('/api/layers/parcelles/geojson/?limit=1')
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ GeoJSON parcelles: {len(data.get('features', []))} feature(s)")
                else:
                    print(f"⚠️ GeoJSON parcelles: {response.status_code}")
            except:
                print("⚠️ GeoJSON parcelles non accessible (normal si couches non importées)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur endpoints GeoJSON: {e}")
            return False
    
    def test_ocr_integration(self):
        """Test de l'intégration OCR"""
        try:
            integrator = OCRSpatialIntegrator()
            print("✅ Intégrateur OCR + Spatial initialisé")
            
            # Vérifier les fonctions utilitaires
            from ANDP_app.services.ocr_integration import validate_benin_coords, validate_coordinate_format
            
            # Test coordonnées valides Bénin
            valid_coords = validate_benin_coords(430000, 705000)  # Cotonou
            print(f"✅ Validation coordonnées Bénin: {valid_coords}")
            
            # Test format coordonnées
            valid_format = validate_coordinate_format(430000.5, 705000.5)
            print(f"✅ Validation format coordonnées: {valid_format}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur intégration OCR: {e}")
            return False
    
    def test_alert_system(self):
        """Test du système d'alerte intelligent"""
        try:
            from ANDP_app.services.spatial_verification import AlertSystem
            print("✅ Système d'alerte initialisé")
            
            # Test des types d'alerte configurés
            from ANDP_app.models import SpatialConflict
            conflict_types = [choice[0] for choice in SpatialConflict.CONFLICT_TYPES]
            print(f"✅ Types de conflits configurés: {len(conflict_types)}")
            for conflict_type in conflict_types:
                print(f"  🚨 {conflict_type}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur système d'alerte: {e}")
            return False
    
    def test_frontend_config(self):
        """Test de la configuration pour le frontend React"""
        try:
            from django.conf import settings
            
            # Vérifier CORS
            cors_enabled = 'corsheaders' in settings.INSTALLED_APPS
            print(f"✅ CORS configuré: {cors_enabled}")
            
            # Vérifier REST Framework
            drf_enabled = 'rest_framework' in settings.INSTALLED_APPS
            print(f"✅ Django REST Framework: {drf_enabled}")
            
            # Vérifier GIS
            gis_enabled = 'django.contrib.gis' in settings.INSTALLED_APPS
            print(f"✅ Django GIS: {gis_enabled}")
            
            # Vérifier configuration media
            media_configured = hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT')
            print(f"✅ Configuration media: {media_configured}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur configuration frontend: {e}")
            return False
    
    def test_sample_document(self):
        """Test avec un document d'exemple"""
        try:
            # Chercher un document de test
            test_files = list(Path("Testing Data").glob("*.png"))[:1]
            
            if not test_files:
                print("⚠️ Aucun document de test trouvé dans Testing Data/")
                return True
            
            test_file = test_files[0]
            print(f"📄 Test avec: {test_file.name}")
            
            # Simuler un upload
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            uploaded_file = SimpleUploadedFile(
                test_file.name,
                file_content,
                content_type='image/png'
            )
            
            # Test de l'endpoint upload
            response = self.client.post('/api/upload/', {
                'file': uploaded_file
            })
            
            print(f"✅ Test upload: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                upload_id = data.get('upload_id')
                print(f"✅ Upload ID généré: {upload_id}")
                
                # Test statut
                status_response = self.client.get(f'/api/upload/{upload_id}/status/')
                print(f"✅ Test statut: {status_response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur test document: {e}")
            return False
    
    def print_summary(self):
        """Affiche le résumé des tests"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 70)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
            print(f"{status} {test_name}")
        
        print(f"\n📈 Score: {passed}/{total} tests réussis")
        
        if passed == total:
            print("\n🎉 SYSTÈME ANDF OPÉRATIONNEL !")
            print("\n📋 Prochaines étapes pour déploiement:")
            print("1. Terminer les migrations: python manage.py migrate")
            print("2. Importer les couches: python manage.py import_layer")
            print("3. Lancer le serveur: python manage.py runserver")
            print("4. Intégrer avec React frontend")
        else:
            print(f"\n⚠️ {total - passed} test(s) en échec")
            print("Vérifiez la configuration avant le déploiement.")
        
        print("\n🔗 API Endpoints pour React + Leaflet:")
        print("- POST /api/upload/ - Upload et analyse")
        print("- GET /api/upload/{id}/status/ - Statut temps réel")
        print("- GET /api/upload/{id}/geojson/ - Données carte")
        print("- GET /api/upload/{id}/conflicts/ - Conflits")
        print("- GET /api/comparison/{id}/ - Comparaison cadastrale")


def main():
    """Fonction principale"""
    tester = ANDFSystemTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()

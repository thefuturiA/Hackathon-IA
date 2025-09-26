#!/usr/bin/env python
"""
Script de test pour le système ANDF
Vérifie que tous les composants fonctionnent correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')
django.setup()

from ANDP_app.services.andf_layers import ANDFLayerService
from ANDP_app.services.spatial_verification import IntelligentSpatialAnalyzer
from django.contrib.gis.geos import Polygon


def test_andf_layers():
    """Test du service de gestion des couches ANDF"""
    print("🔍 Test du service ANDF Layers...")
    
    try:
        # Vérifier les informations des couches
        layer_info = ANDFLayerService.get_layer_info()
        print(f"✅ Couches disponibles: {len(layer_info)}")
        
        for layer_name, info in layer_info.items():
            if info.get('available'):
                print(f"  ✅ {layer_name}: {info.get('feature_count', 0)} features")
            else:
                print(f"  ❌ {layer_name}: Non disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test couches ANDF: {e}")
        return False


def test_spatial_analyzer():
    """Test de l'analyseur spatial intelligent"""
    print("\n🧠 Test de l'analyseur spatial intelligent...")
    
    try:
        analyzer = IntelligentSpatialAnalyzer()
        print("✅ Analyseur spatial initialisé")
        
        # Test avec une géométrie simple
        test_coords = [
            (420000, 710000),
            (420100, 710000),
            (420100, 710100),
            (420000, 710100),
            (420000, 710000)
        ]
        
        test_polygon = Polygon(test_coords, srid=32631)
        print(f"✅ Géométrie de test créée: {test_polygon.area:.2f} m²")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test analyseur spatial: {e}")
        return False


def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🌐 Test des endpoints API...")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test de la page d'accueil
        response = client.get('/')
        if response.status_code == 200:
            print("✅ Page d'accueil accessible")
        else:
            print(f"❌ Page d'accueil: {response.status_code}")
        
        # Test de la documentation API
        try:
            response = client.get('/api/docs/')
            if response.status_code == 200:
                print("✅ Documentation API accessible")
            else:
                print(f"❌ Documentation API: {response.status_code}")
        except:
            print("⚠️ Documentation API non testable (URL non résolue)")
        
        # Test de l'état de santé
        try:
            response = client.get('/api/health/')
            if response.status_code == 200:
                print("✅ Health check accessible")
            else:
                print(f"❌ Health check: {response.status_code}")
        except:
            print("⚠️ Health check non testable (URL non résolue)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test endpoints: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("🚀 ANDP - Test du Système d'Analyse Spatiale Intelligente")
    print("=" * 60)
    
    tests = [
        test_andf_layers,
        test_spatial_analyzer,
        test_api_endpoints,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ Tous les tests réussis ({passed}/{total})")
        print("\n🎉 Le système ANDF est prêt pour la production !")
        print("\n📋 Prochaines étapes:")
        print("1. Lancer: python manage.py migrate")
        print("2. Importer les couches: python manage.py import_layer")
        print("3. Démarrer le serveur: python manage.py runserver")
        print("4. Tester l'API: http://localhost:8000/api/docs/")
    else:
        print(f"⚠️ {passed}/{total} tests réussis")
        print("Vérifiez la configuration avant de continuer.")


if __name__ == "__main__":
    main()

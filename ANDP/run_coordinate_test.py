#!/usr/bin/env python3
"""
Script simple pour tester l'extraction de coordonnées sur les données de test
"""

import os
import sys
import time
from datetime import datetime

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def test_coordinate_extraction():
    """Test l'extraction de coordonnées sur quelques fichiers de test"""
    
    print("🧪 TEST D'EXTRACTION DE COORDONNÉES - DONNÉES DE TEST")
    print("="*60)
    
    # Initialiser l'extracteur
    extractor = HybridOCRCorrector()
    
    # Obtenir les fichiers de test
    testing_data_path = "Testing Data"
    if not os.path.exists(testing_data_path):
        print(f"❌ Dossier {testing_data_path} non trouvé")
        return
    
    # Prendre les 10 premiers fichiers pour le test
    test_files = []
    for filename in sorted(os.listdir(testing_data_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            test_files.append(os.path.join(testing_data_path, filename))
            if len(test_files) >= 10:  # Limiter à 10 fichiers pour le test
                break
    
    print(f"📁 Fichiers à tester: {len(test_files)}")
    print(f"⏰ Début du test: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    results = []
    total_start_time = time.time()
    
    for i, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        print(f"[{i:2d}/{len(test_files)}] 🔍 Test: {filename}")
        
        start_time = time.time()
        try:
            # Extraction des coordonnées
            coordinates = extractor.extract_coordinates(file_path)
            extraction_time = time.time() - start_time
            
            result = {
                'file': filename,
                'coordinates': coordinates,
                'count': len(coordinates),
                'time': round(extraction_time, 2),
                'status': 'success' if coordinates else 'no_coords'
            }
            
            # Affichage des résultats
            if coordinates:
                print(f"   ✅ {len(coordinates)} coordonnées trouvées ({extraction_time:.2f}s):")
                for coord in coordinates:
                    is_valid = extractor.validate_coordinates(coord['x'], coord['y'])
                    status = "✅" if is_valid else "❌"
                    print(f"      {coord['borne']}: X={coord['x']:>10.2f}, Y={coord['y']:>10.2f} {status}")
                
                # Test de fermeture du polygone
                if len(coordinates) >= 3:
                    is_closed = extractor.is_polygon_closed(coordinates)
                    print(f"   📐 Polygone fermé: {'✅' if is_closed else '❌'}")
            else:
                print(f"   ❌ Aucune coordonnée trouvée ({extraction_time:.2f}s)")
                
        except Exception as e:
            extraction_time = time.time() - start_time
            print(f"   🚨 Erreur: {str(e)} ({extraction_time:.2f}s)")
            result = {
                'file': filename,
                'coordinates': [],
                'count': 0,
                'time': round(extraction_time, 2),
                'status': 'error',
                'error': str(e)
            }
        
        results.append(result)
        print()
    
    # Analyse des résultats
    total_time = time.time() - total_start_time
    successful = len([r for r in results if r['count'] > 0])
    total_coords = sum(r['count'] for r in results)
    
    print("="*60)
    print("📊 RÉSUMÉ DES RÉSULTATS")
    print("="*60)
    print(f"📁 Fichiers testés: {len(results)}")
    print(f"✅ Extractions réussies: {successful}")
    print(f"📈 Taux de réussite: {(successful/len(results)*100):.1f}%")
    print(f"📍 Total coordonnées: {total_coords}")
    print(f"📊 Moyenne par fichier: {(total_coords/len(results)):.1f}")
    print(f"⏱️  Temps total: {total_time:.2f}s")
    print(f"⚡ Temps moyen/fichier: {(total_time/len(results)):.2f}s")
    
    # Distribution par nombre de coordonnées
    print(f"\n📋 Distribution:")
    coord_counts = {}
    for result in results:
        count = result['count']
        coord_counts[count] = coord_counts.get(count, 0) + 1
    
    for count in sorted(coord_counts.keys(), reverse=True):
        files_count = coord_counts[count]
        print(f"   {count:2d} coords: {files_count:2d} fichiers")
    
    # Fichiers sans coordonnées
    no_coords = [r['file'] for r in results if r['count'] == 0]
    if no_coords:
        print(f"\n❌ Fichiers sans coordonnées:")
        for filename in no_coords:
            print(f"   - {filename}")
    
    print(f"\n✅ Test terminé!")
    return results

if __name__ == "__main__":
    test_coordinate_extraction()

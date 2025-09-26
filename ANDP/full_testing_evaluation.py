#!/usr/bin/env python3
"""
Évaluation complète de l'extraction de coordonnées sur toutes les données de test
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def run_full_evaluation():
    """Évaluation complète sur tous les fichiers de test"""
    
    print("🧪 ÉVALUATION COMPLÈTE - EXTRACTION DE COORDONNÉES")
    print("="*60)
    
    # Initialiser l'extracteur
    extractor = HybridOCRCorrector()
    
    # Obtenir tous les fichiers de test
    testing_data_path = "Testing Data"
    if not os.path.exists(testing_data_path):
        print(f"❌ Dossier {testing_data_path} non trouvé")
        return
    
    test_files = []
    for filename in sorted(os.listdir(testing_data_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            test_files.append(os.path.join(testing_data_path, filename))
    
    print(f"📁 Total fichiers à tester: {len(test_files)}")
    print(f"⏰ Début de l'évaluation: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    results = []
    total_start_time = time.time()
    
    for i, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        
        # Affichage du progrès
        if i % 10 == 1 or i <= 10:
            print(f"[{i:3d}/{len(test_files)}] 🔍 {filename}")
        elif i % 10 == 0:
            print(f"[{i:3d}/{len(test_files)}] ✅ Traité 10 fichiers...")
        
        start_time = time.time()
        try:
            # Extraction des coordonnées
            coordinates = extractor.extract_coordinates(file_path)
            extraction_time = time.time() - start_time
            
            # Validation des coordonnées
            valid_coords = []
            invalid_coords = []
            for coord in coordinates:
                if extractor.validate_coordinates(coord['x'], coord['y']):
                    valid_coords.append(coord)
                else:
                    invalid_coords.append(coord)
            
            # Test de fermeture du polygone
            polygon_closed = False
            if len(valid_coords) >= 3:
                polygon_closed = extractor.is_polygon_closed(valid_coords)
            
            result = {
                'file': filename,
                'path': file_path,
                'total_coordinates': len(coordinates),
                'valid_coordinates': len(valid_coords),
                'invalid_coordinates': len(invalid_coords),
                'coordinates': coordinates,
                'extraction_time': round(extraction_time, 2),
                'polygon_closed': polygon_closed,
                'status': 'success' if coordinates else 'no_coords',
                'timestamp': datetime.now().isoformat()
            }
            
            # Affichage détaillé pour les premiers fichiers
            if i <= 10:
                if coordinates:
                    print(f"   ✅ {len(coordinates)} coords ({len(valid_coords)} valides) - {extraction_time:.2f}s")
                    if polygon_closed:
                        print(f"   📐 Polygone fermé: ✅")
                else:
                    print(f"   ❌ Aucune coordonnée - {extraction_time:.2f}s")
                    
        except Exception as e:
            extraction_time = time.time() - start_time
            result = {
                'file': filename,
                'path': file_path,
                'total_coordinates': 0,
                'valid_coordinates': 0,
                'invalid_coordinates': 0,
                'coordinates': [],
                'extraction_time': round(extraction_time, 2),
                'polygon_closed': False,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            if i <= 10:
                print(f"   🚨 Erreur: {str(e)} - {extraction_time:.2f}s")
        
        results.append(result)
    
    # Analyse complète des résultats
    total_time = time.time() - total_start_time
    analyze_complete_results(results, total_time)
    
    # Sauvegarde des résultats
    save_complete_results(results, total_time)
    
    return results

def analyze_complete_results(results: List[Dict], total_time: float):
    """Analyse complète des résultats"""
    
    print(f"\n{'='*80}")
    print(f"📊 ANALYSE COMPLÈTE DES RÉSULTATS")
    print(f"{'='*80}")
    
    # Statistiques générales
    total_files = len(results)
    successful_extractions = len([r for r in results if r['total_coordinates'] > 0])
    failed_extractions = len([r for r in results if r['status'] == 'error'])
    no_coords = len([r for r in results if r['total_coordinates'] == 0 and r['status'] != 'error'])
    
    total_coordinates = sum(r['total_coordinates'] for r in results)
    total_valid_coordinates = sum(r['valid_coordinates'] for r in results)
    total_invalid_coordinates = sum(r['invalid_coordinates'] for r in results)
    
    closed_polygons = len([r for r in results if r['polygon_closed']])
    
    print(f"📁 Total fichiers: {total_files}")
    print(f"✅ Extractions réussies: {successful_extractions} ({(successful_extractions/total_files*100):.1f}%)")
    print(f"❌ Échecs: {failed_extractions} ({(failed_extractions/total_files*100):.1f}%)")
    print(f"⚪ Sans coordonnées: {no_coords} ({(no_coords/total_files*100):.1f}%)")
    print(f"📍 Total coordonnées: {total_coordinates}")
    print(f"✅ Coordonnées valides: {total_valid_coordinates} ({(total_valid_coordinates/total_coordinates*100 if total_coordinates > 0 else 0):.1f}%)")
    print(f"❌ Coordonnées invalides: {total_invalid_coordinates}")
    print(f"📐 Polygones fermés: {closed_polygons} ({(closed_polygons/total_files*100):.1f}%)")
    print(f"📊 Moyenne coords/fichier: {(total_coordinates/total_files):.1f}")
    print(f"⏱️  Temps total: {total_time:.2f}s")
    print(f"⚡ Temps moyen/fichier: {(total_time/total_files):.2f}s")
    
    # Distribution par nombre de coordonnées
    print(f"\n📋 Distribution par nombre de coordonnées:")
    coord_distribution = {}
    for result in results:
        count = result['total_coordinates']
        coord_distribution[count] = coord_distribution.get(count, 0) + 1
    
    for count in sorted(coord_distribution.keys(), reverse=True):
        files_count = coord_distribution[count]
        percentage = (files_count / total_files) * 100
        print(f"   {count:2d} coords: {files_count:3d} fichiers ({percentage:5.1f}%)")
    
    # Top 10 des meilleures extractions
    best_extractions = sorted([r for r in results if r['total_coordinates'] > 0], 
                             key=lambda x: x['total_coordinates'], reverse=True)[:10]
    
    if best_extractions:
        print(f"\n🏆 Top 10 des meilleures extractions:")
        for i, result in enumerate(best_extractions, 1):
            valid_ratio = f"({result['valid_coordinates']}/{result['total_coordinates']})"
            closed_status = "🔒" if result['polygon_closed'] else ""
            print(f"   {i:2d}. {result['file']}: {result['total_coordinates']} coords {valid_ratio} {closed_status}")
    
    # Fichiers problématiques
    problem_files = [r for r in results if r['status'] == 'error']
    if problem_files:
        print(f"\n🚨 Fichiers avec erreurs ({len(problem_files)}):")
        for result in problem_files[:10]:
            print(f"   - {result['file']}: {result.get('error', 'Erreur inconnue')}")
    
    # Fichiers sans coordonnées
    no_coord_files = [r for r in results if r['total_coordinates'] == 0 and r['status'] != 'error']
    if no_coord_files:
        print(f"\n⚪ Fichiers sans coordonnées ({len(no_coord_files)}):")
        for result in no_coord_files[:10]:
            print(f"   - {result['file']} ({result['extraction_time']}s)")
        if len(no_coord_files) > 10:
            print(f"   ... et {len(no_coord_files) - 10} autres")

def save_complete_results(results: List[Dict], total_time: float):
    """Sauvegarde les résultats complets"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"complete_testing_results_{timestamp}.json"
    
    # Statistiques pour le fichier JSON
    total_files = len(results)
    successful_extractions = len([r for r in results if r['total_coordinates'] > 0])
    total_coordinates = sum(r['total_coordinates'] for r in results)
    total_valid_coordinates = sum(r['valid_coordinates'] for r in results)
    closed_polygons = len([r for r in results if r['polygon_closed']])
    
    data = {
        'metadata': {
            'test_date': datetime.now().isoformat(),
            'testing_data_path': "Testing Data",
            'total_files': total_files,
            'total_time': round(total_time, 2),
            'system': 'HybridOCRCorrector with PaddleOCR + Tesseract'
        },
        'summary': {
            'successful_extractions': successful_extractions,
            'success_rate': round((successful_extractions/total_files*100), 2),
            'total_coordinates': total_coordinates,
            'total_valid_coordinates': total_valid_coordinates,
            'validation_rate': round((total_valid_coordinates/total_coordinates*100 if total_coordinates > 0 else 0), 2),
            'closed_polygons': closed_polygons,
            'polygon_closure_rate': round((closed_polygons/total_files*100), 2),
            'avg_coordinates_per_file': round((total_coordinates/total_files), 2),
            'avg_time_per_file': round((total_time/total_files), 2)
        },
        'results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats complets sauvegardés dans: {output_file}")
    return output_file

if __name__ == "__main__":
    print("⚠️  ATTENTION: Ce test va traiter tous les fichiers de Testing Data")
    print("   Cela peut prendre plusieurs minutes...")
    
    response = input("\n❓ Continuer? (y/N): ").strip().lower()
    if response == 'y':
        run_full_evaluation()
    else:
        print("👋 Test annulé")

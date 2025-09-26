#!/usr/bin/env python3
"""
Test de validation avec les coordonnées de référence exactes pour leve212.png
"""

import os
import sys
import time
import math

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector
from ultimate_final_extractor import UltimateFinalExtractor

# Coordonnées de référence exactes pour leve212.png
REFERENCE_COORDS = {
    'B1': {'x': 392935.09, 'y': 699309.99},
    'B2': {'x': 392930.77, 'y': 699294.66},
    'B3': {'x': 392919.76, 'y': 699249.80},
    'B4': {'x': 392871.22, 'y': 699271.92},
    'B5': {'x': 392873.34, 'y': 699293.50},
    'B6': {'x': 392874.36, 'y': 699299.80},
    'B7': {'x': 392915.99, 'y': 699294.09},
    'B8': {'x': 392925.48, 'y': 699293.90}
}

def calculate_distance(coord1, coord2):
    """Calcule la distance euclidienne entre deux coordonnées"""
    return math.sqrt((coord1['x'] - coord2['x'])**2 + (coord1['y'] - coord2['y'])**2)

def evaluate_extraction_accuracy(extracted_coords, reference_coords, tolerance=5.0):
    """Évalue la précision de l'extraction par rapport aux coordonnées de référence"""
    
    results = {
        'total_reference': len(reference_coords),
        'total_extracted': len(extracted_coords),
        'matches': [],
        'missing': [],
        'extra': [],
        'accuracy_stats': {}
    }
    
    # Convertir les coordonnées extraites en dictionnaire
    extracted_dict = {}
    for coord in extracted_coords:
        extracted_dict[coord['borne']] = {'x': coord['x'], 'y': coord['y']}
    
    # Analyser chaque borne de référence
    distances = []
    for borne, ref_coord in reference_coords.items():
        if borne in extracted_dict:
            ext_coord = extracted_dict[borne]
            distance = calculate_distance(ref_coord, ext_coord)
            distances.append(distance)
            
            match_info = {
                'borne': borne,
                'reference': ref_coord,
                'extracted': ext_coord,
                'distance': distance,
                'accurate': distance <= tolerance
            }
            results['matches'].append(match_info)
        else:
            results['missing'].append(borne)
    
    # Identifier les bornes extraites en trop
    for borne in extracted_dict.keys():
        if borne not in reference_coords:
            results['extra'].append(borne)
    
    # Calculer les statistiques de précision
    if distances:
        results['accuracy_stats'] = {
            'mean_distance': sum(distances) / len(distances),
            'max_distance': max(distances),
            'min_distance': min(distances),
            'accurate_count': len([d for d in distances if d <= tolerance]),
            'accuracy_rate': (len([d for d in distances if d <= tolerance]) / len(distances)) * 100
        }
    
    return results

def test_leve212_with_reference():
    """Test complet de leve212.png avec validation par rapport aux coordonnées de référence"""
    
    print("🎯 TEST DE VALIDATION AVEC COORDONNÉES DE RÉFÉRENCE - leve212.png")
    print("="*70)
    
    file_path = "Testing Data/leve212.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    print("📍 COORDONNÉES DE RÉFÉRENCE:")
    for borne, coord in REFERENCE_COORDS.items():
        print(f"   {borne}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
    
    # Test extracteur standard
    print(f"\n📊 TEST EXTRACTEUR STANDARD:")
    print("-" * 40)
    
    standard_extractor = HybridOCRCorrector()
    start_time = time.time()
    
    try:
        standard_coords = standard_extractor.extract_coordinates(file_path)
        standard_time = time.time() - start_time
        
        print(f"⏱️  Temps d'extraction: {standard_time:.2f}s")
        print(f"📊 Coordonnées extraites: {len(standard_coords)}")
        
        if standard_coords:
            for coord in standard_coords:
                print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        
        # Évaluation de la précision
        standard_eval = evaluate_extraction_accuracy(standard_coords, REFERENCE_COORDS)
        
        print(f"\n📈 ÉVALUATION DE PRÉCISION (Standard):")
        print(f"   Bornes de référence: {standard_eval['total_reference']}")
        print(f"   Bornes extraites: {standard_eval['total_extracted']}")
        print(f"   Bornes trouvées: {len(standard_eval['matches'])}")
        print(f"   Bornes manquantes: {len(standard_eval['missing'])}")
        
        if standard_eval['missing']:
            print(f"   ❌ Manquantes: {', '.join(standard_eval['missing'])}")
        
        if standard_eval['accuracy_stats']:
            stats = standard_eval['accuracy_stats']
            print(f"   📏 Distance moyenne: {stats['mean_distance']:.2f}m")
            print(f"   📏 Distance max: {stats['max_distance']:.2f}m")
            print(f"   📏 Distance min: {stats['min_distance']:.2f}m")
            print(f"   🎯 Précision (≤5m): {stats['accuracy_rate']:.1f}%")
            
            # Détail des correspondances
            print(f"\n📋 DÉTAIL DES CORRESPONDANCES:")
            for match in standard_eval['matches']:
                status = "✅" if match['accurate'] else "⚠️"
                print(f"   {status} {match['borne']}: distance = {match['distance']:.2f}m")
        
    except Exception as e:
        print(f"❌ Erreur extracteur standard: {e}")
        standard_coords = []
        standard_eval = None
    
    # Test extracteur ULTIME
    print(f"\n🚀 TEST EXTRACTEUR FINAL ULTIME:")
    print("-" * 40)
    
    ultimate_extractor = UltimateFinalExtractor()
    start_time = time.time()
    
    try:
        ultimate_coords = ultimate_extractor.extract_all_coordinates_ultimate(file_path)
        ultimate_time = time.time() - start_time
        
        print(f"⏱️  Temps d'extraction: {ultimate_time:.2f}s")
        print(f"📊 Coordonnées extraites: {len(ultimate_coords)}")
        
        if ultimate_coords:
            for coord in ultimate_coords:
                conf = coord.get('confidence', 1.0)
                source = coord.get('source', 'unknown')
                print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        
        # Évaluation de la précision
        ultimate_eval = evaluate_extraction_accuracy(ultimate_coords, REFERENCE_COORDS)
        
        print(f"\n📈 ÉVALUATION DE PRÉCISION (Ultime):")
        print(f"   Bornes de référence: {ultimate_eval['total_reference']}")
        print(f"   Bornes extraites: {ultimate_eval['total_extracted']}")
        print(f"   Bornes trouvées: {len(ultimate_eval['matches'])}")
        print(f"   Bornes manquantes: {len(ultimate_eval['missing'])}")
        
        if ultimate_eval['missing']:
            print(f"   ❌ Manquantes: {', '.join(ultimate_eval['missing'])}")
        
        if ultimate_eval['accuracy_stats']:
            stats = ultimate_eval['accuracy_stats']
            print(f"   📏 Distance moyenne: {stats['mean_distance']:.2f}m")
            print(f"   📏 Distance max: {stats['max_distance']:.2f}m")
            print(f"   📏 Distance min: {stats['min_distance']:.2f}m")
            print(f"   🎯 Précision (≤5m): {stats['accuracy_rate']:.1f}%")
            
            # Détail des correspondances
            print(f"\n📋 DÉTAIL DES CORRESPONDANCES:")
            for match in ultimate_eval['matches']:
                status = "✅" if match['accurate'] else "⚠️"
                print(f"   {status} {match['borne']}: distance = {match['distance']:.2f}m")
        
    except Exception as e:
        print(f"❌ Erreur extracteur ultime: {e}")
        ultimate_coords = []
        ultimate_eval = None
    
    # Comparaison finale
    print(f"\n{'='*70}")
    print(f"🏆 COMPARAISON FINALE AVEC RÉFÉRENCE")
    print(f"{'='*70}")
    
    if standard_eval and ultimate_eval:
        print(f"📊 COMPLÉTUDE:")
        standard_completeness = (len(standard_eval['matches']) / len(REFERENCE_COORDS)) * 100
        ultimate_completeness = (len(ultimate_eval['matches']) / len(REFERENCE_COORDS)) * 100
        
        print(f"   Standard: {len(standard_eval['matches'])}/{len(REFERENCE_COORDS)} bornes ({standard_completeness:.1f}%)")
        print(f"   Ultime: {len(ultimate_eval['matches'])}/{len(REFERENCE_COORDS)} bornes ({ultimate_completeness:.1f}%)")
        
        if ultimate_completeness > standard_completeness:
            print(f"   🎉 AMÉLIORATION: +{ultimate_completeness - standard_completeness:.1f} points")
        elif ultimate_completeness == standard_completeness:
            print(f"   ➡️  ÉGALITÉ: Même complétude")
        else:
            print(f"   ⚠️  RÉGRESSION: -{standard_completeness - ultimate_completeness:.1f} points")
        
        print(f"\n🎯 PRÉCISION:")
        if standard_eval['accuracy_stats'] and ultimate_eval['accuracy_stats']:
            standard_precision = standard_eval['accuracy_stats']['accuracy_rate']
            ultimate_precision = ultimate_eval['accuracy_stats']['accuracy_rate']
            
            print(f"   Standard: {standard_precision:.1f}% (distance moy: {standard_eval['accuracy_stats']['mean_distance']:.2f}m)")
            print(f"   Ultime: {ultimate_precision:.1f}% (distance moy: {ultimate_eval['accuracy_stats']['mean_distance']:.2f}m)")
            
            if ultimate_precision > standard_precision:
                print(f"   🎉 AMÉLIORATION: +{ultimate_precision - standard_precision:.1f} points de précision")
            elif ultimate_precision == standard_precision:
                print(f"   ➡️  ÉGALITÉ: Même précision")
            else:
                print(f"   ⚠️  RÉGRESSION: -{standard_precision - ultimate_precision:.1f} points de précision")
        
        # Score global
        standard_score = standard_completeness * 0.7 + (standard_eval['accuracy_stats']['accuracy_rate'] if standard_eval['accuracy_stats'] else 0) * 0.3
        ultimate_score = ultimate_completeness * 0.7 + (ultimate_eval['accuracy_stats']['accuracy_rate'] if ultimate_eval['accuracy_stats'] else 0) * 0.3
        
        print(f"\n🏅 SCORE GLOBAL (70% complétude + 30% précision):")
        print(f"   Standard: {standard_score:.1f}/100")
        print(f"   Ultime: {ultimate_score:.1f}/100")
        
        if ultimate_score > standard_score:
            print(f"   🏆 VICTOIRE ULTIME: +{ultimate_score - standard_score:.1f} points")
        elif ultimate_score == standard_score:
            print(f"   🤝 ÉGALITÉ PARFAITE")
        else:
            print(f"   📉 STANDARD MEILLEUR: +{standard_score - ultimate_score:.1f} points")
    
    # Verdict final
    print(f"\n🎯 VERDICT FINAL:")
    if ultimate_eval and len(ultimate_eval['matches']) == len(REFERENCE_COORDS):
        if ultimate_eval['accuracy_stats']['accuracy_rate'] >= 90:
            print(f"   🏆 PARFAIT: Toutes les bornes trouvées avec excellente précision!")
        else:
            print(f"   ✅ EXCELLENT: Toutes les bornes trouvées!")
    elif ultimate_eval and len(ultimate_eval['matches']) >= 6:
        print(f"   👍 BON: Majorité des bornes trouvées")
    else:
        print(f"   ⚠️  INSUFFISANT: Trop de bornes manquantes")
    
    return {
        'standard': standard_eval,
        'ultimate': ultimate_eval,
        'reference': REFERENCE_COORDS
    }

if __name__ == "__main__":
    results = test_leve212_with_reference()

#!/usr/bin/env python3
"""
Analyse de la séquence des bornes dans les levées topographiques
Identifie les fichiers où les bornes ne sont pas dans l'ordre correct (B1, B2, B3, etc.)
"""

import os
import sys
import json
import re
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def extract_borne_number(borne_id: str) -> int:
    """Extrait le numéro de la borne (ex: B1 -> 1, B12 -> 12)"""
    match = re.search(r'B(\d+)', borne_id)
    if match:
        return int(match.group(1))
    return 0

def analyze_borne_sequence(coordinates: List[Dict]) -> Dict:
    """Analyse la séquence des bornes"""
    if not coordinates:
        return {
            'status': 'no_coordinates',
            'message': 'Aucune coordonnée trouvée',
            'missing_bornes': [],
            'out_of_order': [],
            'duplicates': [],
            'sequence_complete': False
        }
    
    # Extraire les numéros de bornes
    borne_numbers = []
    borne_dict = {}
    
    for coord in coordinates:
        borne_num = extract_borne_number(coord['borne'])
        if borne_num > 0:
            borne_numbers.append(borne_num)
            borne_dict[borne_num] = coord['borne']
    
    if not borne_numbers:
        return {
            'status': 'invalid_bornes',
            'message': 'Aucune borne valide trouvée',
            'missing_bornes': [],
            'out_of_order': [],
            'duplicates': [],
            'sequence_complete': False
        }
    
    # Trier les numéros
    sorted_numbers = sorted(borne_numbers)
    min_borne = min(borne_numbers)
    max_borne = max(borne_numbers)
    
    # Vérifier les doublons
    duplicates = []
    seen = set()
    for num in borne_numbers:
        if num in seen:
            duplicates.append(f"B{num}")
        seen.add(num)
    
    # Vérifier la séquence complète
    expected_sequence = list(range(1, max_borne + 1))
    missing_bornes = []
    
    for expected in expected_sequence:
        if expected not in borne_numbers:
            missing_bornes.append(f"B{expected}")
    
    # Vérifier l'ordre
    out_of_order = []
    if borne_numbers != sorted_numbers:
        out_of_order = [borne_dict[num] for num in borne_numbers]
    
    # Déterminer le statut
    sequence_complete = (min_borne == 1 and len(missing_bornes) == 0 and len(duplicates) == 0)
    
    if sequence_complete and len(out_of_order) == 0:
        status = 'perfect'
        message = f'Séquence parfaite: B1 à B{max_borne}'
    elif len(missing_bornes) > 0:
        status = 'missing_bornes'
        message = f'Bornes manquantes: {", ".join(missing_bornes)}'
    elif len(out_of_order) > 0:
        status = 'out_of_order'
        message = f'Bornes dans le désordre: {" -> ".join(out_of_order)}'
    elif len(duplicates) > 0:
        status = 'duplicates'
        message = f'Bornes dupliquées: {", ".join(duplicates)}'
    elif min_borne != 1:
        status = 'no_b1'
        message = f'Commence par B{min_borne} au lieu de B1'
    else:
        status = 'irregular'
        message = 'Séquence irrégulière'
    
    return {
        'status': status,
        'message': message,
        'borne_count': len(coordinates),
        'borne_range': f'B{min_borne}-B{max_borne}',
        'missing_bornes': missing_bornes,
        'out_of_order': out_of_order,
        'duplicates': duplicates,
        'sequence_complete': sequence_complete,
        'actual_sequence': [borne_dict[num] for num in borne_numbers],
        'expected_sequence': [f'B{i}' for i in expected_sequence]
    }

def analyze_all_files():
    """Analyse tous les fichiers de Testing Data"""
    
    print("🔍 ANALYSE DE LA SÉQUENCE DES BORNES")
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
    
    print(f"📁 Fichiers à analyser: {len(test_files)}")
    print()
    
    results = []
    
    # Compteurs pour les statistiques
    perfect_count = 0
    missing_bornes_count = 0
    out_of_order_count = 0
    no_b1_count = 0
    duplicates_count = 0
    no_coords_count = 0
    
    for i, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        print(f"[{i:3d}/{len(test_files)}] 🔍 {filename}", end=" ")
        
        try:
            # Extraction des coordonnées
            coordinates = extractor.extract_coordinates(file_path)
            
            # Analyse de la séquence
            sequence_analysis = analyze_borne_sequence(coordinates)
            
            result = {
                'file': filename,
                'path': file_path,
                'coordinates': coordinates,
                'sequence_analysis': sequence_analysis
            }
            
            results.append(result)
            
            # Affichage du résultat
            status = sequence_analysis['status']
            message = sequence_analysis['message']
            
            if status == 'perfect':
                print(f"✅ {message}")
                perfect_count += 1
            elif status == 'missing_bornes':
                print(f"⚠️  {message}")
                missing_bornes_count += 1
            elif status == 'out_of_order':
                print(f"🔄 {message}")
                out_of_order_count += 1
            elif status == 'no_b1':
                print(f"❌ {message}")
                no_b1_count += 1
            elif status == 'duplicates':
                print(f"🔁 {message}")
                duplicates_count += 1
            elif status == 'no_coordinates':
                print(f"⚪ {message}")
                no_coords_count += 1
            else:
                print(f"❓ {message}")
                
        except Exception as e:
            print(f"🚨 Erreur: {str(e)[:50]}...")
            result = {
                'file': filename,
                'path': file_path,
                'coordinates': [],
                'sequence_analysis': {
                    'status': 'error',
                    'message': str(e),
                    'missing_bornes': [],
                    'out_of_order': [],
                    'duplicates': [],
                    'sequence_complete': False
                }
            }
            results.append(result)
    
    # Analyse des résultats
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ DE L'ANALYSE DES SÉQUENCES")
    print(f"{'='*60}")
    
    total_files = len(results)
    print(f"📁 Total fichiers: {total_files}")
    print(f"✅ Séquences parfaites: {perfect_count} ({(perfect_count/total_files*100):.1f}%)")
    print(f"⚠️  Bornes manquantes: {missing_bornes_count} ({(missing_bornes_count/total_files*100):.1f}%)")
    print(f"🔄 Bornes désordonnées: {out_of_order_count} ({(out_of_order_count/total_files*100):.1f}%)")
    print(f"❌ Sans B1: {no_b1_count} ({(no_b1_count/total_files*100):.1f}%)")
    print(f"🔁 Bornes dupliquées: {duplicates_count} ({(duplicates_count/total_files*100):.1f}%)")
    print(f"⚪ Sans coordonnées: {no_coords_count} ({(no_coords_count/total_files*100):.1f}%)")
    
    # Détails des fichiers problématiques
    print(f"\n🔍 DÉTAILS DES FICHIERS PROBLÉMATIQUES:")
    
    # Fichiers avec bornes manquantes
    missing_files = [r for r in results if r['sequence_analysis']['status'] == 'missing_bornes']
    if missing_files:
        print(f"\n⚠️  FICHIERS AVEC BORNES MANQUANTES ({len(missing_files)}):")
        for result in missing_files:
            analysis = result['sequence_analysis']
            print(f"   - {result['file']}: {analysis['borne_range']} - Manquent: {', '.join(analysis['missing_bornes'])}")
    
    # Fichiers avec bornes désordonnées
    disorder_files = [r for r in results if r['sequence_analysis']['status'] == 'out_of_order']
    if disorder_files:
        print(f"\n🔄 FICHIERS AVEC BORNES DÉSORDONNÉES ({len(disorder_files)}):")
        for result in disorder_files:
            analysis = result['sequence_analysis']
            actual = ' -> '.join(analysis['actual_sequence'])
            expected = ' -> '.join(analysis['expected_sequence'])
            print(f"   - {result['file']}:")
            print(f"     Actuel:   {actual}")
            print(f"     Attendu:  {expected}")
    
    # Fichiers sans B1
    no_b1_files = [r for r in results if r['sequence_analysis']['status'] == 'no_b1']
    if no_b1_files:
        print(f"\n❌ FICHIERS SANS B1 ({len(no_b1_files)}):")
        for result in no_b1_files:
            analysis = result['sequence_analysis']
            print(f"   - {result['file']}: {analysis['borne_range']} - {analysis['message']}")
    
    # Fichiers avec doublons
    duplicate_files = [r for r in results if r['sequence_analysis']['status'] == 'duplicates']
    if duplicate_files:
        print(f"\n🔁 FICHIERS AVEC BORNES DUPLIQUÉES ({len(duplicate_files)}):")
        for result in duplicate_files:
            analysis = result['sequence_analysis']
            print(f"   - {result['file']}: Doublons: {', '.join(analysis['duplicates'])}")
    
    # Sauvegarde des résultats
    output_file = "borne_sequence_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_files': total_files,
                'perfect_sequences': perfect_count,
                'missing_bornes': missing_bornes_count,
                'out_of_order': out_of_order_count,
                'no_b1': no_b1_count,
                'duplicates': duplicates_count,
                'no_coordinates': no_coords_count
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {output_file}")
    
    return results

def analyze_specific_files(filenames: List[str]):
    """Analyse des fichiers spécifiques"""
    
    print("🎯 ANALYSE SPÉCIFIQUE DE FICHIERS")
    print("="*50)
    
    extractor = HybridOCRCorrector()
    
    for filename in filenames:
        file_path = os.path.join("Testing Data", filename)
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {filename}")
            continue
        
        print(f"\n🔍 Analyse de {filename}:")
        print("-" * 40)
        
        try:
            coordinates = extractor.extract_coordinates(file_path)
            sequence_analysis = analyze_borne_sequence(coordinates)
            
            print(f"📍 Coordonnées trouvées: {len(coordinates)}")
            if coordinates:
                print("   Bornes extraites:")
                for coord in coordinates:
                    print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
            
            print(f"\n📊 Analyse de séquence:")
            print(f"   Statut: {sequence_analysis['status']}")
            print(f"   Message: {sequence_analysis['message']}")
            
            if sequence_analysis['missing_bornes']:
                print(f"   Bornes manquantes: {', '.join(sequence_analysis['missing_bornes'])}")
            
            if sequence_analysis['out_of_order']:
                print(f"   Séquence actuelle: {' -> '.join(sequence_analysis['actual_sequence'])}")
                print(f"   Séquence attendue: {' -> '.join(sequence_analysis['expected_sequence'])}")
            
        except Exception as e:
            print(f"🚨 Erreur: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Analyse de fichiers spécifiques
        filenames = sys.argv[1:]
        analyze_specific_files(filenames)
    else:
        # Analyse de tous les fichiers
        analyze_all_files()

#!/usr/bin/env python3
"""
Analyse complète automatisée de l'extraction de coordonnées sur tous les fichiers de Testing Data
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

def run_complete_analysis():
    """Analyse complète automatisée sur tous les fichiers de test"""
    
    print("🧪 ANALYSE COMPLÈTE AUTOMATISÉE - TOUS LES FICHIERS DE TEST")
    print("="*70)
    
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
    
    print(f"📁 Total fichiers à analyser: {len(test_files)}")
    print(f"⏰ Début de l'analyse: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    results = []
    total_start_time = time.time()
    
    for i, file_path in enumerate(test_files, 1):
        filename = os.path.basename(file_path)
        
        # Affichage du progrès
        print(f"[{i:3d}/{len(test_files)}] 🔍 {filename}", end=" ")
        
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
            
            # Affichage du résultat
            if coordinates:
                status_icon = "✅" if len(valid_coords) > 0 else "⚠️"
                closed_icon = "🔒" if polygon_closed else ""
                print(f"{status_icon} {len(coordinates)} coords ({len(valid_coords)} valides) {closed_icon} - {extraction_time:.2f}s")
            else:
                print(f"❌ Aucune coordonnée - {extraction_time:.2f}s")
                
        except Exception as e:
            extraction_time = time.time() - start_time
            print(f"🚨 Erreur: {str(e)[:50]}... - {extraction_time:.2f}s")
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
        
        results.append(result)
    
    # Analyse complète des résultats
    total_time = time.time() - total_start_time
    analysis = analyze_complete_results(results, total_time)
    
    # Sauvegarde des résultats
    output_file = save_complete_results(results, analysis, total_time)
    
    # Génération du rapport détaillé
    generate_detailed_report(results, analysis)
    
    return results, analysis

def analyze_complete_results(results: List[Dict], total_time: float) -> Dict:
    """Analyse complète des résultats"""
    
    print(f"\n{'='*70}")
    print(f"📊 ANALYSE COMPLÈTE DES RÉSULTATS")
    print(f"{'='*70}")
    
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
            print(f"   - {result['file']}: {result.get('error', 'Erreur inconnue')[:50]}...")
    
    # Fichiers avec peu de coordonnées (possibles coordonnées manquantes)
    low_coord_files = [r for r in results if 0 < r['total_coordinates'] <= 3]
    if low_coord_files:
        print(f"\n⚠️  Fichiers avec peu de coordonnées ({len(low_coord_files)}) - possibles coordonnées manquantes:")
        for result in sorted(low_coord_files, key=lambda x: x['total_coordinates']):
            print(f"   - {result['file']}: {result['total_coordinates']} coords")
    
    # Fichiers sans coordonnées
    no_coord_files = [r for r in results if r['total_coordinates'] == 0 and r['status'] != 'error']
    if no_coord_files:
        print(f"\n⚪ Fichiers sans coordonnées ({len(no_coord_files)}):")
        for result in no_coord_files[:10]:
            print(f"   - {result['file']} ({result['extraction_time']}s)")
        if len(no_coord_files) > 10:
            print(f"   ... et {len(no_coord_files) - 10} autres")
    
    return {
        'summary': {
            'total_files': total_files,
            'successful_extractions': successful_extractions,
            'failed_extractions': failed_extractions,
            'no_coordinates': no_coords,
            'success_rate': (successful_extractions / total_files) * 100 if total_files > 0 else 0,
            'total_coordinates': total_coordinates,
            'total_valid_coordinates': total_valid_coordinates,
            'validation_rate': (total_valid_coordinates/total_coordinates*100 if total_coordinates > 0 else 0),
            'closed_polygons': closed_polygons,
            'polygon_closure_rate': (closed_polygons/total_files*100),
            'avg_coordinates_per_file': total_coordinates / total_files if total_files > 0 else 0,
            'total_extraction_time': round(total_time, 2),
            'avg_time_per_file': round(total_time / total_files, 2) if total_files > 0 else 0
        },
        'distribution': coord_distribution,
        'best_files': best_extractions,
        'problem_files': problem_files,
        'low_coord_files': low_coord_files,
        'no_coord_files': no_coord_files
    }

def save_complete_results(results: List[Dict], analysis: Dict, total_time: float) -> str:
    """Sauvegarde les résultats complets"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"complete_testing_results_{timestamp}.json"
    
    data = {
        'metadata': {
            'test_date': datetime.now().isoformat(),
            'testing_data_path': "Testing Data",
            'total_files': len(results),
            'total_time': round(total_time, 2),
            'system': 'HybridOCRCorrector with PaddleOCR + Tesseract'
        },
        'analysis': analysis,
        'results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats complets sauvegardés dans: {output_file}")
    return output_file

def generate_detailed_report(results: List[Dict], analysis: Dict):
    """Génère un rapport détaillé en markdown"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"detailed_extraction_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Rapport Détaillé d'Extraction de Coordonnées\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Système:** HybridOCRCorrector avec PaddleOCR + Tesseract\n\n")
        
        # Résumé exécutif
        f.write("## 📊 Résumé Exécutif\n\n")
        summary = analysis['summary']
        f.write(f"- **Fichiers traités:** {summary['total_files']}\n")
        f.write(f"- **Taux de réussite:** {summary['success_rate']:.1f}%\n")
        f.write(f"- **Total coordonnées:** {summary['total_coordinates']}\n")
        f.write(f"- **Taux de validation:** {summary['validation_rate']:.1f}%\n")
        f.write(f"- **Polygones fermés:** {summary['closed_polygons']} ({summary['polygon_closure_rate']:.1f}%)\n")
        f.write(f"- **Temps total:** {summary['total_extraction_time']}s\n\n")
        
        # Détails par fichier
        f.write("## 📋 Détails par Fichier\n\n")
        f.write("| Fichier | Coords | Valides | Fermé | Temps (s) | Statut |\n")
        f.write("|---------|--------|---------|-------|-----------|--------|\n")
        
        for result in sorted(results, key=lambda x: x['file']):
            coords = result['total_coordinates']
            valides = result['valid_coordinates']
            ferme = "✅" if result['polygon_closed'] else "❌"
            temps = result['extraction_time']
            statut = "✅" if result['status'] == 'success' and coords > 0 else "❌" if result['status'] == 'error' else "⚪"
            
            f.write(f"| {result['file']} | {coords} | {valides} | {ferme} | {temps} | {statut} |\n")
        
        # Coordonnées détaillées pour chaque fichier
        f.write("\n## 📍 Coordonnées Extraites par Fichier\n\n")
        
        for result in sorted(results, key=lambda x: x['file']):
            if result['coordinates']:
                f.write(f"### {result['file']}\n\n")
                f.write("| Borne | X (UTM) | Y (UTM) | Valide |\n")
                f.write("|-------|---------|---------|--------|\n")
                
                extractor = HybridOCRCorrector()
                for coord in result['coordinates']:
                    is_valid = extractor.validate_coordinates(coord['x'], coord['y'])
                    valid_icon = "✅" if is_valid else "❌"
                    f.write(f"| {coord['borne']} | {coord['x']:.2f} | {coord['y']:.2f} | {valid_icon} |\n")
                f.write("\n")
        
        # Recommandations
        f.write("## 🎯 Recommandations\n\n")
        
        if analysis['low_coord_files']:
            f.write("### Fichiers avec Coordonnées Manquantes Possibles\n\n")
            f.write("Les fichiers suivants ont peu de coordonnées et pourraient nécessiter une amélioration de l'extraction:\n\n")
            for result in analysis['low_coord_files']:
                f.write(f"- **{result['file']}:** {result['total_coordinates']} coordonnées seulement\n")
            f.write("\n")
        
        if analysis['no_coord_files']:
            f.write("### Fichiers sans Coordonnées\n\n")
            f.write("Les fichiers suivants n'ont donné aucune coordonnée:\n\n")
            for result in analysis['no_coord_files'][:10]:
                f.write(f"- **{result['file']}**\n")
            f.write("\n")
        
        f.write("### Améliorations Suggérées\n\n")
        f.write("1. **Optimiser les patterns de reconnaissance** pour les fichiers avec peu de coordonnées\n")
        f.write("2. **Améliorer le préprocessing** pour les images de mauvaise qualité\n")
        f.write("3. **Ajuster les seuils de validation** pour capturer plus de coordonnées valides\n")
        f.write("4. **Implémenter une détection contextuelle** pour les bornes manquantes\n")
    
    print(f"📄 Rapport détaillé généré: {report_file}")
    return report_file

if __name__ == "__main__":
    print("🚀 Lancement de l'analyse complète automatisée...")
    results, analysis = run_complete_analysis()
    print(f"\n✅ Analyse terminée!")
    print(f"📊 {analysis['summary']['total_files']} fichiers traités")
    print(f"📍 {analysis['summary']['total_coordinates']} coordonnées extraites")
    print(f"⏱️  Temps total: {analysis['summary']['total_extraction_time']}s")

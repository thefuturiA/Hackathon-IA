#!/usr/bin/env python3
"""
Script de test complet pour l'extraction de coordonnées sur les données de test
Teste l'extraction de coordonnées sur tous les fichiers du dossier Testing Data
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.train_test_topo import TopoTrainingService
from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class TestingDataEvaluator:
    """
    Évaluateur spécialisé pour les données de test
    """
    
    def __init__(self, testing_data_path: str = "Testing Data"):
        self.testing_data_path = testing_data_path
        self.ocr_extractor = HybridOCRCorrector()
        self.results = []
        self.start_time = None
        
    def get_testing_files(self) -> List[str]:
        """Récupère tous les fichiers de test"""
        if not os.path.exists(self.testing_data_path):
            print(f"❌ Dossier {self.testing_data_path} non trouvé")
            return []
            
        files = []
        for filename in os.listdir(self.testing_data_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(self.testing_data_path, filename))
        
        return sorted(files)
    
    def test_single_file(self, file_path: str, show_details: bool = True) -> Dict:
        """Teste l'extraction sur un seul fichier"""
        filename = os.path.basename(file_path)
        
        if show_details:
            print(f"\n{'='*60}")
            print(f"🔍 Test: {filename}")
            print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Extraction des coordonnées
            coordinates = self.ocr_extractor.extract_coordinates(file_path)
            extraction_time = time.time() - start_time
            
            result = {
                'file': filename,
                'path': file_path,
                'coordinates': coordinates,
                'count': len(coordinates),
                'extraction_time': round(extraction_time, 2),
                'status': 'success' if coordinates else 'no_coords_found',
                'timestamp': datetime.now().isoformat()
            }
            
            if show_details:
                if coordinates:
                    print(f"✅ {len(coordinates)} coordonnées extraites en {extraction_time:.2f}s:")
                    for i, coord in enumerate(coordinates, 1):
                        x_valid = self.ocr_extractor.validate_coordinates(coord['x'], coord['y'])
                        status_icon = "✅" if x_valid else "❌"
                        print(f"   {i:2d}. {coord['borne']}: X={coord['x']:>10.2f}, Y={coord['y']:>10.2f} {status_icon}")
                    
                    # Test de fermeture du polygone
                    if len(coordinates) >= 3:
                        is_closed = self.ocr_extractor.is_polygon_closed(coordinates)
                        result['polygon_closed'] = is_closed
                        print(f"\n📐 Polygone fermé: {'✅ Oui' if is_closed else '❌ Non'}")
                    
                    # Statistiques des coordonnées
                    x_coords = [c['x'] for c in coordinates]
                    y_coords = [c['y'] for c in coordinates]
                    print(f"📊 Plage X: {min(x_coords):.2f} - {max(x_coords):.2f}")
                    print(f"📊 Plage Y: {min(y_coords):.2f} - {max(y_coords):.2f}")
                else:
                    print(f"❌ Aucune coordonnée trouvée (temps: {extraction_time:.2f}s)")
                    
        except Exception as e:
            extraction_time = time.time() - start_time
            error_msg = str(e)
            
            if show_details:
                print(f"🚨 Erreur: {error_msg}")
                
            result = {
                'file': filename,
                'path': file_path,
                'coordinates': [],
                'count': 0,
                'extraction_time': round(extraction_time, 2),
                'status': 'error',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            
        return result
    
    def run_batch_test(self, limit: int = None, show_details: bool = True) -> List[Dict]:
        """Lance le test en lot sur tous les fichiers"""
        files = self.get_testing_files()
        
        if not files:
            print("❌ Aucun fichier de test trouvé")
            return []
        
        if limit:
            files = files[:limit]
            
        print(f"🚀 Début des tests sur {len(files)} fichiers...")
        print(f"📁 Dossier: {self.testing_data_path}")
        print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        results = []
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i:3d}/{len(files)}] ", end="")
            
            result = self.test_single_file(file_path, show_details=show_details)
            results.append(result)
            
            # Affichage du progrès
            if not show_details:
                status_icon = "✅" if result['count'] > 0 else "❌"
                print(f"{status_icon} {result['file']}: {result['count']} coords ({result['extraction_time']}s)")
        
        self.results = results
        total_time = time.time() - self.start_time
        print(f"\n⏱️  Temps total: {total_time:.2f}s")
        
        return results
    
    def analyze_results(self) -> Dict:
        """Analyse détaillée des résultats"""
        if not self.results:
            return {}
        
        total_files = len(self.results)
        successful_extractions = len([r for r in self.results if r['count'] > 0])
        failed_extractions = len([r for r in self.results if r['status'] == 'error'])
        no_coords = len([r for r in self.results if r['count'] == 0 and r['status'] != 'error'])
        
        total_coordinates = sum(r['count'] for r in self.results)
        total_time = sum(r['extraction_time'] for r in self.results)
        
        # Distribution par nombre de coordonnées
        coord_distribution = {}
        for result in self.results:
            count = result['count']
            coord_distribution[count] = coord_distribution.get(count, 0) + 1
        
        # Fichiers les plus performants
        best_files = sorted([r for r in self.results if r['count'] > 0], 
                           key=lambda x: x['count'], reverse=True)[:10]
        
        # Fichiers problématiques
        problem_files = [r for r in self.results if r['status'] == 'error']
        no_coord_files = [r for r in self.results if r['count'] == 0 and r['status'] != 'error']
        
        analysis = {
            'summary': {
                'total_files': total_files,
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions,
                'no_coordinates': no_coords,
                'success_rate': (successful_extractions / total_files) * 100 if total_files > 0 else 0,
                'total_coordinates': total_coordinates,
                'avg_coordinates_per_file': total_coordinates / total_files if total_files > 0 else 0,
                'total_extraction_time': round(total_time, 2),
                'avg_time_per_file': round(total_time / total_files, 2) if total_files > 0 else 0
            },
            'distribution': coord_distribution,
            'best_files': best_files,
            'problem_files': problem_files,
            'no_coord_files': no_coord_files
        }
        
        return analysis
    
    def print_detailed_analysis(self):
        """Affiche une analyse détaillée des résultats"""
        analysis = self.analyze_results()
        
        if not analysis:
            print("❌ Aucun résultat à analyser")
            return
        
        summary = analysis['summary']
        
        print(f"\n{'='*80}")
        print(f"📊 ANALYSE DÉTAILLÉE DES RÉSULTATS DE TEST")
        print(f"{'='*80}")
        
        # Résumé général
        print(f"📁 Fichiers testés: {summary['total_files']}")
        print(f"✅ Extractions réussies: {summary['successful_extractions']}")
        print(f"❌ Échecs: {summary['failed_extractions']}")
        print(f"⚪ Sans coordonnées: {summary['no_coordinates']}")
        print(f"📈 Taux de réussite: {summary['success_rate']:.1f}%")
        print(f"📍 Total coordonnées: {summary['total_coordinates']}")
        print(f"📊 Moyenne par fichier: {summary['avg_coordinates_per_file']:.1f}")
        print(f"⏱️  Temps total: {summary['total_extraction_time']}s")
        print(f"⚡ Temps moyen/fichier: {summary['avg_time_per_file']}s")
        
        # Distribution des coordonnées
        print(f"\n📋 Distribution par nombre de coordonnées:")
        for count in sorted(analysis['distribution'].keys(), reverse=True):
            files_count = analysis['distribution'][count]
            percentage = (files_count / summary['total_files']) * 100
            print(f"   {count:2d} coords: {files_count:3d} fichiers ({percentage:5.1f}%)")
        
        # Meilleurs fichiers
        if analysis['best_files']:
            print(f"\n🏆 Top 10 des extractions:")
            for i, result in enumerate(analysis['best_files'], 1):
                print(f"   {i:2d}. {result['file']}: {result['count']} coords ({result['extraction_time']}s)")
        
        # Fichiers problématiques
        if analysis['problem_files']:
            print(f"\n🚨 Fichiers avec erreurs ({len(analysis['problem_files'])}):")
            for result in analysis['problem_files'][:10]:
                print(f"   - {result['file']}: {result.get('error', 'Erreur inconnue')}")
        
        if analysis['no_coord_files']:
            print(f"\n⚪ Fichiers sans coordonnées ({len(analysis['no_coord_files'])}):")
            for result in analysis['no_coord_files'][:10]:
                print(f"   - {result['file']} ({result['extraction_time']}s)")
    
    def save_results(self, output_file: str = None):
        """Sauvegarde les résultats en JSON"""
        if not self.results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"testing_results_{timestamp}.json"
        
        data = {
            'metadata': {
                'test_date': datetime.now().isoformat(),
                'testing_data_path': self.testing_data_path,
                'total_files': len(self.results),
                'total_time': sum(r['extraction_time'] for r in self.results)
            },
            'results': self.results,
            'analysis': self.analyze_results()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Résultats sauvegardés dans: {output_file}")
        return output_file


def main():
    """Fonction principale"""
    print("🧪 TEST D'EXTRACTION DE COORDONNÉES - DONNÉES DE TEST")
    print("="*60)
    
    evaluator = TestingDataEvaluator()
    
    # Menu interactif
    while True:
        print(f"\n📋 Options disponibles:")
        print("1. Test rapide (5 premiers fichiers)")
        print("2. Test complet (tous les fichiers)")
        print("3. Test sur fichiers spécifiques")
        print("4. Test silencieux (tous les fichiers)")
        print("5. Quitter")
        
        choice = input("\n❓ Votre choix (1-5): ").strip()
        
        if choice == '1':
            print("\n🚀 Test rapide sur 5 fichiers...")
            results = evaluator.run_batch_test(limit=5, show_details=True)
            evaluator.print_detailed_analysis()
            
        elif choice == '2':
            print("\n🚀 Test complet sur tous les fichiers...")
            results = evaluator.run_batch_test(show_details=True)
            evaluator.print_detailed_analysis()
            
            save = input("\n💾 Sauvegarder les résultats? (y/N): ").strip().lower()
            if save == 'y':
                evaluator.save_results()
                
        elif choice == '3':
            files_input = input("\n📁 Noms des fichiers (séparés par des virgules): ").strip()
            if files_input:
                filenames = [f.strip() for f in files_input.split(',')]
                for filename in filenames:
                    file_path = os.path.join("Testing Data", filename)
                    if os.path.exists(file_path):
                        evaluator.test_single_file(file_path, show_details=True)
                    else:
                        print(f"❌ Fichier non trouvé: {filename}")
                        
        elif choice == '4':
            print("\n🚀 Test silencieux sur tous les fichiers...")
            results = evaluator.run_batch_test(show_details=False)
            evaluator.print_detailed_analysis()
            
            save = input("\n💾 Sauvegarder les résultats? (y/N): ").strip().lower()
            if save == 'y':
                evaluator.save_results()
                
        elif choice == '5':
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Choix invalide, veuillez réessayer.")


if __name__ == "__main__":
    main()

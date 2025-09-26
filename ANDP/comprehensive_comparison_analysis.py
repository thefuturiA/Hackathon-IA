#!/usr/bin/env python3
"""
Analyse comparative complète entre l'extracteur standard et l'extracteur final
Test sur tous les fichiers de Testing Data pour mesurer l'amélioration
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

from ANDP_app.services.ocr_extraction import HybridOCRCorrector
from final_complete_extractor import FinalCompleteExtractor

class ComprehensiveComparisonAnalyzer:
    """Analyseur de comparaison entre extracteurs standard et final"""
    
    def __init__(self, testing_data_path: str = "Testing Data"):
        self.testing_data_path = testing_data_path
        self.standard_extractor = HybridOCRCorrector()
        self.final_extractor = FinalCompleteExtractor()
        self.results = {
            'standard': [],
            'final': [],
            'comparison': []
        }
        
    def get_all_testing_files(self) -> List[str]:
        """Récupère tous les fichiers de test"""
        if not os.path.exists(self.testing_data_path):
            print(f"❌ Dossier {self.testing_data_path} non trouvé")
            return []
            
        files = []
        for filename in os.listdir(self.testing_data_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(self.testing_data_path, filename))
        
        return sorted(files)
    
    def test_single_file_comparison(self, file_path: str) -> Dict:
        """Compare les deux extracteurs sur un seul fichier"""
        
        filename = os.path.basename(file_path)
        print(f"\n{'='*80}")
        print(f"🔍 COMPARAISON: {filename}")
        print(f"{'='*80}")
        
        # Test extracteur standard
        print("📊 EXTRACTEUR STANDARD:")
        start_time = time.time()
        try:
            standard_coords = self.standard_extractor.extract_coordinates(file_path)
            standard_time = time.time() - start_time
            standard_result = {
                'coordinates': standard_coords,
                'count': len(standard_coords),
                'time': round(standard_time, 2),
                'status': 'success'
            }
            print(f"   ✅ {len(standard_coords)} coordonnées en {standard_time:.2f}s")
            for coord in standard_coords:
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        except Exception as e:
            standard_time = time.time() - start_time
            standard_result = {
                'coordinates': [],
                'count': 0,
                'time': round(standard_time, 2),
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Erreur: {str(e)}")
        
        # Test extracteur final
        print(f"\n🚀 EXTRACTEUR FINAL:")
        start_time = time.time()
        try:
            final_coords = self.final_extractor.extract_all_bornes_complete(file_path)
            final_time = time.time() - start_time
            final_result = {
                'coordinates': final_coords,
                'count': len(final_coords),
                'time': round(final_time, 2),
                'status': 'success'
            }
            print(f"   ✅ {len(final_coords)} coordonnées en {final_time:.2f}s")
            for coord in final_coords:
                conf = coord.get('confidence', 1.0)
                source = coord.get('source', 'unknown')
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        except Exception as e:
            final_time = time.time() - start_time
            final_result = {
                'coordinates': [],
                'count': 0,
                'time': round(final_time, 2),
                'status': 'error',
                'error': str(e)
            }
            print(f"   ❌ Erreur: {str(e)}")
        
        # Analyse comparative
        improvement = final_result['count'] - standard_result['count']
        time_ratio = final_result['time'] / standard_result['time'] if standard_result['time'] > 0 else 1
        
        # Analyse de séquence
        standard_bornes = [c['borne'] for c in standard_result['coordinates']]
        final_bornes = [c['borne'] for c in final_result['coordinates']]
        
        standard_sequence = self._analyze_sequence(standard_bornes)
        final_sequence = self._analyze_sequence(final_bornes)
        
        comparison = {
            'file': filename,
            'standard': standard_result,
            'final': final_result,
            'improvement': {
                'coordinates_gained': improvement,
                'percentage_improvement': (improvement / max(standard_result['count'], 1)) * 100,
                'time_ratio': round(time_ratio, 2),
                'sequence_improvement': {
                    'standard': standard_sequence,
                    'final': final_sequence,
                    'completeness_gain': final_sequence['completeness'] - standard_sequence['completeness']
                }
            }
        }
        
        # Affichage de la comparaison
        print(f"\n📊 COMPARAISON:")
        print(f"   Standard: {standard_result['count']} coords")
        print(f"   Final: {final_result['count']} coords")
        print(f"   Amélioration: +{improvement} coords ({comparison['improvement']['percentage_improvement']:.1f}%)")
        print(f"   Temps: x{time_ratio:.1f}")
        print(f"   Complétude: {standard_sequence['completeness']:.1f}% → {final_sequence['completeness']:.1f}%")
        
        return comparison
    
    def _analyze_sequence(self, bornes: List[str]) -> Dict:
        """Analyse la qualité de la séquence des bornes"""
        
        if not bornes:
            return {
                'has_b1': False,
                'is_sequential': False,
                'missing_count': 8,
                'completeness': 0.0,
                'max_borne': 0
            }
        
        # Extraire les numéros de bornes
        borne_numbers = []
        for borne in bornes:
            try:
                num = int(borne[1:]) if borne.startswith('B') else 0
                if num > 0:
                    borne_numbers.append(num)
            except:
                continue
        
        if not borne_numbers:
            return {
                'has_b1': False,
                'is_sequential': False,
                'missing_count': 8,
                'completeness': 0.0,
                'max_borne': 0
            }
        
        borne_numbers.sort()
        max_borne = max(borne_numbers)
        has_b1 = 1 in borne_numbers
        
        # Vérifier la séquentialité
        expected_sequence = list(range(1, max_borne + 1))
        missing_count = len([n for n in expected_sequence if n not in borne_numbers])
        is_sequential = missing_count == 0
        
        # Calculer la complétude (sur 8 bornes max attendues)
        completeness = (len(borne_numbers) / 8) * 100
        
        return {
            'has_b1': has_b1,
            'is_sequential': is_sequential,
            'missing_count': missing_count,
            'completeness': completeness,
            'max_borne': max_borne,
            'found_bornes': borne_numbers
        }
    
    def run_comprehensive_analysis(self, limit: int = None) -> Dict:
        """Lance l'analyse complète sur tous les fichiers"""
        
        files = self.get_all_testing_files()
        
        if not files:
            print("❌ Aucun fichier de test trouvé")
            return {}
        
        if limit:
            files = files[:limit]
            
        print(f"🚀 ANALYSE COMPARATIVE COMPLÈTE")
        print(f"📁 Dossier: {self.testing_data_path}")
        print(f"📊 Fichiers à analyser: {len(files)}")
        print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = time.time()
        comparisons = []
        
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i:3d}/{len(files)}] ", end="")
            
            comparison = self.test_single_file_comparison(file_path)
            comparisons.append(comparison)
            
            # Affichage du progrès
            improvement = comparison['improvement']['coordinates_gained']
            completeness_gain = comparison['improvement']['sequence_improvement']['completeness_gain']
            status = "🚀" if improvement > 0 else "➡️" if improvement == 0 else "⚠️"
            print(f"   {status} +{improvement} coords, +{completeness_gain:.1f}% complétude")
        
        total_time = time.time() - start_time
        
        # Analyse globale
        global_analysis = self._analyze_global_results(comparisons)
        global_analysis['metadata'] = {
            'total_files': len(files),
            'analysis_time': round(total_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['comparison'] = comparisons
        
        return global_analysis
    
    def _analyze_global_results(self, comparisons: List[Dict]) -> Dict:
        """Analyse globale des résultats"""
        
        if not comparisons:
            return {}
        
        # Statistiques générales
        total_files = len(comparisons)
        
        # Extracteur standard
        standard_total_coords = sum(c['standard']['count'] for c in comparisons)
        standard_avg_coords = standard_total_coords / total_files
        standard_total_time = sum(c['standard']['time'] for c in comparisons)
        standard_avg_time = standard_total_time / total_files
        
        # Extracteur final
        final_total_coords = sum(c['final']['count'] for c in comparisons)
        final_avg_coords = final_total_coords / total_files
        final_total_time = sum(c['final']['time'] for c in comparisons)
        final_avg_time = final_total_time / total_files
        
        # Améliorations
        total_improvement = final_total_coords - standard_total_coords
        files_improved = len([c for c in comparisons if c['improvement']['coordinates_gained'] > 0])
        files_same = len([c for c in comparisons if c['improvement']['coordinates_gained'] == 0])
        files_worse = len([c for c in comparisons if c['improvement']['coordinates_gained'] < 0])
        
        # Analyse de complétude
        standard_avg_completeness = sum(c['improvement']['sequence_improvement']['standard']['completeness'] for c in comparisons) / total_files
        final_avg_completeness = sum(c['improvement']['sequence_improvement']['final']['completeness'] for c in comparisons) / total_files
        completeness_improvement = final_avg_completeness - standard_avg_completeness
        
        # Fichiers avec séquences complètes
        standard_complete_sequences = len([c for c in comparisons if c['improvement']['sequence_improvement']['standard']['completeness'] >= 100])
        final_complete_sequences = len([c for c in comparisons if c['improvement']['sequence_improvement']['final']['completeness'] >= 100])
        
        # Top améliorations
        top_improvements = sorted(comparisons, key=lambda c: c['improvement']['coordinates_gained'], reverse=True)[:10]
        
        return {
            'summary': {
                'total_files': total_files,
                'standard_performance': {
                    'total_coordinates': standard_total_coords,
                    'avg_coordinates': round(standard_avg_coords, 2),
                    'avg_time': round(standard_avg_time, 2),
                    'avg_completeness': round(standard_avg_completeness, 1)
                },
                'final_performance': {
                    'total_coordinates': final_total_coords,
                    'avg_coordinates': round(final_avg_coords, 2),
                    'avg_time': round(final_avg_time, 2),
                    'avg_completeness': round(final_avg_completeness, 1)
                },
                'improvements': {
                    'total_coordinates_gained': total_improvement,
                    'avg_coordinates_gained': round(total_improvement / total_files, 2),
                    'completeness_improvement': round(completeness_improvement, 1),
                    'files_improved': files_improved,
                    'files_same': files_same,
                    'files_worse': files_worse,
                    'improvement_rate': round((files_improved / total_files) * 100, 1)
                },
                'sequence_quality': {
                    'standard_complete_sequences': standard_complete_sequences,
                    'final_complete_sequences': final_complete_sequences,
                    'complete_sequences_gained': final_complete_sequences - standard_complete_sequences
                }
            },
            'top_improvements': top_improvements
        }
    
    def print_global_analysis(self, analysis: Dict):
        """Affiche l'analyse globale"""
        
        if not analysis:
            print("❌ Aucune analyse à afficher")
            return
        
        summary = analysis['summary']
        
        print(f"\n{'='*100}")
        print(f"📊 ANALYSE GLOBALE COMPARATIVE - TOUS LES FICHIERS")
        print(f"{'='*100}")
        
        # Performance générale
        print(f"📁 Fichiers analysés: {summary['total_files']}")
        print(f"⏱️  Temps d'analyse: {analysis['metadata']['analysis_time']:.1f}s")
        
        print(f"\n📈 PERFORMANCE EXTRACTEUR STANDARD:")
        std = summary['standard_performance']
        print(f"   Total coordonnées: {std['total_coordinates']}")
        print(f"   Moyenne par fichier: {std['avg_coordinates']}")
        print(f"   Temps moyen: {std['avg_time']:.2f}s")
        print(f"   Complétude moyenne: {std['avg_completeness']:.1f}%")
        
        print(f"\n🚀 PERFORMANCE EXTRACTEUR FINAL:")
        final = summary['final_performance']
        print(f"   Total coordonnées: {final['total_coordinates']}")
        print(f"   Moyenne par fichier: {final['avg_coordinates']}")
        print(f"   Temps moyen: {final['avg_time']:.2f}s")
        print(f"   Complétude moyenne: {final['avg_completeness']:.1f}%")
        
        print(f"\n🎯 AMÉLIORATIONS GLOBALES:")
        imp = summary['improvements']
        print(f"   Coordonnées gagnées: +{imp['total_coordinates_gained']}")
        print(f"   Gain moyen par fichier: +{imp['avg_coordinates_gained']}")
        print(f"   Amélioration complétude: +{imp['completeness_improvement']:.1f}%")
        print(f"   Fichiers améliorés: {imp['files_improved']}/{summary['total_files']} ({imp['improvement_rate']:.1f}%)")
        print(f"   Fichiers identiques: {imp['files_same']}")
        print(f"   Fichiers dégradés: {imp['files_worse']}")
        
        print(f"\n🎯 QUALITÉ DES SÉQUENCES:")
        seq = summary['sequence_quality']
        print(f"   Séquences complètes (standard): {seq['standard_complete_sequences']}")
        print(f"   Séquences complètes (final): {seq['final_complete_sequences']}")
        print(f"   Gain séquences complètes: +{seq['complete_sequences_gained']}")
        
        # Top améliorations
        print(f"\n🏆 TOP 10 AMÉLIORATIONS:")
        for i, comp in enumerate(analysis['top_improvements'], 1):
            gain = comp['improvement']['coordinates_gained']
            completeness_gain = comp['improvement']['sequence_improvement']['completeness_gain']
            print(f"   {i:2d}. {comp['file']}: +{gain} coords, +{completeness_gain:.1f}% complétude")
    
    def save_comprehensive_results(self, analysis: Dict, output_file: str = None):
        """Sauvegarde les résultats complets"""
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"comprehensive_comparison_{timestamp}.json"
        
        data = {
            'analysis': analysis,
            'detailed_comparisons': self.results['comparison']
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats complets sauvegardés: {output_file}")
        return output_file

def main():
    """Fonction principale"""
    
    print("🔍 ANALYSE COMPARATIVE COMPLÈTE - EXTRACTEURS STANDARD vs FINAL")
    print("="*80)
    
    analyzer = ComprehensiveComparisonAnalyzer()
    
    # Menu
    print(f"\n📋 Options d'analyse:")
    print("1. Test rapide (10 premiers fichiers)")
    print("2. Analyse complète (tous les fichiers)")
    print("3. Test sur fichiers spécifiques")
    
    choice = input("\n❓ Votre choix (1-3): ").strip()
    
    if choice == '1':
        print("\n🚀 Test rapide sur 10 fichiers...")
        analysis = analyzer.run_comprehensive_analysis(limit=10)
        analyzer.print_global_analysis(analysis)
        
    elif choice == '2':
        print("\n🚀 Analyse complète sur tous les fichiers...")
        analysis = analyzer.run_comprehensive_analysis()
        analyzer.print_global_analysis(analysis)
        
        save = input("\n💾 Sauvegarder les résultats? (y/N): ").strip().lower()
        if save == 'y':
            analyzer.save_comprehensive_results(analysis)
            
    elif choice == '3':
        files_input = input("\n📁 Noms des fichiers (séparés par des virgules): ").strip()
        if files_input:
            filenames = [f.strip() for f in files_input.split(',')]
            for filename in filenames:
                file_path = os.path.join("Testing Data", filename)
                if os.path.exists(file_path):
                    analyzer.test_single_file_comparison(file_path)
                else:
                    print(f"❌ Fichier non trouvé: {filename}")
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main()

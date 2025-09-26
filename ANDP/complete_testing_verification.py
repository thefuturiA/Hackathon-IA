#!/usr/bin/env python3
"""
TEST DE VÉRIFICATION COMPLET sur TOUS les éléments de Testing Data
Utilise l'extracteur FINAL ULTIME pour validation exhaustive
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector
from ultimate_final_extractor import UltimateFinalExtractor

class CompleteTestingVerification:
    """
    Vérification complète sur TOUS les fichiers de Testing Data
    """
    
    def __init__(self):
        self.standard_extractor = HybridOCRCorrector()
        self.ultimate_extractor = UltimateFinalExtractor()
        self.results = []
        self.start_time = None
        
    def get_all_testing_files(self) -> List[str]:
        """Récupère TOUS les fichiers de Testing Data"""
        
        testing_data_path = "Testing Data"
        if not os.path.exists(testing_data_path):
            print(f"❌ Dossier {testing_data_path} non trouvé")
            return []
        
        files = []
        for filename in os.listdir(testing_data_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(testing_data_path, filename))
        
        return sorted(files)
    
    def test_single_file_comparison(self, file_path: str, show_details: bool = False) -> Dict:
        """Test comparatif sur un seul fichier"""
        
        filename = os.path.basename(file_path)
        
        if show_details:
            print(f"\n{'='*60}")
            print(f"🔍 VÉRIFICATION: {filename}")
            print(f"{'='*60}")
        
        result = {
            'file': filename,
            'path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test extracteur standard
        start_time = time.time()
        try:
            standard_coords = self.standard_extractor.extract_coordinates(file_path)
            standard_time = time.time() - start_time
            
            standard_bornes = [c['borne'] for c in standard_coords]
            standard_numbers = []
            for borne in standard_bornes:
                try:
                    num = int(borne[1:]) if borne.startswith('B') else 0
                    if num > 0:
                        standard_numbers.append(num)
                except:
                    continue
            
            standard_numbers.sort()
            standard_completeness = (len(standard_coords) / 8) * 100
            
            result['standard'] = {
                'coords': standard_coords,
                'count': len(standard_coords),
                'sequence': [f'B{n}' for n in standard_numbers],
                'completeness': standard_completeness,
                'time': round(standard_time, 2),
                'status': 'success'
            }
            
            if show_details:
                print(f"📊 STANDARD: {len(standard_coords)} coords ({standard_completeness:.1f}%) en {standard_time:.2f}s")
                if standard_coords:
                    for coord in standard_coords:
                        print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
                
        except Exception as e:
            standard_time = time.time() - start_time
            result['standard'] = {
                'coords': [],
                'count': 0,
                'sequence': [],
                'completeness': 0,
                'time': round(standard_time, 2),
                'status': 'error',
                'error': str(e)
            }
            if show_details:
                print(f"❌ STANDARD: Erreur - {str(e)}")
        
        # Test extracteur ULTIME
        start_time = time.time()
        try:
            ultimate_coords = self.ultimate_extractor.extract_all_coordinates_ultimate(file_path)
            ultimate_time = time.time() - start_time
            
            ultimate_bornes = [c['borne'] for c in ultimate_coords]
            ultimate_numbers = []
            for borne in ultimate_bornes:
                try:
                    num = int(borne[1:]) if borne.startswith('B') else 0
                    if num > 0:
                        ultimate_numbers.append(num)
                except:
                    continue
            
            ultimate_numbers.sort()
            ultimate_completeness = (len(ultimate_coords) / 8) * 100
            
            result['ultimate'] = {
                'coords': ultimate_coords,
                'count': len(ultimate_coords),
                'sequence': [f'B{n}' for n in ultimate_numbers],
                'completeness': ultimate_completeness,
                'time': round(ultimate_time, 2),
                'status': 'success'
            }
            
            if show_details:
                print(f"🚀 ULTIME: {len(ultimate_coords)} coords ({ultimate_completeness:.1f}%) en {ultimate_time:.2f}s")
                if ultimate_coords:
                    for coord in ultimate_coords:
                        conf = coord.get('confidence', 1.0)
                        pattern = coord.get('pattern', 'unknown')
                        print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {pattern})")
                
        except Exception as e:
            ultimate_time = time.time() - start_time
            result['ultimate'] = {
                'coords': [],
                'count': 0,
                'sequence': [],
                'completeness': 0,
                'time': round(ultimate_time, 2),
                'status': 'error',
                'error': str(e)
            }
            if show_details:
                print(f"❌ ULTIME: Erreur - {str(e)}")
        
        # Calcul des améliorations
        standard_count = result['standard']['count']
        ultimate_count = result['ultimate']['count']
        improvement = ultimate_count - standard_count
        
        standard_completeness = result['standard']['completeness']
        ultimate_completeness = result['ultimate']['completeness']
        completeness_improvement = ultimate_completeness - standard_completeness
        
        result['improvement'] = {
            'coordinates': improvement,
            'completeness': completeness_improvement,
            'percentage': (improvement / max(standard_count, 1)) * 100
        }
        
        # Classification du résultat
        if improvement > 0:
            result['verdict'] = 'AMÉLIORATION'
            result['status_icon'] = '🎉'
        elif improvement == 0:
            result['verdict'] = 'ÉGALITÉ'
            result['status_icon'] = '➡️'
        else:
            result['verdict'] = 'RÉGRESSION'
            result['status_icon'] = '⚠️'
        
        # Classification de qualité
        if ultimate_completeness >= 100:
            result['quality'] = 'PARFAIT'
            result['quality_icon'] = '🏆'
        elif ultimate_completeness >= 75:
            result['quality'] = 'EXCELLENT'
            result['quality_icon'] = '✅'
        elif ultimate_completeness >= 50:
            result['quality'] = 'BON'
            result['quality_icon'] = '👍'
        else:
            result['quality'] = 'INSUFFISANT'
            result['quality_icon'] = '⚠️'
        
        if show_details:
            print(f"\n📊 COMPARAISON:")
            print(f"   Standard: {standard_count} coords ({standard_completeness:.1f}%)")
            print(f"   Ultime: {ultimate_count} coords ({ultimate_completeness:.1f}%)")
            print(f"   Amélioration: +{improvement} coords (+{completeness_improvement:.1f} points)")
            print(f"   Verdict: {result['status_icon']} {result['verdict']}")
            print(f"   Qualité: {result['quality_icon']} {result['quality']}")
        
        return result
    
    def run_complete_verification(self, show_details: bool = False, max_files: int = None) -> List[Dict]:
        """Lance la vérification complète sur tous les fichiers"""
        
        files = self.get_all_testing_files()
        
        if not files:
            print("❌ Aucun fichier de test trouvé")
            return []
        
        if max_files:
            files = files[:max_files]
        
        print(f"🚀 VÉRIFICATION COMPLÈTE DE TOUS LES FICHIERS TESTING DATA")
        print(f"="*70)
        print(f"📁 Dossier: Testing Data")
        print(f"📊 Fichiers à tester: {len(files)}")
        print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Extracteurs: Standard vs FINAL ULTIME")
        
        self.start_time = time.time()
        results = []
        
        for i, file_path in enumerate(files, 1):
            filename = os.path.basename(file_path)
            
            if not show_details:
                print(f"\n[{i:3d}/{len(files)}] 🔍 {filename}...", end=" ")
            
            try:
                result = self.test_single_file_comparison(file_path, show_details=show_details)
                results.append(result)
                
                if not show_details:
                    improvement = result['improvement']['coordinates']
                    completeness = result['ultimate']['completeness']
                    status_icon = result['status_icon']
                    quality_icon = result['quality_icon']
                    
                    print(f"{status_icon} {quality_icon} {result['ultimate']['count']} coords ({completeness:.1f}%) [+{improvement}]")
                
            except Exception as e:
                print(f"❌ ERREUR: {str(e)}")
                results.append({
                    'file': filename,
                    'path': file_path,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        self.results = results
        total_time = time.time() - self.start_time
        
        print(f"\n⏱️  Temps total: {total_time:.2f}s")
        print(f"📊 Fichiers traités: {len(results)}")
        
        return results
    
    def analyze_complete_results(self) -> Dict:
        """Analyse complète des résultats"""
        
        if not self.results:
            return {}
        
        # Statistiques générales
        total_files = len(self.results)
        successful_files = len([r for r in self.results if 'error' not in r])
        error_files = total_files - successful_files
        
        # Analyse des améliorations
        improvements = []
        regressions = []
        equalities = []
        
        standard_total_coords = 0
        ultimate_total_coords = 0
        
        quality_distribution = {'PARFAIT': 0, 'EXCELLENT': 0, 'BON': 0, 'INSUFFISANT': 0}
        
        for result in self.results:
            if 'error' in result:
                continue
            
            improvement = result['improvement']['coordinates']
            if improvement > 0:
                improvements.append(result)
            elif improvement == 0:
                equalities.append(result)
            else:
                regressions.append(result)
            
            standard_total_coords += result['standard']['count']
            ultimate_total_coords += result['ultimate']['count']
            
            quality = result.get('quality', 'INSUFFISANT')
            quality_distribution[quality] += 1
        
        # Calculs de performance
        improvement_rate = (len(improvements) / successful_files) * 100 if successful_files > 0 else 0
        regression_rate = (len(regressions) / successful_files) * 100 if successful_files > 0 else 0
        equality_rate = (len(equalities) / successful_files) * 100 if successful_files > 0 else 0
        
        total_improvement = ultimate_total_coords - standard_total_coords
        improvement_percentage = (total_improvement / max(standard_total_coords, 1)) * 100
        
        # Top améliorations
        top_improvements = sorted(improvements, key=lambda x: x['improvement']['coordinates'], reverse=True)[:10]
        
        # Cas parfaits
        perfect_cases = [r for r in self.results if r.get('quality') == 'PARFAIT']
        
        analysis = {
            'summary': {
                'total_files': total_files,
                'successful_files': successful_files,
                'error_files': error_files,
                'success_rate': (successful_files / total_files) * 100 if total_files > 0 else 0
            },
            'performance': {
                'improvements': len(improvements),
                'equalities': len(equalities),
                'regressions': len(regressions),
                'improvement_rate': improvement_rate,
                'equality_rate': equality_rate,
                'regression_rate': regression_rate
            },
            'coordinates': {
                'standard_total': standard_total_coords,
                'ultimate_total': ultimate_total_coords,
                'total_improvement': total_improvement,
                'improvement_percentage': improvement_percentage,
                'average_standard': standard_total_coords / successful_files if successful_files > 0 else 0,
                'average_ultimate': ultimate_total_coords / successful_files if successful_files > 0 else 0
            },
            'quality_distribution': quality_distribution,
            'top_improvements': top_improvements,
            'perfect_cases': perfect_cases,
            'regression_cases': regressions
        }
        
        return analysis
    
    def print_complete_analysis(self):
        """Affiche l'analyse complète des résultats"""
        
        analysis = self.analyze_complete_results()
        
        if not analysis:
            print("❌ Aucun résultat à analyser")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 ANALYSE COMPLÈTE - VÉRIFICATION TESTING DATA")
        print(f"{'='*80}")
        
        # Résumé général
        summary = analysis['summary']
        print(f"📁 Fichiers traités: {summary['total_files']}")
        print(f"✅ Succès: {summary['successful_files']}")
        print(f"❌ Erreurs: {summary['error_files']}")
        print(f"📈 Taux de réussite: {summary['success_rate']:.1f}%")
        
        # Performance
        perf = analysis['performance']
        print(f"\n🎯 PERFORMANCE COMPARATIVE:")
        print(f"🎉 Améliorations: {perf['improvements']} fichiers ({perf['improvement_rate']:.1f}%)")
        print(f"➡️  Égalités: {perf['equalities']} fichiers ({perf['equality_rate']:.1f}%)")
        print(f"⚠️  Régressions: {perf['regressions']} fichiers ({perf['regression_rate']:.1f}%)")
        
        # Coordonnées
        coords = analysis['coordinates']
        print(f"\n📍 COORDONNÉES TOTALES:")
        print(f"Standard: {coords['standard_total']} coordonnées")
        print(f"Ultime: {coords['ultimate_total']} coordonnées")
        print(f"Amélioration: +{coords['total_improvement']} coordonnées ({coords['improvement_percentage']:.1f}%)")
        print(f"Moyenne standard: {coords['average_standard']:.1f} coords/fichier")
        print(f"Moyenne ultime: {coords['average_ultimate']:.1f} coords/fichier")
        
        # Distribution qualité
        quality = analysis['quality_distribution']
        print(f"\n🏆 DISTRIBUTION QUALITÉ (Extracteur Ultime):")
        print(f"🏆 Parfait (100%): {quality['PARFAIT']} fichiers")
        print(f"✅ Excellent (≥75%): {quality['EXCELLENT']} fichiers")
        print(f"👍 Bon (≥50%): {quality['BON']} fichiers")
        print(f"⚠️  Insuffisant (<50%): {quality['INSUFFISANT']} fichiers")
        
        # Top améliorations
        if analysis['top_improvements']:
            print(f"\n🎉 TOP 10 AMÉLIORATIONS:")
            for i, result in enumerate(analysis['top_improvements'], 1):
                improvement = result['improvement']['coordinates']
                completeness = result['ultimate']['completeness']
                print(f"   {i:2d}. {result['file']}: +{improvement} coords ({completeness:.1f}%)")
        
        # Cas parfaits
        if analysis['perfect_cases']:
            print(f"\n🏆 CAS PARFAITS (100% complétude):")
            for result in analysis['perfect_cases']:
                print(f"   - {result['file']}: {result['ultimate']['count']} coordonnées")
        
        # Régressions (si il y en a)
        if analysis['regression_cases']:
            print(f"\n⚠️  RÉGRESSIONS À ANALYSER:")
            for result in analysis['regression_cases']:
                improvement = result['improvement']['coordinates']
                print(f"   - {result['file']}: {improvement} coords")
        
        # Verdict final
        print(f"\n{'='*80}")
        print(f"🎯 VERDICT FINAL")
        print(f"{'='*80}")
        
        if perf['improvement_rate'] >= 50:
            print(f"🎉 SUCCÈS MAJEUR: {perf['improvement_rate']:.1f}% des fichiers améliorés")
        elif perf['improvement_rate'] >= 25:
            print(f"✅ SUCCÈS: {perf['improvement_rate']:.1f}% des fichiers améliorés")
        elif perf['regression_rate'] < 10:
            print(f"👍 SATISFAISANT: Peu de régressions ({perf['regression_rate']:.1f}%)")
        else:
            print(f"⚠️  ATTENTION: {perf['regression_rate']:.1f}% de régressions")
        
        if coords['improvement_percentage'] > 0:
            print(f"📈 Amélioration globale: +{coords['improvement_percentage']:.1f}% de coordonnées")
        
        print(f"🏆 Qualité excellente/parfaite: {quality['PARFAIT'] + quality['EXCELLENT']} fichiers")
    
    def save_complete_results(self, output_file: str = None):
        """Sauvegarde les résultats complets"""
        
        if not self.results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"complete_testing_verification_{timestamp}.json"
        
        # Préparer les données pour JSON (enlever les objets non sérialisables)
        json_results = []
        for result in self.results:
            json_result = result.copy()
            
            # Nettoyer les coordonnées pour JSON
            if 'standard' in json_result and 'coords' in json_result['standard']:
                json_result['standard']['coords'] = [
                    {k: v for k, v in coord.items() if k in ['borne', 'x', 'y']}
                    for coord in json_result['standard']['coords']
                ]
            
            if 'ultimate' in json_result and 'coords' in json_result['ultimate']:
                json_result['ultimate']['coords'] = [
                    {k: v for k, v in coord.items() if k in ['borne', 'x', 'y', 'confidence', 'source', 'pattern']}
                    for coord in json_result['ultimate']['coords']
                ]
            
            json_results.append(json_result)
        
        data = {
            'metadata': {
                'test_date': datetime.now().isoformat(),
                'total_files': len(self.results),
                'total_time': time.time() - self.start_time if self.start_time else 0,
                'extractors': ['Standard HybridOCRCorrector', 'Ultimate Final Extractor']
            },
            'results': json_results,
            'analysis': self.analyze_complete_results()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Résultats complets sauvegardés dans: {output_file}")
        return output_file

def main():
    """Fonction principale"""
    
    print("🚀 VÉRIFICATION COMPLÈTE - TOUS LES FICHIERS TESTING DATA")
    print("="*70)
    
    verifier = CompleteTestingVerification()
    
    # Menu interactif
    while True:
        print(f"\n📋 Options de vérification:")
        print("1. Test rapide (10 premiers fichiers)")
        print("2. Test moyen (25 premiers fichiers)")
        print("3. Test complet (TOUS les fichiers)")
        print("4. Test complet avec détails")
        print("5. Quitter")
        
        choice = input("\n❓ Votre choix (1-5): ").strip()
        
        if choice == '1':
            print("\n🚀 Test rapide sur 10 fichiers...")
            results = verifier.run_complete_verification(show_details=False, max_files=10)
            verifier.print_complete_analysis()
            
        elif choice == '2':
            print("\n🚀 Test moyen sur 25 fichiers...")
            results = verifier.run_complete_verification(show_details=False, max_files=25)
            verifier.print_complete_analysis()
            
        elif choice == '3':
            print("\n🚀 Test complet sur TOUS les fichiers...")
            results = verifier.run_complete_verification(show_details=False)
            verifier.print_complete_analysis()
            
            save = input("\n💾 Sauvegarder les résultats? (y/N): ").strip().lower()
            if save == 'y':
                verifier.save_complete_results()
                
        elif choice == '4':
            print("\n🚀 Test complet avec détails sur TOUS les fichiers...")
            results = verifier.run_complete_verification(show_details=True)
            verifier.print_complete_analysis()
            
            save = input("\n💾 Sauvegarder les résultats? (y/N): ").strip().lower()
            if save == 'y':
                verifier.save_complete_results()
                
        elif choice == '5':
            print("👋 Au revoir!")
            break
            
        else:
            print("❌ Choix invalide, veuillez réessayer.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script d'évaluation complète de l'extraction de coordonnées
sur les levées topographiques du Bénin
"""

import sys
import os
import json
from datetime import datetime
sys.path.append('ANDP_app')

from ANDP_app.services.train_test_topo import TopoTrainingService

def main():
    print("🇧🇯 ÉVALUATION COMPLÈTE - EXTRACTION COORDONNÉES LEVÉES TOPOGRAPHIQUES")
    print("="*80)
    
    trainer = TopoTrainingService()
    
    # Test sur un échantillon d'abord
    print("🧪 Phase 1: Test sur échantillon (10 premiers fichiers)")
    print("-" * 60)
    
    sample_results = trainer.batch_extract(limit=10)
    trainer.print_analysis()
    
    # Demander si continuer
    print("\n" + "="*60)
    response = input("❓ Continuer avec l'évaluation complète? (y/N): ")
    
    if response.lower() == 'y':
        print("\n🚀 Phase 2: Évaluation complète")
        print("-" * 60)
        
        # Test complet
        all_results = trainer.batch_extract()
        trainer.print_analysis()
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"evaluation_results_{timestamp}.json"
        trainer.save_results(output_file)
        
        # Statistiques détaillées
        print("\n📊 STATISTIQUES DÉTAILLÉES")
        print("="*60)
        
        analysis = trainer.analyze_results()
        
        # Répartition par nombre de coordonnées
        print("📈 Répartition par nombre de coordonnées extraites:")
        for count, files in sorted(analysis['coordinate_distribution'].items()):
            percentage = (files / analysis['total_files']) * 100
            print(f"   {count:2d} coordonnées: {files:3d} fichiers ({percentage:5.1f}%)")
        
        # Fichiers les plus problématiques
        if analysis['files_without_coords']:
            print(f"\n❌ Fichiers sans coordonnées ({len(analysis['files_without_coords'])}):")
            for i, filename in enumerate(analysis['files_without_coords'][:20]):
                print(f"   {i+1:2d}. {filename}")
            if len(analysis['files_without_coords']) > 20:
                print(f"   ... et {len(analysis['files_without_coords']) - 20} autres")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        success_rate = analysis['success_rate']
        
        if success_rate >= 90:
            print("   ✅ Excellent taux de réussite! Le système fonctionne bien.")
        elif success_rate >= 70:
            print("   ⚠️  Bon taux de réussite, mais peut être amélioré:")
            print("      - Ajuster les patterns de reconnaissance")
            print("      - Améliorer le préprocessing des images")
        else:
            print("   🚨 Taux de réussite faible, améliorations nécessaires:")
            print("      - Revoir les patterns de reconnaissance")
            print("      - Améliorer la qualité OCR")
            print("      - Considérer un entraînement de modèle spécialisé")
        
        print(f"\n💾 Résultats sauvegardés dans: {output_file}")
    
    else:
        print("\n✅ Évaluation terminée sur l'échantillon.")

if __name__ == "__main__":
    main()

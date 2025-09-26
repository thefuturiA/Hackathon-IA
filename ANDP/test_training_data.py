#!/usr/bin/env python3
"""
Script de test pour l'extraction de coordonnées sur les levées topographiques
"""

import os
import sys
sys.path.append('ANDP_app')

from ANDP_app.services.train_test_topo import TopoTrainingService

def test_sample_files():
    """Test sur quelques fichiers échantillons"""
    trainer = TopoTrainingService()
    
    # Test sur les premiers fichiers disponibles
    print("🧪 Test d'extraction sur les levées topographiques du Bénin")
    print("="*60)
    
    # Tester quelques fichiers spécifiques
    sample_files = [
        "leve16.png", "leve18.png", "leve19.png", 
        "leve101.png", "leve102.png"
    ]
    
    trainer.test_specific_files(sample_files)

def test_batch_extraction():
    """Test d'extraction en lot"""
    trainer = TopoTrainingService()
    
    print("\n🚀 Test d'extraction en lot (10 premiers fichiers)")
    print("="*60)
    
    results = trainer.batch_extract(limit=10)
    trainer.print_analysis()
    
    return results

def main():
    print("🇧🇯 EXTRACTION DE COORDONNÉES - LEVÉES TOPOGRAPHIQUES BÉNIN")
    print("="*70)
    
    # Vérifier que le dossier Training Data existe
    if not os.path.exists("Training Data"):
        print("❌ Dossier 'Training Data' non trouvé")
        return
    
    # Test échantillon
    test_sample_files()
    
    # Demander si continuer avec le test en lot
    response = input("\n❓ Effectuer un test en lot sur 10 fichiers? (y/N): ")
    if response.lower() == 'y':
        results = test_batch_extraction()
        
        # Proposer de sauvegarder
        save_response = input("\n💾 Sauvegarder les résultats? (y/N): ")
        if save_response.lower() == 'y':
            trainer = TopoTrainingService()
            trainer.results = results
            trainer.save_results("test_results.json")

if __name__ == "__main__":
    main()

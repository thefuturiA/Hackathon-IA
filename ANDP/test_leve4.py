#!/usr/bin/env python3
"""
Test spécifique pour leve4.jpeg avec comparaison extracteur standard vs final
"""

import os
import sys
import time

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector
from final_complete_extractor import FinalCompleteExtractor

def test_leve4_comparison():
    """Test comparatif sur leve4.jpeg"""
    
    print("🔍 TEST COMPARATIF - leve4.jpeg")
    print("="*60)
    
    file_path = "Testing Data/leve4.jpeg"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    standard_extractor = HybridOCRCorrector()
    final_extractor = FinalCompleteExtractor()
    
    # Test extracteur standard
    print("📊 EXTRACTEUR STANDARD:")
    print("-" * 30)
    start_time = time.time()
    try:
        standard_coords = standard_extractor.extract_coordinates(file_path)
        standard_time = time.time() - start_time
        
        print(f"✅ {len(standard_coords)} coordonnées extraites en {standard_time:.2f}s")
        if standard_coords:
            for coord in standard_coords:
                print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        else:
            print("   ❌ Aucune coordonnée trouvée")
            
        # Analyse de séquence standard
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
        
        print(f"   📊 Séquence: {[f'B{n}' for n in standard_numbers]}")
        print(f"   📈 Complétude: {standard_completeness:.1f}%")
        
        if standard_numbers:
            expected = list(range(1, max(standard_numbers) + 1))
            missing = [f'B{n}' for n in expected if n not in standard_numbers]
            if missing:
                print(f"   ❌ Manquantes: {', '.join(missing)}")
        
    except Exception as e:
        standard_coords = []
        standard_time = time.time() - start_time
        print(f"   ❌ Erreur: {str(e)}")
    
    print(f"\n🚀 EXTRACTEUR FINAL:")
    print("-" * 30)
    start_time = time.time()
    try:
        final_coords = final_extractor.extract_all_bornes_complete(file_path)
        final_time = time.time() - start_time
        
        print(f"✅ {len(final_coords)} coordonnées extraites en {final_time:.2f}s")
        if final_coords:
            for coord in final_coords:
                conf = coord.get('confidence', 1.0)
                source = coord.get('source', 'unknown')
                print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        else:
            print("   ❌ Aucune coordonnée trouvée")
            
        # Analyse de séquence final
        final_bornes = [c['borne'] for c in final_coords]
        final_numbers = []
        for borne in final_bornes:
            try:
                num = int(borne[1:]) if borne.startswith('B') else 0
                if num > 0:
                    final_numbers.append(num)
            except:
                continue
        
        final_numbers.sort()
        final_completeness = (len(final_coords) / 8) * 100
        
        print(f"   📊 Séquence: {[f'B{n}' for n in final_numbers]}")
        print(f"   📈 Complétude: {final_completeness:.1f}%")
        
        if final_numbers:
            expected = list(range(1, max(final_numbers) + 1))
            missing = [f'B{n}' for n in expected if n not in final_numbers]
            if missing:
                print(f"   ❌ Manquantes: {', '.join(missing)}")
            else:
                print(f"   ✅ Séquence complète!")
        
    except Exception as e:
        final_coords = []
        final_time = time.time() - start_time
        print(f"   ❌ Erreur: {str(e)}")
    
    # Comparaison finale
    print(f"\n📊 COMPARAISON FINALE:")
    print("="*40)
    
    improvement = len(final_coords) - len(standard_coords)
    completeness_improvement = final_completeness - standard_completeness if 'final_completeness' in locals() and 'standard_completeness' in locals() else 0
    
    print(f"📍 Coordonnées:")
    print(f"   Standard: {len(standard_coords)}")
    print(f"   Final: {len(final_coords)}")
    print(f"   Amélioration: +{improvement} ({improvement/max(len(standard_coords),1)*100:.1f}%)")
    
    print(f"📈 Complétude:")
    print(f"   Standard: {standard_completeness:.1f}%" if 'standard_completeness' in locals() else "   Standard: N/A")
    print(f"   Final: {final_completeness:.1f}%" if 'final_completeness' in locals() else "   Final: N/A")
    print(f"   Amélioration: +{completeness_improvement:.1f} points")
    
    print(f"⏱️  Temps:")
    print(f"   Standard: {standard_time:.2f}s")
    print(f"   Final: {final_time:.2f}s")
    print(f"   Ratio: x{final_time/max(standard_time,0.1):.1f}")
    
    # Verdict
    if improvement > 0:
        print(f"\n🎉 SUCCÈS: L'extracteur final est MEILLEUR!")
    elif improvement == 0:
        print(f"\n➡️  ÉGALITÉ: Même performance")
    else:
        print(f"\n⚠️  ATTENTION: L'extracteur standard était meilleur")
    
    return {
        'standard': {'coords': standard_coords, 'time': standard_time},
        'final': {'coords': final_coords, 'time': final_time},
        'improvement': improvement
    }

if __name__ == "__main__":
    result = test_leve4_comparison()

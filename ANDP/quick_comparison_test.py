#!/usr/bin/env python3
"""
Test rapide de comparaison entre extracteur standard et final
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

def quick_comparison_test():
    """Test rapide sur fichiers clés"""
    
    print("🚀 TEST RAPIDE DE COMPARAISON - EXTRACTEURS STANDARD vs FINAL")
    print("="*80)
    
    # Fichiers de test représentatifs
    test_files = [
        "leve212.png",  # Cas problématique connu
        "leve1.jpg",    # Cas de référence
        "leve213.png",  # Fichier similaire à 212
        "leve214.png",  # Autre fichier de la série
        "leve251.jpg"   # Fichier différent
    ]
    
    standard_extractor = HybridOCRCorrector()
    final_extractor = FinalCompleteExtractor()
    
    results = []
    
    for filename in test_files:
        file_path = f"Testing Data/{filename}"
        
        if not os.path.exists(file_path):
            print(f"⚠️  Fichier non trouvé: {filename}")
            continue
            
        print(f"\n{'='*60}")
        print(f"🔍 TEST: {filename}")
        print(f"{'='*60}")
        
        # Test extracteur standard
        print("📊 EXTRACTEUR STANDARD:")
        start_time = time.time()
        try:
            standard_coords = standard_extractor.extract_coordinates(file_path)
            standard_time = time.time() - start_time
            print(f"   ✅ {len(standard_coords)} coordonnées en {standard_time:.2f}s")
            for coord in standard_coords:
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        except Exception as e:
            standard_coords = []
            standard_time = time.time() - start_time
            print(f"   ❌ Erreur: {str(e)}")
        
        # Test extracteur final (version simplifiée)
        print(f"\n🚀 EXTRACTEUR FINAL:")
        start_time = time.time()
        try:
            final_coords = final_extractor.extract_all_bornes_complete(file_path)
            final_time = time.time() - start_time
            print(f"   ✅ {len(final_coords)} coordonnées en {final_time:.2f}s")
            for coord in final_coords:
                conf = coord.get('confidence', 1.0)
                source = coord.get('source', 'unknown')
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f})")
        except Exception as e:
            final_coords = []
            final_time = time.time() - start_time
            print(f"   ❌ Erreur: {str(e)}")
        
        # Comparaison
        improvement = len(final_coords) - len(standard_coords)
        print(f"\n📊 COMPARAISON:")
        print(f"   Standard: {len(standard_coords)} coords")
        print(f"   Final: {len(final_coords)} coords")
        print(f"   Amélioration: +{improvement} coords")
        print(f"   Temps: {standard_time:.2f}s → {final_time:.2f}s")
        
        # Analyse de séquence
        standard_bornes = [c['borne'] for c in standard_coords]
        final_bornes = [c['borne'] for c in final_coords]
        
        standard_completeness = (len(standard_coords) / 8) * 100
        final_completeness = (len(final_coords) / 8) * 100
        
        print(f"   Complétude: {standard_completeness:.1f}% → {final_completeness:.1f}%")
        
        results.append({
            'file': filename,
            'standard_count': len(standard_coords),
            'final_count': len(final_coords),
            'improvement': improvement,
            'standard_time': standard_time,
            'final_time': final_time
        })
    
    # Résumé global
    print(f"\n{'='*80}")
    print(f"📊 RÉSUMÉ GLOBAL")
    print(f"{'='*80}")
    
    total_standard = sum(r['standard_count'] for r in results)
    total_final = sum(r['final_count'] for r in results)
    total_improvement = total_final - total_standard
    
    avg_standard_time = sum(r['standard_time'] for r in results) / len(results)
    avg_final_time = sum(r['final_time'] for r in results) / len(results)
    
    print(f"📁 Fichiers testés: {len(results)}")
    print(f"📍 Coordonnées totales:")
    print(f"   Standard: {total_standard}")
    print(f"   Final: {total_final}")
    print(f"   Amélioration: +{total_improvement} (+{(total_improvement/max(total_standard,1)*100):.1f}%)")
    print(f"⏱️  Temps moyen:")
    print(f"   Standard: {avg_standard_time:.2f}s")
    print(f"   Final: {avg_final_time:.2f}s")
    
    # Détail par fichier
    print(f"\n📋 DÉTAIL PAR FICHIER:")
    for r in results:
        status = "🚀" if r['improvement'] > 0 else "➡️" if r['improvement'] == 0 else "⚠️"
        print(f"   {status} {r['file']}: {r['standard_count']} → {r['final_count']} (+{r['improvement']})")
    
    return results

if __name__ == "__main__":
    results = quick_comparison_test()

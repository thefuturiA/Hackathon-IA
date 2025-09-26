#!/usr/bin/env python3
"""
Test spécifique pour leve298.png avec comparaison extracteur standard vs ultra-précis corrigé
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
from fixed_ultra_precise_extractor import FixedUltraPreciseExtractor

def test_leve298_comparison():
    """Test comparatif sur leve298.png"""
    
    print("🔍 TEST COMPARATIF - leve298.png")
    print("="*60)
    
    file_path = "Testing Data/leve298.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    standard_extractor = HybridOCRCorrector()
    fixed_extractor = FixedUltraPreciseExtractor()
    
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
            else:
                print(f"   ✅ Séquence complète!")
        
    except Exception as e:
        standard_coords = []
        standard_time = time.time() - start_time
        print(f"   ❌ Erreur: {str(e)}")
        standard_completeness = 0
    
    print(f"\n🚀 EXTRACTEUR ULTRA-PRÉCIS CORRIGÉ:")
    print("-" * 30)
    start_time = time.time()
    try:
        fixed_coords = fixed_extractor.extract_all_coordinates_fixed(file_path)
        fixed_time = time.time() - start_time
        
        print(f"✅ {len(fixed_coords)} coordonnées extraites en {fixed_time:.2f}s")
        if fixed_coords:
            for coord in fixed_coords:
                conf = coord.get('confidence', 1.0)
                source = coord.get('source', 'unknown')
                print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {source})")
        else:
            print("   ❌ Aucune coordonnée trouvée")
            
        # Analyse de séquence corrigé
        fixed_bornes = [c['borne'] for c in fixed_coords]
        fixed_numbers = []
        for borne in fixed_bornes:
            try:
                num = int(borne[1:]) if borne.startswith('B') else 0
                if num > 0:
                    fixed_numbers.append(num)
            except:
                continue
        
        fixed_numbers.sort()
        fixed_completeness = (len(fixed_coords) / 8) * 100
        
        print(f"   📊 Séquence: {[f'B{n}' for n in fixed_numbers]}")
        print(f"   📈 Complétude: {fixed_completeness:.1f}%")
        
        if fixed_numbers:
            expected = list(range(1, max(fixed_numbers) + 1))
            missing = [f'B{n}' for n in expected if n not in fixed_numbers]
            if missing:
                print(f"   ❌ Manquantes: {', '.join(missing)}")
            else:
                print(f"   ✅ Séquence complète!")
        
    except Exception as e:
        fixed_coords = []
        fixed_time = time.time() - start_time
        print(f"   ❌ Erreur: {str(e)}")
        fixed_completeness = 0
    
    # Comparaison finale
    print(f"\n📊 COMPARAISON FINALE:")
    print("="*40)
    
    improvement = len(fixed_coords) - len(standard_coords)
    completeness_improvement = fixed_completeness - standard_completeness
    
    print(f"📍 Coordonnées:")
    print(f"   Standard: {len(standard_coords)}")
    print(f"   Ultra-précis corrigé: {len(fixed_coords)}")
    print(f"   Amélioration: +{improvement} ({improvement/max(len(standard_coords),1)*100:.1f}%)")
    
    print(f"📈 Complétude:")
    print(f"   Standard: {standard_completeness:.1f}%")
    print(f"   Ultra-précis corrigé: {fixed_completeness:.1f}%")
    print(f"   Amélioration: +{completeness_improvement:.1f} points")
    
    print(f"⏱️  Temps:")
    print(f"   Standard: {standard_time:.2f}s")
    print(f"   Ultra-précis corrigé: {fixed_time:.2f}s")
    print(f"   Ratio: x{fixed_time/max(standard_time,0.1):.1f}")
    
    # Verdict
    if improvement > 0:
        print(f"\n🎉 SUCCÈS: L'extracteur ultra-précis corrigé est MEILLEUR!")
        print(f"   +{improvement} coordonnées supplémentaires")
        print(f"   +{completeness_improvement:.1f} points de complétude")
    elif improvement == 0:
        print(f"\n➡️  ÉGALITÉ: Même performance")
        if fixed_completeness >= 75:
            print(f"   ✅ Performance déjà excellente maintenue")
        elif fixed_completeness >= 50:
            print(f"   👍 Performance satisfaisante maintenue")
    else:
        print(f"\n⚠️  ATTENTION: L'extracteur standard était meilleur")
        print(f"   Régression de {abs(improvement)} coordonnées")
    
    # Analyse de qualité
    if fixed_completeness >= 100:
        print(f"\n🏆 EXCELLENCE: Extraction parfaite (100%)")
    elif fixed_completeness >= 75:
        print(f"\n✅ TRÈS BON: Extraction de haute qualité (≥75%)")
    elif fixed_completeness >= 50:
        print(f"\n👍 BON: Extraction acceptable (≥50%)")
    else:
        print(f"\n⚠️  FAIBLE: Extraction insuffisante (<50%)")
    
    # Analyse détaillée des coordonnées trouvées
    if fixed_coords:
        print(f"\n📍 DÉTAIL DES COORDONNÉES ULTRA-PRÉCISES CORRIGÉES:")
        for coord in fixed_coords:
            conf = coord.get('confidence', 1.0)
            source = coord.get('source', 'unknown')
            status = "🔥" if conf >= 0.9 else "✅" if conf >= 0.7 else "⚠️"
            print(f"   {status} {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f})")
    
    # Analyse des patterns détectés
    if fixed_coords:
        sources = {}
        for coord in fixed_coords:
            source = coord.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n🔍 ANALYSE DES PATTERNS DÉTECTÉS:")
        for source, count in sources.items():
            print(f"   {source}: {count} coordonnées")
    
    return {
        'standard': {'coords': standard_coords, 'time': standard_time, 'completeness': standard_completeness},
        'fixed': {'coords': fixed_coords, 'time': fixed_time, 'completeness': fixed_completeness},
        'improvement': improvement,
        'completeness_improvement': completeness_improvement
    }

if __name__ == "__main__":
    result = test_leve298_comparison()

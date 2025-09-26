#!/usr/bin/env python3
import sys
import os
sys.path.append('ANDP_app')

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def test_leve106():
    print("=== TEST SPÉCIFIQUE POUR LEVE106.PNG ===")
    
    extractor = HybridOCRCorrector()
    coords = extractor.extract_coordinates('Training Data/leve106.png')
    
    print(f"\n📍 COORDONNÉES EXTRAITES ({len(coords)} bornes):")
    if coords:
        for c in coords:
            print(f"   {c['borne']}: X={c['x']}, Y={c['y']}")
    else:
        print("   Aucune coordonnée trouvée")
    
    # Test de fermeture du polygone
    if len(coords) >= 3:
        is_closed = extractor.is_polygon_closed(coords, tolerance=10.0)
        print(f"\n🔄 Polygone fermé (tolérance 10m): {'✅' if is_closed else '❌'}")
    
    # Validation des coordonnées
    print(f"\n🔍 VALIDATION:")
    valid_coords = 0
    for c in coords:
        is_valid = extractor.validate_coordinates(c['x'], c['y'])
        status = "✅" if is_valid else "❌"
        print(f"   {c['borne']}: {status} ({'Valide' if is_valid else 'Hors limites Bénin'})")
        if is_valid:
            valid_coords += 1
    
    if coords:
        success_rate = (valid_coords / len(coords)) * 100
        print(f"\n📊 STATISTIQUES:")
        print(f"   Bornes extraites: {len(coords)}")
        print(f"   Bornes valides: {valid_coords}/{len(coords)} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("   🎉 Extraction parfaite!")
        elif success_rate >= 80:
            print("   ✅ Bonne extraction")
        else:
            print("   ⚠️  Extraction à améliorer")

if __name__ == "__main__":
    test_leve106()

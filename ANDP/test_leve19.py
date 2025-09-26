#!/usr/bin/env python3
import sys
import os
sys.path.append('ANDP_app')

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def test_leve19():
    print("=== TEST SPÉCIFIQUE POUR LEVE19.PNG ===")
    
    extractor = HybridOCRCorrector()
    coords = extractor.extract_coordinates('Training Data/leve19.png')
    
    print(f"\n📍 COORDONNÉES EXTRAITES ({len(coords)} bornes):")
    if coords:
        for c in coords:
            print(f"   {c['borne']}: X={c['x']}, Y={c['y']}")
        
        # Vérifier si le polygone est fermé
        if len(coords) >= 3:
            is_closed = extractor.is_polygon_closed(coords, tolerance=5.0)  # Tolérance plus large
            print(f"\n🔄 Polygone fermé (tolérance 5m): {'✅' if is_closed else '❌'}")
    else:
        print("   Aucune coordonnée trouvée")
    
    # Coordonnées attendues selon vous
    expected = [
        {'borne': 'B1', 'x': 401374.38, 'y': 712334.71},
        {'borne': 'B2', 'x': 401378.12, 'y': 712287.17},
        {'borne': 'B3', 'x': 401353.24, 'y': 712284.56},
        {'borne': 'B4', 'x': 401349.45, 'y': 712332.75}
    ]
    
    print(f"\n📋 COORDONNÉES ATTENDUES ({len(expected)} bornes):")
    for c in expected:
        print(f"   {c['borne']}: X={c['x']}, Y={c['y']}")
    
    # Comparaison
    found_bornes = {c['borne'] for c in coords}
    expected_bornes = {c['borne'] for c in expected}
    
    missing = expected_bornes - found_bornes
    extra = found_bornes - expected_bornes
    
    print(f"\n🔍 ANALYSE:")
    print(f"   Bornes manquantes: {missing if missing else 'Aucune'}")
    print(f"   Bornes supplémentaires: {extra if extra else 'Aucune'}")
    
    # Test de fermeture avec les coordonnées attendues
    is_expected_closed = extractor.is_polygon_closed(expected, tolerance=5.0)
    print(f"   Polygone attendu fermé: {'✅' if is_expected_closed else '❌'}")

if __name__ == "__main__":
    test_leve19()

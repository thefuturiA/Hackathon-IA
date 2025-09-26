#!/usr/bin/env python3
import sys
import os
sys.path.append('ANDP_app')

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def test_leve101():
    print("=== TEST SPÉCIFIQUE POUR LEVE101.PNG ===")
    
    extractor = HybridOCRCorrector()
    coords = extractor.extract_coordinates('Training Data/leve101.png')
    
    print(f"\n📍 COORDONNÉES EXTRAITES ({len(coords)} bornes):")
    if coords:
        for c in coords:
            print(f"   {c['borne']}: X={c['x']}, Y={c['y']}")
    else:
        print("   Aucune coordonnée trouvée")
    
    # Coordonnées attendues selon vous
    expected = [
        {'borne': 'B1', 'x': 396027.3, 'y': 726474.99},
        {'borne': 'B2', 'x': 396098.92, 'y': 726433.0},
        {'borne': 'B3', 'x': 396069.24, 'y': 726358.68},
        {'borne': 'B4', 'x': 396047.61, 'y': 726305.55},
        {'borne': 'B5', 'x': 395968.92, 'y': 726317.8},
        {'borne': 'B6', 'x': 395974.84, 'y': 726357.42},
        {'borne': 'B7', 'x': 395973.38, 'y': 726368.85},
        {'borne': 'B8', 'x': 395963.55, 'y': 726403.42},
        {'borne': 'B9', 'x': 395972.67, 'y': 726410.36},
        {'borne': 'B10', 'x': 395983.57, 'y': 726424.79}
    ]
    
    print(f"\n📋 COORDONNÉES ATTENDUES ({len(expected)} bornes):")
    for c in expected:
        print(f"   {c['borne']}: X={c['x']}, Y={c['y']}")
    
    # Comparaison détaillée
    found_bornes = {c['borne']: c for c in coords}
    expected_bornes = {c['borne']: c for c in expected}
    
    missing = set(expected_bornes.keys()) - set(found_bornes.keys())
    extra = set(found_bornes.keys()) - set(expected_bornes.keys())
    common = set(found_bornes.keys()) & set(expected_bornes.keys())
    
    print(f"\n🔍 ANALYSE DÉTAILLÉE:")
    print(f"   Bornes trouvées: {len(coords)}/{len(expected)} ({len(coords)/len(expected)*100:.1f}%)")
    print(f"   Bornes manquantes: {missing if missing else 'Aucune'}")
    print(f"   Bornes supplémentaires: {extra if extra else 'Aucune'}")
    
    # Vérification de précision pour les bornes communes
    if common:
        print(f"\n📏 PRÉCISION DES COORDONNÉES (bornes communes):")
        total_error_x = 0
        total_error_y = 0
        for borne in sorted(common):
            found = found_bornes[borne]
            expected_coord = expected_bornes[borne]
            error_x = abs(found['x'] - expected_coord['x'])
            error_y = abs(found['y'] - expected_coord['y'])
            total_error_x += error_x
            total_error_y += error_y
            
            status = "✅" if error_x < 1.0 and error_y < 1.0 else "⚠️" if error_x < 5.0 and error_y < 5.0 else "❌"
            print(f"   {borne}: ΔX={error_x:.2f}m, ΔY={error_y:.2f}m {status}")
        
        avg_error_x = total_error_x / len(common)
        avg_error_y = total_error_y / len(common)
        print(f"   Erreur moyenne: ΔX={avg_error_x:.2f}m, ΔY={avg_error_y:.2f}m")
    
    # Test de fermeture du polygone
    if len(coords) >= 3:
        is_closed = extractor.is_polygon_closed(coords, tolerance=10.0)
        print(f"\n🔄 Polygone fermé (tolérance 10m): {'✅' if is_closed else '❌'}")
    
    if len(expected) >= 3:
        is_expected_closed = extractor.is_polygon_closed(expected, tolerance=10.0)
        print(f"   Polygone attendu fermé: {'✅' if is_expected_closed else '❌'}")

if __name__ == "__main__":
    test_leve101()

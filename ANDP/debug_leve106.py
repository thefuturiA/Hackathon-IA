#!/usr/bin/env python3
import sys
import os
sys.path.append('ANDP_app')

from ANDP_app.services.ocr_extraction import HybridOCRCorrector
import re

def debug_leve106():
    print("=== DEBUG DÉTAILLÉ POUR LEVE106.PNG ===")
    
    extractor = HybridOCRCorrector()
    
    # Extraction du texte brut pour analyse
    img = extractor.preprocess_image('Training Data/leve106.png')
    ocr_result = extractor.ocr.ocr('Training Data/leve106.png')
    raw_texts = " ".join([line[1][0] for page in ocr_result for line in page])
    
    print("TEXTE BRUT OCR:")
    print(raw_texts)
    print("\n" + "="*80)
    
    # Après corrections
    corrected_text = extractor.correct_text_ml(raw_texts)
    corrected_text = extractor.apply_borne_corrections(corrected_text)
    
    print("TEXTE APRÈS CORRECTIONS:")
    print(corrected_text)
    print("\n" + "="*80)
    
    # Recherche de tous les nombres qui ressemblent à des coordonnées
    print("RECHERCHE DE COORDONNÉES POTENTIELLES:")
    
    # Chercher des nombres de 6-7 chiffres (coordonnées UTM)
    utm_numbers = re.findall(r'\d{6,7}[.,]?\d{0,3}', corrected_text)
    print(f"Nombres UTM trouvés: {utm_numbers}")
    
    # Valider lesquels sont dans les limites du Bénin
    valid_coords = []
    for num_str in utm_numbers:
        try:
            num = float(num_str.replace(',', '.'))
            if extractor.validate_coordinates(num, 700000):  # Test avec Y arbitraire
                print(f"  X potentiel: {num}")
                valid_coords.append(num)
            elif extractor.validate_coordinates(400000, num):  # Test avec X arbitraire
                print(f"  Y potentiel: {num}")
                valid_coords.append(num)
        except ValueError:
            continue
    
    print(f"\nCoordonnées valides trouvées: {valid_coords}")
    
    # Recherche de patterns de bornes alternatifs
    print("\n" + "="*80)
    print("RECHERCHE DE PATTERNS ALTERNATIFS:")
    
    # Peut-être que les bornes ne sont pas nommées B1, B2 mais autrement
    alternative_patterns = [
        r'(\d+)[^\d]*(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})',  # Juste numéro
        r'([A-Z]\d*)[^\d]*(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})',  # Lettre + numéro
        r'(P\d+)[^\d]*(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})',  # P1, P2, etc.
        r'(\d{6,7}[.,]?\d{0,3})[^\d]*(\d{6,7}[.,]?\d{0,3})',  # Juste coordonnées
    ]
    
    for i, pattern in enumerate(alternative_patterns, 1):
        print(f"\nPATTERN ALTERNATIF {i}: {pattern}")
        matches = list(re.finditer(pattern, corrected_text))
        for match in matches:
            try:
                if len(match.groups()) == 3:
                    borne_id = match.group(1)
                    x = float(match.group(2).replace(',', '.'))
                    y = float(match.group(3).replace(',', '.'))
                    if extractor.validate_coordinates(x, y):
                        print(f"  ✅ {borne_id}: X={x}, Y={y}")
                    else:
                        print(f"  ❌ {borne_id}: X={x}, Y={y} (hors limites)")
                else:
                    x = float(match.group(1).replace(',', '.'))
                    y = float(match.group(2).replace(',', '.'))
                    if extractor.validate_coordinates(x, y):
                        print(f"  ✅ Coord: X={x}, Y={y}")
                    else:
                        print(f"  ❌ Coord: X={x}, Y={y} (hors limites)")
            except (ValueError, IndexError):
                print(f"  ⚠️  Erreur conversion: {match.groups()}")
    
    # Analyse ligne par ligne
    print("\n" + "="*80)
    print("ANALYSE LIGNE PAR LIGNE:")
    lines = corrected_text.split()
    for i, line in enumerate(lines):
        if any(char.isdigit() for char in line) and len(line) > 5:
            print(f"Ligne {i+1}: {line}")

if __name__ == "__main__":
    debug_leve106()

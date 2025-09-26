#!/usr/bin/env python3
import sys
import os
sys.path.append('ANDP_app')

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

def debug_leve101():
    print("=== DEBUG DÉTAILLÉ POUR LEVE101.PNG ===")
    
    extractor = HybridOCRCorrector()
    
    # Extraction du texte brut pour analyse
    img = extractor.preprocess_image('Training Data/leve101.png')
    ocr_result = extractor.ocr.ocr('Training Data/leve101.png')
    raw_texts = " ".join([line[1][0] for page in ocr_result for line in page])
    
    print("TEXTE BRUT OCR:")
    print(raw_texts)
    print("\n" + "="*80)
    
    # Après corrections
    corrected_text = extractor.correct_text_ml(raw_texts)
    for wrong, correct in extractor.BORNE_CORRECTIONS.items():
        corrected_text = corrected_text.replace(wrong, correct)
    
    print("TEXTE APRÈS CORRECTIONS:")
    print(corrected_text)
    print("\n" + "="*80)
    
    # Recherche de toutes les occurrences de B6, B8, BB, B0, BO
    import re
    
    print("RECHERCHE DE PATTERNS SUSPECTS:")
    suspects = ['B6', 'B8', 'BB', 'B0', 'BO', 'B6rnes', 'B8rnes']
    for suspect in suspects:
        matches = list(re.finditer(re.escape(suspect), corrected_text, re.IGNORECASE))
        if matches:
            for match in matches:
                start = max(0, match.start() - 20)
                end = min(len(corrected_text), match.end() + 20)
                context = corrected_text[start:end]
                print(f"  {suspect}: ...{context}...")
    
    print("\n" + "="*80)
    
    # Test des patterns individuels
    patterns = [
        r'(B\d+)(\d{6,7}[.,]?\d{0,3})(\d{6,7}[.,]?\d{0,3})',
        r'(B\d+)[:\s]*[XxEe]?[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+[YyNn]?[:\s]*(\d{6,7}[.,]?\d{0,3})',
        r'(B\d+)[:\s]+(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})',
        r'(B\d+)[^\d]*(\d{6,7}[.,]?\d{0,2})[^\d]*(\d{6,7}[.,]?\d{0,2})'
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"PATTERN {i}: {pattern}")
        matches = list(re.finditer(pattern, corrected_text))
        for match in matches:
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if extractor.validate_coordinates(x, y):
                    print(f"  ✅ {borne_id}: X={x}, Y={y}")
                else:
                    print(f"  ❌ {borne_id}: X={x}, Y={y} (hors limites)")
            except ValueError:
                print(f"  ⚠️  {borne_id}: Erreur conversion {match.group(2)}, {match.group(3)}")
        print()

if __name__ == "__main__":
    debug_leve101()

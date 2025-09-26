#!/usr/bin/env python3
import os
import sys
import cv2
import numpy as np
import re
import pytesseract
from typing import List, Dict, Tuple
from shapely.geometry import Polygon

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class CorrectedFinalExtractorV2(HybridOCRCorrector):
    """Extracteur final corrigé avec corrections auto + validation polygone"""
    
    def __init__(self):
        super().__init__()

    def extract_all_bornes_dynamic(self, img_path: str) -> List[Dict]:
        print(f"🎯 EXTRACTION FINALE DYNAMIQUE v2 pour {os.path.basename(img_path)}")
        print("="*70)

        # 1. Extraction standard
        standard_coords = self.extract_coordinates(img_path)
        standard_coords = self._auto_correct_labels(standard_coords)

        print(f"✅ Extraction standard: {len(standard_coords)} coordonnées")
        for coord in standard_coords:
            print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")

        # 2. Recherche intensive si nécessaire
        enhanced_coords = self._intensive_search_dynamic(img_path, standard_coords)

        # 3. Validation finale + correction polygonale
        final_coords = self._final_validation_dynamic(enhanced_coords)

        return final_coords

    # ---------------------------------------------------
    # CORRECTIONS AUTO (R7 → B7, Bl → B1, etc.)
    # ---------------------------------------------------
    def _auto_correct_labels(self, coords: List[Dict]) -> List[Dict]:
        corrections = {
            "R7": "B7", "87": "B7", "r7": "B7",
            "Bl": "B1", "BT": "B1", "BI": "B1", "BO": "B1", "B|": "B1"
        }
        for c in coords:
            if c['borne'] in corrections:
                print(f"   🔄 Correction automatique: {c['borne']} → {corrections[c['borne']]}")
                c['borne'] = corrections[c['borne']]
    
        # 🚨 Correction spéciale : le tout premier "B" sans numéro = B1
        if coords:
            first = coords[0]
            if first['borne'] == "B":  
                print("   🔄 Correction spéciale: premier 'B' → B1")
                first['borne'] = "B1"
    
        return coords
    
    # ---------------------------------------------------
    # RECHERCHE B1 SPÉCIALE
    # ---------------------------------------------------
    def _search_b1_special(self, all_texts: List[Tuple[str, str]]) -> Dict:
        patterns = [
            r'(B1|Bl|BT|BI|BO|B\|)\s*(\d{6,7}[.,]?\d{0,3})[\s,]+(\d{6,7}[.,]?\d{0,3})',
            r'COORD[O0]NN[EÉ]ES[^\d]*(\d{6,7}[.,]?\d{0,3})[\s,]+(\d{6,7}[.,]?\d{0,3})'
        ]
        for source, text in all_texts:
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    try:
                        if len(match.groups()) == 3:
                            x = float(match.group(2).replace(',', '.'))
                            y = float(match.group(3).replace(',', '.'))
                        else:
                            x = float(match.group(1).replace(',', '.'))
                            y = float(match.group(2).replace(',', '.'))
                        if self.validate_coordinates(x, y):
                            return {
                                'borne': 'B1',
                                'x': x, 'y': y,
                                'confidence': 0.8,
                                'source': f"B1_special_{source}"
                            }
                    except:
                        continue
        return None

    # ---------------------------------------------------
    # RECHERCHE DYNAMIQUE (reprend ton code précédent)
    # ---------------------------------------------------
    def _intensive_search_dynamic(self, img_path: str, standard_coords: List[Dict]) -> List[Dict]:
        all_coords = standard_coords.copy()
        found_bornes = [c['borne'] for c in standard_coords]
        found_numbers = [int(b[1:]) for b in found_bornes if b.startswith("B")]

        if not found_numbers:
            print("❌ Pas de bornes trouvées pour guider la recherche")
            return all_coords

        max_borne = max(found_numbers)
        expected_bornes = list(range(1, max_borne + 1))
        missing_numbers = [n for n in expected_bornes if n not in found_numbers]

        print(f"📊 Bornes trouvées: {found_bornes}")
        print(f"🔍 Bornes manquantes: {[f'B{n}' for n in missing_numbers]}")

        if not missing_numbers:
            return all_coords

        # OCR intensif
        optimized_images = self._create_optimized_images(img_path)
        all_texts = self._extract_text_comprehensive(img_path, optimized_images)

        missing_coords = []

        # Cas spécial B1
        if 1 in missing_numbers:
            b1 = self._search_b1_special(all_texts)
            if b1:
                missing_coords.append(b1)
                missing_numbers.remove(1)

        # Si d'autres manquent → recherche regex + fallback géométrique
        for borne_num in missing_numbers:
            inferred = self._infer_borne_geometrically(borne_num, standard_coords)
            if inferred:
                missing_coords.append(inferred)

        all_coords.extend(missing_coords)
        return all_coords

    # ---------------------------------------------------
    # VALIDATION POLYGONALE
    # ---------------------------------------------------
    def _final_validation_dynamic(self, all_coords: List[Dict]) -> List[Dict]:
        unique_coords = {}
        for c in all_coords:
            if c['borne'] not in unique_coords or c.get('confidence', 0) > unique_coords[c['borne']].get('confidence', 0):
                unique_coords[c['borne']] = c

        coords_sorted = sorted(unique_coords.values(), key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))

        print("\n✅ RÉSULTATS VALIDÉS:")
        for c in coords_sorted:
            print(f"   {c['borne']}: X={c['x']:.2f}, Y={c['y']:.2f} (conf: {c.get('confidence', 1.0):.2f})")

        # Validation polygone
        if len(coords_sorted) >= 3:
            poly = Polygon([(c['x'], c['y']) for c in coords_sorted])
            print(f"📐 Aire polygone: {poly.area:.2f}")
            if not poly.is_valid:
                print("⚠️  Polygone invalide, chevauchements possibles")

        return coords_sorted


def test_corrected_extractor_leve4():
    """Test de l'extracteur corrigé sur leve260.png"""
    
    print("🚀 TEST EXTRACTEUR FINAL CORRIGÉ - leve260.png")
    print("="*60)
    
    extractor = CorrectedFinalExtractorV2()   # ✅ correction ici
    file_path = "Testing Data/leve260.png"
    
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return
    
    # Test de l'extraction corrigée
    corrected_coords = extractor.extract_all_bornes_dynamic(file_path)
    
    print(f"\n📊 RÉSULTATS FINAUX:")
    print(f"   Total coordonnées: {len(corrected_coords)}")
    
    # Analyse de complétude
    borne_numbers = []
    for coord in corrected_coords:
        try:
            num = int(coord['borne'][1:])
            borne_numbers.append(num)
        except:
            continue
    
    borne_numbers.sort()
    completeness = (len(corrected_coords) / 8) * 100
    
    print(f"   📊 Séquence: {[f'B{n}' for n in borne_numbers]}")
    print(f"   📈 Complétude: {completeness:.1f}%")
    
    if borne_numbers:
        expected = list(range(1, max(borne_numbers) + 1))
        missing = [f'B{n}' for n in expected if n not in borne_numbers]
        if missing:
            print(f"   ❌ Manquantes: {', '.join(missing)}")
        else:
            print(f"   ✅ Séquence complète!")
    
    return corrected_coords


if __name__ == "__main__":
    corrected_coords = test_corrected_extractor_leve4()

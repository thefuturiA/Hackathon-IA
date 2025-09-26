#!/usr/bin/env python3
"""
EXTRACTEUR ÉTAPE PAR ÉTAPE
Analyse le texte progressivement pour comprendre les patterns
"""

import os
import sys
import re
from typing import List, Dict

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')
import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class StepByStepExtractor(HybridOCRCorrector):
    """Extracteur qui analyse étape par étape"""
    
    def analyze_text_step_by_step(self, img_path: str):
        """Analyse le texte étape par étape pour comprendre"""
        
        print(f"🔍 ANALYSE ÉTAPE PAR ÉTAPE - {os.path.basename(img_path)}")
        print("="*60)
        
        # Étape 1: Extraire le texte brut
        ocr_result = self.ocr.ocr(img_path)
        combined_text = ' '.join([line[1][0] for page in ocr_result for line in page])
        
        print("ÉTAPE 1: TEXTE BRUT")
        print("-" * 20)
        print(combined_text)
        print()
        
        # Étape 2: Identifier les bornes explicites
        print("ÉTAPE 2: BORNES EXPLICITES")
        print("-" * 20)
        explicit_bornes = re.findall(r'B\d+', combined_text)
        print(f"Bornes explicites trouvées: {set(explicit_bornes)}")
        print()
        
        # Étape 3: Identifier les coordonnées collées
        print("ÉTAPE 3: COORDONNÉES COLLÉES")
        print("-" * 20)
        # Pattern pour coordonnées collées: 6-7 chiffres + 6-7 chiffres
        stuck_pattern = r'(\d{6,7}\.\d{2})(\d{6,7}\.\d{2})'
        stuck_matches = re.findall(stuck_pattern, combined_text)
        print(f"Coordonnées collées trouvées: {len(stuck_matches)}")
        for i, (x, y) in enumerate(stuck_matches):
            print(f"  {i+1}. X={x}, Y={y}")
        print()
        
        # Étape 4: Analyser le contexte autour des coordonnées
        print("ÉTAPE 4: CONTEXTE DES COORDONNÉES")
        print("-" * 20)
        
        # Analyser le texte autour de chaque coordonnée collée
        for i, (x, y) in enumerate(stuck_matches):
            coord_text = f"{x}{y}"
            # Trouver la position dans le texte
            pos = combined_text.find(coord_text)
            if pos != -1:
                # Contexte avant et après
                before = combined_text[max(0, pos-20):pos]
                after = combined_text[pos+len(coord_text):pos+len(coord_text)+20]
                print(f"  Coord {i+1}: ...{before}[{coord_text}]{after}...")
        print()
        
        # Étape 5: Essayer d'associer les coordonnées aux bornes
        print("ÉTAPE 5: ASSOCIATION BORNES-COORDONNÉES")
        print("-" * 20)
        
        coordinates = []
        
        # Association explicite (B2 392922.77699270.66)
        explicit_pattern = r'(B\d+)\s*(\d{6,7}\.\d{2})(\d{6,7}\.\d{2})'
        explicit_matches = re.findall(explicit_pattern, combined_text)
        
        for borne, x, y in explicit_matches:
            try:
                x_val = float(x)
                y_val = float(y)
                if self.validate_coordinates(x_val, y_val):
                    coordinates.append({
                        'borne': borne,
                        'x': x_val,
                        'y': y_val,
                        'type': 'explicit'
                    })
                    print(f"  ✅ {borne}: X={x_val:.2f}, Y={y_val:.2f} (explicite)")
            except:
                continue
        
        # Association par proximité pour les coordonnées orphelines
        print("\n  Coordonnées orphelines (sans borne explicite):")
        
        # Chercher les coordonnées qui ne sont pas déjà associées
        all_coord_pairs = re.findall(r'(\d{6,7}\.\d{2})(\d{6,7}\.\d{2})', combined_text)
        used_coords = [(c['x'], c['y']) for c in coordinates]
        
        orphan_coords = []
        for x, y in all_coord_pairs:
            try:
                x_val = float(x)
                y_val = float(y)
                if (x_val, y_val) not in used_coords and self.validate_coordinates(x_val, y_val):
                    orphan_coords.append((x_val, y_val))
            except:
                continue
        
        print(f"  Coordonnées orphelines: {len(orphan_coords)}")
        for i, (x, y) in enumerate(orphan_coords):
            print(f"    {i+1}. X={x:.2f}, Y={y:.2f}")
        
        # Étape 6: Tentative d'association logique
        print(f"\nÉTAPE 6: ASSOCIATION LOGIQUE")
        print("-" * 20)
        
        # Si on a des coordonnées orphelines, essayer de les associer
        if orphan_coords:
            print("  Tentative d'association par ordre d'apparition...")
            
            # Bornes manquantes probables
            found_bornes = [int(c['borne'][1:]) for c in coordinates]
            expected_bornes = list(range(1, 9))  # B1 à B8
            missing_bornes = [f'B{n}' for n in expected_bornes if n not in found_bornes]
            
            print(f"  Bornes manquantes: {missing_bornes}")
            print(f"  Coordonnées orphelines: {len(orphan_coords)}")
            
            # Association simple par ordre
            for i, (x, y) in enumerate(orphan_coords):
                if i < len(missing_bornes):
                    borne = missing_bornes[i]
                    coordinates.append({
                        'borne': borne,
                        'x': x,
                        'y': y,
                        'type': 'inferred'
                    })
                    print(f"  ✅ {borne}: X={x:.2f}, Y={y:.2f} (inféré)")
        
        # Résumé final
        print(f"\nRÉSUMÉ FINAL:")
        print("-" * 20)
        coordinates.sort(key=lambda c: int(c['borne'][1:]))
        
        for coord in coordinates:
            type_icon = "🔗" if coord['type'] == 'explicit' else "🔍"
            print(f"  {type_icon} {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} ({coord['type']})")
        
        print(f"\nTotal: {len(coordinates)} coordonnées")
        return coordinates

def test_step_by_step():
    """Test étape par étape sur leve212.png"""
    
    extractor = StepByStepExtractor()
    
    # Test sur leve212.png seulement
    coords = extractor.analyze_text_step_by_step("Testing Data/leve28.png")
    
    print(f"\n" + "="*60)
    print(f"🎯 CONCLUSION DE L'ANALYSE")
    print("="*60)
    
    if coords:
        explicit_count = len([c for c in coords if c['type'] == 'explicit'])
        inferred_count = len([c for c in coords if c['type'] == 'inferred'])
        
        print(f"✅ Coordonnées explicites: {explicit_count}")
        print(f"🔍 Coordonnées inférées: {inferred_count}")
        print(f"📊 Total: {len(coords)} / 8 ({len(coords)/8*100:.1f}%)")
        
        # Validation avec les coordonnées de référence
        reference = {
            'B1': (392935.09, 699309.99),
            'B2': (392930.77, 699294.66),
            'B3': (392919.76, 699249.80),
            'B4': (392871.22, 699271.92),
            'B5': (392873.34, 699293.50),
            'B6': (392874.36, 699299.80),
            'B7': (392915.99, 699294.09),
            'B8': (392925.48, 699293.90)
        }
        
        print(f"\n📏 VALIDATION AVEC RÉFÉRENCE:")
        for coord in coords:
            borne = coord['borne']
            if borne in reference:
                ref_x, ref_y = reference[borne]
                distance = ((coord['x'] - ref_x)**2 + (coord['y'] - ref_y)**2)**0.5
                status = "✅" if distance < 5 else "⚠️" if distance < 50 else "❌"
                print(f"  {status} {borne}: distance = {distance:.2f}m")
            else:
                print(f"  ❓ {borne}: pas dans référence")
    
    return coords

if __name__ == "__main__":
    test_step_by_step()

#!/usr/bin/env python3
"""
Extracteur ULTRA-AGRESSIF pour forcer la lecture des coordonnées manquantes
Utilise TOUTES les techniques OCR possibles pour extraire le maximum
"""

import os
import sys
import re
import cv2
import numpy as np
import pytesseract
from typing import List, Dict, Tuple

# Ajouter le chemin du projet Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ANDP.settings')

import django
django.setup()

from ANDP_app.services.ocr_extraction import HybridOCRCorrector

class UltraAggressiveExtractor(HybridOCRCorrector):
    """
    Extracteur ULTRA-AGRESSIF qui utilise TOUTES les techniques OCR
    pour forcer la lecture des coordonnées manquantes
    """
    
    def extract_coordinates_ultra_aggressive(self, img_path: str) -> List[Dict]:
        """Extraction ULTRA-AGRESSIVE avec TOUTES les techniques OCR"""
        
        print(f"🔥 EXTRACTION ULTRA-AGRESSIVE pour {os.path.basename(img_path)}")
        print("="*60)
        print("🚀 TOUTES les techniques OCR pour forcer la lecture")
        
        # Phase 1: Extraction ULTRA-AGRESSIVE avec toutes les techniques
        all_texts = self._extract_text_ultra_aggressive(img_path)
        
        # Phase 2: Extraction avec patterns ULTRA-AGRESSIFS
        coordinates = []
        for source, text in all_texts:
            coords = self._extract_with_ultra_aggressive_patterns(text, source)
            coordinates.extend(coords)
        
        # Phase 3: Déduplication intelligente
        coordinates = self._smart_deduplication(coordinates)
        
        # Phase 4: Validation finale
        final_coords = self._ultra_aggressive_validation(coordinates)
        
        return final_coords
    
    def _extract_text_ultra_aggressive(self, img_path: str) -> List[Tuple[str, str]]:
        """Extraction de texte ULTRA-AGRESSIVE avec TOUTES les techniques"""
        
        print(f"\n🔥 EXTRACTION TEXTE ULTRA-AGRESSIVE:")
        all_texts = []
        
        # Charger l'image
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. PaddleOCR standard
        try:
            ocr_result = self.ocr.ocr(img_path)
            paddle_text = " ".join([line[1][0] for page in ocr_result for line in page])
            corrected_paddle = self.correct_text_ml(paddle_text)
            corrected_paddle = self.apply_borne_corrections(corrected_paddle)
            all_texts.append(("PaddleOCR", corrected_paddle))
            print(f"   ✅ PaddleOCR: {len(corrected_paddle)} caractères")
        except Exception as e:
            print(f"   ❌ PaddleOCR échoué: {e}")
        
        # 2. Images préprocessées ULTRA-AGRESSIVES
        processed_images = self._create_ultra_aggressive_images(gray)
        
        # 3. Tesseract avec TOUS les PSM sur TOUTES les images
        psm_modes = [3, 4, 6, 7, 8, 9, 10, 11, 12, 13]
        
        for img_name, processed_img in processed_images:
            for psm in psm_modes:
                try:
                    config = f"--psm {psm} -c tessedit_char_whitelist=0123456789.,B "
                    text = pytesseract.image_to_string(processed_img, config=config)
                    if text.strip() and len(text.strip()) > 10:  # Seulement si texte significatif
                        corrected_text = self.correct_text_ml(text)
                        corrected_text = self.apply_borne_corrections(corrected_text)
                        all_texts.append((f"Tesseract_{img_name}_PSM{psm}", corrected_text))
                        print(f"   ✅ Tesseract {img_name} PSM{psm}: {len(corrected_text)} caractères")
                except Exception as e:
                    continue  # Ignorer les erreurs silencieusement
        
        print(f"   📊 Total extractions: {len(all_texts)}")
        return all_texts
    
    def _create_ultra_aggressive_images(self, gray: np.ndarray) -> List[Tuple[str, np.ndarray]]:
        """Crée des images préprocessées ULTRA-AGRESSIVES"""
        
        images = []
        
        # Image originale
        images.append(("original", gray))
        
        # Débruitage agressif
        denoised = cv2.fastNlMeansDenoising(gray, h=30)
        images.append(("denoised", denoised))
        
        # Amélioration du contraste CLAHE
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        images.append(("enhanced", enhanced))
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        images.append(("binary", binary))
        
        # Binarisation OTSU
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        images.append(("otsu", otsu))
        
        # Morphologie pour nettoyer
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        images.append(("cleaned", cleaned))
        
        # Dilatation pour épaissir le texte
        dilated = cv2.dilate(binary, kernel, iterations=1)
        images.append(("dilated", dilated))
        
        # Érosion pour affiner
        eroded = cv2.erode(binary, kernel, iterations=1)
        images.append(("eroded", eroded))
        
        # Combinaison débruitage + CLAHE + binarisation
        combo = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        images.append(("combo", combo))
        
        # Inversion pour texte blanc sur fond noir
        inverted = cv2.bitwise_not(binary)
        images.append(("inverted", inverted))
        
        return images
    
    def _extract_with_ultra_aggressive_patterns(self, text: str, source: str) -> List[Dict]:
        """Extraction avec patterns ULTRA-AGRESSIFS"""
        
        coordinates = []
        
        # Pattern 1: Bornes explicites normales (B1 X Y)
        pattern1 = r'(B\d+)[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    coordinates.append({
                        'borne': borne_id,
                        'x': x,
                        'y': y,
                        'confidence': 1.0,
                        'source': f'{source}_explicit_normal',
                        'pattern': 'explicit_normal'
                    })
            except ValueError:
                continue
        
        # Pattern 2: Coordonnées collées (B4 432839.05704141.19)
        pattern2 = r'(B\d+)[:\s]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})'
        for match in re.finditer(pattern2, text, re.IGNORECASE):
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    coordinates.append({
                        'borne': borne_id,
                        'x': x,
                        'y': y,
                        'confidence': 0.9,
                        'source': f'{source}_explicit_stuck',
                        'pattern': 'explicit_stuck'
                    })
            except ValueError:
                continue
        
        # Pattern 3: Coordonnées ULTRA-COLLÉES (plus agressif)
        pattern3 = r'(B\d+)(\d{6,7}[.,]?\d{0,2})(\d{6,7}[.,]?\d{0,2})'
        for match in re.finditer(pattern3, text, re.IGNORECASE):
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si pas déjà trouvé
                    already_found = any(c['borne'] == borne_id for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': borne_id,
                            'x': x,
                            'y': y,
                            'confidence': 0.8,
                            'source': f'{source}_ultra_stuck',
                            'pattern': 'ultra_stuck'
                        })
            except ValueError:
                continue
        
        # Pattern 4: B1 implicite avant B2
        pattern4 = r'(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})\s+B2'
        for match in re.finditer(pattern4, text, re.IGNORECASE):
            try:
                x = float(match.group(1).replace(',', '.'))
                y = float(match.group(2).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    already_found = any(c['borne'] == 'B1' for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': 'B1',
                            'x': x,
                            'y': y,
                            'confidence': 0.8,
                            'source': f'{source}_implicit_b1',
                            'pattern': 'implicit_b1'
                        })
            except ValueError:
                continue
        
        # Pattern 5: Recherche ULTRA-AGRESSIVE de toutes les paires de coordonnées
        pattern5 = r'(\d{6,7}[.,]?\d{0,3})\s*[,\s]\s*(\d{6,7}[.,]?\d{0,3})'
        all_coord_pairs = []
        for match in re.finditer(pattern5, text):
            try:
                x = float(match.group(1).replace(',', '.'))
                y = float(match.group(2).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    all_coord_pairs.append((x, y, match.start(), match.end()))
            except ValueError:
                continue
        
        # Associer les paires aux bornes par proximité dans le texte
        for x, y, start, end in all_coord_pairs:
            # Chercher une borne dans les 50 caractères avant
            text_before = text[max(0, start-50):start]
            borne_match = re.search(r'(B\d+)', text_before[::-1])  # Recherche inverse
            
            if borne_match:
                borne_id = borne_match.group(1)[::-1]  # Inverser le résultat
                # Vérifier si pas déjà trouvé avec meilleure confiance
                existing = next((c for c in coordinates if c['borne'] == borne_id), None)
                if not existing or existing['confidence'] < 0.7:
                    if existing:
                        coordinates.remove(existing)
                    coordinates.append({
                        'borne': borne_id,
                        'x': x,
                        'y': y,
                        'confidence': 0.7,
                        'source': f'{source}_proximity_association',
                        'pattern': 'proximity'
                    })
        
        if coordinates:
            print(f"   🔥 {source}: {len(coordinates)} coordonnées trouvées")
            for coord in coordinates:
                print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} ({coord['pattern']})")
        else:
            print(f"   ❌ {source}: Aucune coordonnée trouvée")
        
        return coordinates
    
    def _smart_deduplication(self, coordinates: List[Dict]) -> List[Dict]:
        """Déduplication intelligente basée sur la confiance"""
        
        print(f"\n🔍 DÉDUPLICATION ULTRA-AGRESSIVE:")
        print(f"   Coordonnées brutes: {len(coordinates)}")
        
        if not coordinates:
            return []
        
        # Grouper par borne
        borne_groups = {}
        for coord in coordinates:
            borne = coord['borne']
            if borne not in borne_groups:
                borne_groups[borne] = []
            borne_groups[borne].append(coord)
        
        # Sélectionner la meilleure pour chaque borne
        deduplicated = []
        for borne, coords in borne_groups.items():
            # Trier par confiance décroissante
            coords.sort(key=lambda c: c['confidence'], reverse=True)
            best = coords[0]
            
            # Si plusieurs candidats avec confiance similaire, vérifier cohérence spatiale
            if len(coords) > 1:
                similar_confidence = [c for c in coords if abs(c['confidence'] - best['confidence']) < 0.1]
                if len(similar_confidence) > 1:
                    # Prendre celui avec les coordonnées les plus "normales"
                    for candidate in similar_confidence:
                        if candidate['pattern'] in ['explicit_normal', 'explicit_stuck']:
                            best = candidate
                            break
            
            deduplicated.append(best)
            print(f"   ✅ {borne}: {best['pattern']} (conf: {best['confidence']:.2f}) - {best['source']}")
        
        print(f"   Coordonnées déduplicées: {len(deduplicated)}")
        return deduplicated
    
    def _ultra_aggressive_validation(self, coordinates: List[Dict]) -> List[Dict]:
        """Validation finale ULTRA-AGRESSIVE"""
        
        print(f"\n✅ VALIDATION FINALE ULTRA-AGRESSIVE:")
        
        if not coordinates:
            print(f"   ❌ Aucune coordonnée à valider")
            return []
        
        # Validation UTM
        valid_coords = []
        for coord in coordinates:
            if self.validate_coordinates(coord['x'], coord['y']):
                valid_coords.append(coord)
            else:
                print(f"   ❌ {coord['borne']} rejeté: coordonnées invalides")
        
        # Tri par numéro de borne
        valid_coords.sort(key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))
        
        print(f"   📍 Coordonnées finales ULTRA-AGRESSIVES: {len(valid_coords)}")
        for coord in valid_coords:
            conf = coord.get('confidence', 1.0)
            pattern = coord.get('pattern', 'unknown')
            source = coord.get('source', 'unknown')
            print(f"      {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f} (conf: {conf:.2f}, {pattern})")
        
        # Analyse de complétude
        borne_numbers = []
        for coord in valid_coords:
            try:
                num = int(coord['borne'][1:])
                borne_numbers.append(num)
            except:
                continue
        
        borne_numbers.sort()
        completeness = (len(valid_coords) / 8) * 100
        
        print(f"\n📊 ANALYSE ULTRA-AGRESSIVE:")
        print(f"   Séquence trouvée: {[f'B{n}' for n in borne_numbers]}")
        print(f"   Complétude: {completeness:.1f}%")
        
        if borne_numbers:
            expected = list(range(1, max(borne_numbers) + 1))
            missing = [f'B{n}' for n in expected if n not in borne_numbers]
            if missing:
                print(f"   ❌ Encore manquantes: {', '.join(missing)}")
                print(f"   💡 Ces bornes sont probablement illisibles dans l'image")
            else:
                print(f"   ✅ Séquence complète trouvée!")
        
        return valid_coords

def test_ultra_aggressive_on_critical_files():
    """Test de l'extracteur ULTRA-AGRESSIF sur les fichiers critiques"""
    
    print("🔥 TEST EXTRACTEUR ULTRA-AGRESSIF")
    print("="*60)
    print("🚀 FORCER la lecture des coordonnées manquantes")
    
    extractor = UltraAggressiveExtractor()
    
    # Fichiers critiques avec coordonnées manquantes
    test_files = [
        "Testing Data/leve212.png",  # B1, B3, B4, B5 manquantes
        "Testing Data/leve275.png",  # B1, B2 manquantes
        "Testing Data/leve214.png",  # B3, B4, B5 manquantes
    ]
    
    results = {}
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ Fichier non trouvé: {file_path}")
            continue
        
        filename = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"🔥 TEST ULTRA-AGRESSIF: {filename}")
        print(f"{'='*60}")
        
        try:
            coords = extractor.extract_coordinates_ultra_aggressive(file_path)
            
            # Analyse de complétude
            borne_numbers = []
            for coord in coords:
                try:
                    num = int(coord['borne'][1:])
                    borne_numbers.append(num)
                except:
                    continue
            
            borne_numbers.sort()
            completeness = (len(coords) / 8) * 100
            
            results[filename] = {
                'coords': coords,
                'count': len(coords),
                'completeness': completeness,
                'sequence': [f'B{n}' for n in borne_numbers]
            }
            
            print(f"\n🎯 RÉSULTAT ULTRA-AGRESSIF {filename}:")
            print(f"   Coordonnées trouvées: {len(coords)}")
            print(f"   Séquence: {[f'B{n}' for n in borne_numbers]}")
            print(f"   Complétude: {completeness:.1f}%")
            
            # Comparaison avec l'extracteur PUR
            if filename == "leve212.png":
                print(f"   📊 vs PUR: {len(coords)} vs 4 (+{len(coords)-4})")
            elif filename == "leve275.png":
                print(f"   📊 vs PUR: {len(coords)} vs 2 (+{len(coords)-2})")
            elif filename == "leve214.png":
                print(f"   📊 vs PUR: {len(coords)} vs 3 (+{len(coords)-3})")
            
        except Exception as e:
            print(f"❌ Erreur sur {filename}: {e}")
            results[filename] = {'error': str(e)}
    
    # Résumé final
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ ULTRA-AGRESSIF")
    print(f"{'='*60}")
    
    for filename, result in results.items():
        if 'error' in result:
            print(f"❌ {filename}: ERREUR")
        else:
            status = "🏆" if result['completeness'] >= 100 else "✅" if result['completeness'] >= 75 else "👍" if result['completeness'] >= 50 else "⚠️"
            print(f"{status} {filename}: {result['count']} coords ({result['completeness']:.1f}%)")
            print(f"      Séquence: {result['sequence']}")
    
    print(f"\n💡 STRATÉGIE POUR LES COORDONNÉES MANQUANTES:")
    print(f"   🔥 Utiliser l'extracteur ULTRA-AGRESSIF pour maximiser la lecture")
    print(f"   📝 Améliorer le préprocessing d'image pour les cas difficiles")
    print(f"   🔍 Analyser manuellement les images pour les bornes illisibles")
    print(f"   ✅ Accepter que certaines coordonnées soient réellement illisibles")
    
    return results

if __name__ == "__main__":
    results = test_ultra_aggressive_on_critical_files()

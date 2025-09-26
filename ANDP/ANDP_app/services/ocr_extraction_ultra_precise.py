import cv2
import numpy as np
import pytesseract
import re
from paddleocr import PaddleOCR
from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class UltraPreciseCoordinateExtractor:
    """
    Extracteur ultra-précis pour tableaux de coordonnées topographiques
    Basé sur l'algorithme FixedUltraPreciseExtractor optimisé
    
    Mission: Détecter le tableau de coordonnées → OCR → Extraction précise → Validation
    """

    BENIN_UTM_BOUNDS = {
        'X_MIN': 200000, 'X_MAX': 500000,
        'Y_MIN': 600000, 'Y_MAX': 1400000
    }

    OCR_CORRECTIONS = str.maketrans({
        'O': '0', 'o': '0', 'I': '1', 'l': '1', 'S': '5', 'G': '6'
    })

    def __init__(self, corrector_model_path: str = None, use_gpu: bool = False):
        # OCR
        self.ocr = PaddleOCR(lang='en', use_angle_cls=True, use_gpu=False)
        # Correcteur ML
        if corrector_model_path:
            self.device = 'cuda' if use_gpu and torch.cuda.is_available() else 'cpu'
            self.tokenizer = AutoTokenizer.from_pretrained(corrector_model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(corrector_model_path).to(self.device)
        else:
            self.model = None

    def preprocess_image(self, img_path: str) -> np.ndarray:
        """Préprocessing optimisé pour tableaux de coordonnées"""
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        return cleaned

    def correct_text_ml(self, text: str) -> str:
        """Corrige le texte OCR avec le modèle ML (si disponible)"""
        if not self.model:
            return text.translate(self.OCR_CORRECTIONS)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.device)
        outputs = self.model.generate(**inputs, max_length=512)
        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return corrected

    def apply_borne_corrections(self, text: str) -> str:
        """Applique les corrections spécifiques aux bornes"""
        corrections = {
            'BB': 'B8', 'B0': 'B8', 'BO': 'B8',
            'Bl': 'B1', 'B|': 'B1', 'B!': 'B1',
            'B5': 'B5', 'BS': 'B5', 'B6': 'B6',
            'B7': 'B7', 'B8': 'B8', 'B9': 'B9'
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        return text

    def extract_coordinates(self, img_path: str) -> List[Dict]:
        """
        Extraction ultra-précise des coordonnées du tableau
        Pipeline: Détection zone → OCR → Patterns multiples → Validation
        """
        
        print(f"🎯 EXTRACTION ULTRA-PRÉCISE pour {img_path}")
        
        # Extraction OCR standard
        img = self.preprocess_image(img_path)
        ocr_result = self.ocr.ocr(img_path)
        raw_text = " ".join([line[1][0] for page in ocr_result for line in page])
        
        print(f"📝 Texte OCR brut: {raw_text[:200]}...")
        
        # Nettoyer et corriger le texte
        corrected_text = self.correct_text_ml(raw_text)
        corrected_text = self.apply_borne_corrections(corrected_text)
        
        print(f"📝 Texte corrigé: {corrected_text[:200]}...")
        
        # Extraction avec patterns ultra-précis
        coordinates = self._extract_with_ultra_patterns(corrected_text)
        
        # Post-traitement pour associer les coordonnées isolées
        coordinates = self._associate_isolated_coordinates(corrected_text, coordinates)
        
        # Validation et tri final
        final_coords = self._validate_and_sort(coordinates)
        
        print(f"✅ RÉSULTATS FINAUX: {len(final_coords)} coordonnées extraites")
        for coord in final_coords:
            print(f"   {coord['borne']}: X={coord['x']:.2f}, Y={coord['y']:.2f}")
        
        return final_coords

    def _extract_with_ultra_patterns(self, text: str) -> List[Dict]:
        """Extraction avec patterns ultra-précis pour tous les formats"""
        
        coordinates = []
        
        # Pattern 1: Bornes explicites normales (B1-B5)
        pattern1 = r'(B[1-5])[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})'
        matches1 = re.finditer(pattern1, text, re.IGNORECASE)

        for match in matches1:
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
                        'source': 'explicit_normal'
                    })
                    print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (normal)")
            except ValueError:
                continue
        
        # Pattern 2: Bornes avec coordonnées COLLÉES (B4 432839.05704141.19)
        pattern2 = r'(B\d+)[:\s]*(\d{6}[.,]?\d{2})(\d{6}[.,]?\d{2})'
        matches2 = re.finditer(pattern2, text, re.IGNORECASE)
        
        for match in matches2:
            borne_id = match.group(1)
            try:
                x = float(match.group(2).replace(',', '.'))
                y = float(match.group(3).replace(',', '.'))
                if self.validate_coordinates(x, y):
                    # Vérifier si cette borne n'est pas déjà trouvée
                    already_found = any(c['borne'] == borne_id for c in coordinates)
                    if not already_found:
                        coordinates.append({
                            'borne': borne_id,
                            'x': x,
                            'y': y,
                            'confidence': 0.9,
                            'source': 'explicit_stuck'
                        })
                        print(f"   ✅ {borne_id}: X={x:.2f}, Y={y:.2f} (collées)")
            except ValueError:
                continue
        
        # Pattern 3: Séquences de coordonnées pour capturer B1, B2, etc.
        pattern3 = r'(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})'
        matches3 = re.finditer(pattern3, text)
        
        for match in matches3:
            try:
                # Première paire de coordonnées
                x1 = float(match.group(1).replace(',', '.'))
                y1 = float(match.group(2).replace(',', '.'))
                # Deuxième paire de coordonnées
                x2 = float(match.group(3).replace(',', '.'))
                y2 = float(match.group(4).replace(',', '.'))
                
                # Assigner aux bornes manquantes
                found_bornes = [c['borne'] for c in coordinates]
                
                if self.validate_coordinates(x1, y1) and 'B1' not in found_bornes:
                    coordinates.append({
                        'borne': 'B1',
                        'x': x1,
                        'y': y1,
                        'confidence': 0.8,
                        'source': 'sequence_pattern'
                    })
                    print(f"   ✅ B1: X={x1:.2f}, Y={y1:.2f} (séquence)")
                
                if self.validate_coordinates(x2, y2) and 'B2' not in found_bornes:
                    coordinates.append({
                        'borne': 'B2',
                        'x': x2,
                        'y': y2,
                        'confidence': 0.8,
                        'source': 'sequence_pattern'
                    })
                    print(f"   ✅ B2: X={x2:.2f}, Y={y2:.2f} (séquence)")
                    
            except ValueError:
                continue
        
        return coordinates

    def _associate_isolated_coordinates(self, text: str, existing_coords: List[Dict]) -> List[Dict]:
        """Associe les coordonnées isolées aux bornes manquantes (conservative approach)"""

        # Identifier les bornes déjà trouvées
        found_bornes = [c['borne'] for c in existing_coords]

        # Seulement chercher les bornes manquantes dans la séquence standard B1-B4
        # Éviter de créer B5+ à moins d'évidence claire
        standard_bornes = ['B1', 'B2', 'B3', 'B4']
        missing_standard = [b for b in standard_bornes if b not in found_bornes]

        if not missing_standard:
            return existing_coords  # Toutes les bornes standard sont trouvées

        # Chercher des patterns spécifiques pour les bornes manquantes
        enhanced_coords = existing_coords.copy()

        # Pattern pour coordonnées sans borne explicite, près d'autres coordonnées
        coord_context_pattern = r'(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})(?:\s+(?:\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3}))?'

        matches = re.finditer(coord_context_pattern, text)

        for match in matches:
            try:
                x1 = float(match.group(1).replace(',', '.'))
                y1 = float(match.group(2).replace(',', '.'))

                if self.validate_coordinates(x1, y1):
                    # Vérifier si cette coordonnée n'est pas déjà trouvée
                    is_duplicate = any(
                        abs(c['x'] - x1) < 1 and abs(c['y'] - y1) < 1
                        for c in existing_coords + enhanced_coords
                    )

                    if not is_duplicate and missing_standard:
                        borne_id = missing_standard.pop(0)
                        enhanced_coords.append({
                            'borne': borne_id,
                            'x': x1,
                            'y': y1,
                            'confidence': 0.7,
                            'source': 'context_association'
                        })
                        print(f"   ✅ {borne_id}: X={x1:.2f}, Y={y1:.2f} (contexte)")

                # Si il y a une deuxième paire dans le match
                if match.group(3) and match.group(4) and missing_standard:
                    x2 = float(match.group(3).replace(',', '.'))
                    y2 = float(match.group(4).replace(',', '.'))

                    if self.validate_coordinates(x2, y2):
                        is_duplicate = any(
                            abs(c['x'] - x2) < 1 and abs(c['y'] - y2) < 1
                            for c in existing_coords + enhanced_coords
                        )

                        if not is_duplicate:
                            borne_id = missing_standard.pop(0)
                            enhanced_coords.append({
                                'borne': borne_id,
                                'x': x2,
                                'y': y2,
                                'confidence': 0.7,
                                'source': 'context_association'
                            })
                            print(f"   ✅ {borne_id}: X={x2:.2f}, Y={y2:.2f} (contexte)")

            except (ValueError, IndexError):
                continue

        return enhanced_coords

    def _validate_and_sort(self, coordinates: List[Dict]) -> List[Dict]:
        """Validation et tri final"""
        
        # Supprimer les doublons (garder le plus confiant)
        unique_coords = {}
        for coord in coordinates:
            borne = coord['borne']
            if borne not in unique_coords or coord['confidence'] > unique_coords[borne]['confidence']:
                unique_coords[borne] = coord
        
        # Convertir en liste et trier
        final_coords = list(unique_coords.values())
        final_coords.sort(key=lambda c: int(re.search(r'B(\d+)', c['borne']).group(1)))
        
        return final_coords

    @classmethod
    def validate_coordinates(cls, x: float, y: float) -> bool:
        """Validation des coordonnées dans les limites du Bénin"""
        return (cls.BENIN_UTM_BOUNDS['X_MIN'] <= x <= cls.BENIN_UTM_BOUNDS['X_MAX'] and
                cls.BENIN_UTM_BOUNDS['Y_MIN'] <= y <= cls.BENIN_UTM_BOUNDS['Y_MAX'])

    @staticmethod
    def is_polygon_closed(coordinates: List[Dict], tolerance: float = 1.0) -> bool:
        """Vérifie si le polygone est fermé"""
        if len(coordinates) < 3:
            return False
        first, last = coordinates[0], coordinates[-1]
        distance = ((first['x'] - last['x'])**2 + (first['y'] - last['y'])**2)**0.5
        return distance <= tolerance


# Alias pour compatibilité avec l'ancien code
HybridOCRCorrector = UltraPreciseCoordinateExtractor
PaddleOCROracle = UltraPreciseCoordinateExtractor
LayoutLMOracle = UltraPreciseCoordinateExtractor

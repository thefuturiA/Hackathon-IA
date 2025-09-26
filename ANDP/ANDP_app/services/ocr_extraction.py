import cv2
import numpy as np
import pytesseract
import re
from paddleocr import PaddleOCR
from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class HybridOCRCorrector:
    """
    OCR hybride + correcteur ML pour levées topographiques.
    Extraction directe des coordonnées fiables.
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
        # Corrections simples
        corrections = {
            'BB': 'B8',
            'B0': 'B8', 
            'BO': 'B8',
            'Bl': 'B1',
            'B|': 'B1',
        }
        
        for wrong, correct in corrections.items():
            text = text.replace(wrong, correct)
        
        # Correction spéciale pour 88 -> B8 (seulement si suivi de coordonnées)
        text = re.sub(r'\b88\s+(\d{6,7}[.,]?\d{0,3})\s+(\d{6,7}[.,]?\d{0,3})', r'B8 \1 \2', text)
        
        return text

    def extract_coordinates(self, img_path: str) -> List[Dict]:
        img = self.preprocess_image(img_path)
        # OCR hybride
        ocr_result = self.ocr.ocr(img_path)
        raw_texts = " ".join([line[1][0] for page in ocr_result for line in page])
        pyt_text = " ".join(pytesseract.image_to_string(img, config="--psm 6").splitlines())
        combined_text = raw_texts + " " + pyt_text
        # Correction ML ou rule-based
        combined_text = self.correct_text_ml(combined_text)
        
        # Corrections spécifiques pour les bornes mal reconnues
        combined_text = self.apply_borne_corrections(combined_text)
        
        print(f"Texte extrait: {combined_text[:200]}...")  # Debug
        
        # Patterns multiples pour capturer différents formats
        coordinates = []
        patterns = [
            # Pattern collé: B1401374.38712334.71 (sans espaces)
            r'(B\d+)(\d{6,7}[.,]?\d{0,3})(\d{6,7}[.,]?\d{0,3})',
            # Pattern principal: B1 X Y
            r'(B\d+)[:\s]*[XxEe]?[:\s]*(\d{6,7}[.,]?\d{0,3})[,\s]+[YyNn]?[:\s]*(\d{6,7}[.,]?\d{0,3})',
            # Pattern alternatif: B1: 401374.38 712334.71
            r'(B\d+)[:\s]+(\d{6,7}[.,]?\d{0,3})[,\s]+(\d{6,7}[.,]?\d{0,3})',
            # Pattern simple: B1 401374.38 712334.71
            r'(B\d+)[^\d]*(\d{6,7}[.,]?\d{0,2})[^\d]*(\d{6,7}[.,]?\d{0,2})'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, combined_text):
                borne_id = match.group(1)
                try:
                    x = float(match.group(2).replace(',', '.'))
                    y = float(match.group(3).replace(',', '.'))
                    if self.validate_coordinates(x, y):
                        coord = {'borne': borne_id, 'x': x, 'y': y}
                        # Éviter les doublons
                        if not any(c['borne'] == borne_id for c in coordinates):
                            coordinates.append(coord)
                            print(f"Trouvé: {borne_id} X={x} Y={y}")
                except ValueError:
                    continue

        # Supprimer doublons et trier
        seen = set()
        unique_coords = []
        for c in coordinates:
            if c['borne'] not in seen:
                seen.add(c['borne'])
                unique_coords.append(c)
        unique_coords.sort(key=lambda c: int(c['borne'][1:]))
        return unique_coords

    @classmethod
    def validate_coordinates(cls, x: float, y: float) -> bool:
        return (cls.BENIN_UTM_BOUNDS['X_MIN'] <= x <= cls.BENIN_UTM_BOUNDS['X_MAX'] and
                cls.BENIN_UTM_BOUNDS['Y_MIN'] <= y <= cls.BENIN_UTM_BOUNDS['Y_MAX'])

    @staticmethod
    def is_polygon_closed(coordinates: List[Dict], tolerance: float = 1.0) -> bool:
        if len(coordinates) < 3:
            return False
        first, last = coordinates[0], coordinates[-1]
        distance = ((first['x'] - last['x'])**2 + (first['y'] - last['y'])**2)**0.5
        return distance <= tolerance


# Alias pour compatibilité
PaddleOCROracle = HybridOCRCorrector
LayoutLMOracle = HybridOCRCorrector

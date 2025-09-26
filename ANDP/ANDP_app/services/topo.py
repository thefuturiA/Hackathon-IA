from .ocr_extraction import HybridOCRCorrector
from typing import List, Dict

class TopographyService:
    """
    Service d'orchestration pour extraire les coordonnées des levées
    en utilisant l'OCR hybride avec correction ML.
    """

    def __init__(self, debug=False):
        self.ocr_extractor = HybridOCRCorrector()
        self.debug = debug

    def process_survey_images(self, image_paths: List[str]) -> Dict:
        """
        Traite une liste d'images et retourne toutes les coordonnées extraites
        """
        all_coordinates = []
        for img_path in image_paths:
            if self.debug:
                print(f"Traitement de {img_path}")
            coords = self.ocr_extractor.extract_coordinates(img_path)
            all_coordinates.extend(coords)

        # Supprimer doublons exacts au cas où plusieurs images contiennent la même borne
        unique_coords = {}
        for coord in all_coordinates:
            if coord['borne'] not in unique_coords:
                unique_coords[coord['borne']] = coord

        # Retourner trié par numéro de borne
        final_coords = list(unique_coords.values())
        final_coords.sort(key=lambda c: int(c['borne'][1:]))

        return {"coordinates": final_coords}
    
    def process_single_image(self, image_path: str) -> Dict:
        """
        Traite une seule image et retourne les coordonnées extraites
        """
        if self.debug:
            print(f"Traitement de {image_path}")
        coords = self.ocr_extractor.extract_coordinates(image_path)
        return {"coordinates": coords}

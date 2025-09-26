"""
Intégration OCR avancée avec vérification spatiale
Connecte l'extraction de coordonnées avec l'analyse spatiale ANDF
"""

import tempfile
import os
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.utils import timezone
from ..models import PublicUpload, OCRResult, Parcel
from .ocr_extraction_ultra_precise import UltraPreciseCoordinateExtractor
from .spatial_verification import IntelligentSpatialAnalyzer
import logging

logger = logging.getLogger(__name__)


class OCRSpatialIntegrator:
    """
    Intégrateur OCR + Analyse Spatiale
    Workflow complet: Upload → OCR → Coordonnées → Polygone → Vérification ANDF
    """
    
    def __init__(self):
        self.ocr_extractor = UltraPreciseCoordinateExtractor()
        self.spatial_analyzer = IntelligentSpatialAnalyzer()
    
    def process_upload_complete(self, upload: PublicUpload):
        """
        Traitement complet d'un upload: OCR + Spatial
        
        Args:
            upload: Instance PublicUpload à traiter
        
        Returns:
            dict: Résultats complets du traitement
        """
        try:
            # 1. EXTRACTION OCR
            upload.add_log_entry('ocr_start', 'Début extraction OCR')
            upload.processing_status = 'ocr_processing'
            upload.save()
            
            ocr_result = self._extract_coordinates(upload)
            
            # 2. CRÉATION DE GÉOMÉTRIE
            upload.add_log_entry('geometry_start', 'Création de la géométrie')
            upload.processing_status = 'geometry_created'
            upload.save()
            
            parcel = self._create_parcel_geometry(upload, ocr_result)
            
            # 3. VÉRIFICATION SPATIALE INTELLIGENTE
            if parcel and parcel.geometry:
                upload.add_log_entry('spatial_verification_start', 'Début vérification spatiale')
                upload.processing_status = 'spatial_verification'
                upload.save()
                
                verification = self.spatial_analyzer.analyze_parcel(parcel)
                
                # 4. FINALISATION
                upload.processing_status = 'completed'
                upload.processed = True
                upload.completed_at = timezone.now()
                upload.save()
                
                return self._build_complete_response(upload, ocr_result, parcel, verification)
            else:
                upload.processing_status = 'error'
                upload.error_message = "Impossible de créer la géométrie de la parcelle"
                upload.save()
                raise ValueError("Géométrie invalide")
                
        except Exception as e:
            logger.error(f"Erreur traitement complet: {e}")
            upload.processing_status = 'error'
            upload.error_message = str(e)
            upload.save()
            raise
    
    def _extract_coordinates(self, upload: PublicUpload):
        """
        Extraction des coordonnées via OCR
        """
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.file.name)[1]) as tmp_file:
            for chunk in upload.file.chunks():
                tmp_file.write(chunk)
            tmp_file.flush()
            tmp_path = tmp_file.name
        
        try:
            # Extraction OCR
            coordinates = self.ocr_extractor.extract_coordinates(tmp_path)
            
            # Validation des coordonnées
            validated_coords = []
            for coord in coordinates:
                if self.ocr_extractor.validate_coordinates(coord['x'], coord['y']):
                    validated_coords.append(coord)
            
            # Créer l'objet OCRResult
            ocr_result = OCRResult.objects.create(
                upload=upload,
                raw_text="",  # Le HybridOCRCorrector ne retourne pas le texte brut
                coordinates_found=len(coordinates),
                extracted_coordinates=coordinates,
                validated_coordinates=validated_coords,
                confidence_score=len(validated_coords) / max(len(coordinates), 1) if coordinates else 0,
                extraction_method='hybrid_corrector'
            )
            
            upload.add_log_entry(
                'ocr_completed',
                f'OCR terminé: {len(validated_coords)} coordonnées valides sur {len(coordinates)} extraites',
                {
                    'total_extracted': len(coordinates),
                    'valid_coordinates': len(validated_coords),
                    'confidence': ocr_result.confidence_score
                }
            )
            
            return ocr_result
            
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _create_parcel_geometry(self, upload: PublicUpload, ocr_result: OCRResult):
        """
        Crée la géométrie de la parcelle à partir des coordonnées
        """
        validated_coords = ocr_result.validated_coordinates
        
        if len(validated_coords) < 3:
            upload.add_log_entry(
                'geometry_error',
                f'Insuffisant de coordonnées valides: {len(validated_coords)} (minimum 3 requis)'
            )
            return None
        
        try:
            # Créer le polygone
            coord_pairs = [(coord['x'], coord['y']) for coord in validated_coords]
            
            # Vérifier si le polygone est fermé
            if coord_pairs[0] != coord_pairs[-1]:
                coord_pairs.append(coord_pairs[0])  # Fermer le polygone
            
            # Créer la géométrie
            polygon = Polygon(coord_pairs, srid=32631)
            
            # Calculer les métriques
            area = polygon.area  # m²
            perimeter = polygon.length  # m
            centroid = polygon.centroid
            
            # Créer l'objet Parcel
            parcel = Parcel.objects.create(
                upload=upload,
                geometry=polygon,
                centroid=centroid,
                area=area,
                perimeter=perimeter,
                status='invalid'  # Sera mis à jour après vérification
            )
            
            upload.add_log_entry(
                'geometry_created',
                f'Géométrie créée: {area:.2f} m² ({len(validated_coords)} points)',
                {
                    'area': area,
                    'perimeter': perimeter,
                    'coordinates_count': len(validated_coords),
                    'is_closed': True
                }
            )
            
            return parcel
            
        except Exception as e:
            logger.error(f"Erreur création géométrie: {e}")
            upload.add_log_entry('geometry_error', f'Erreur création géométrie: {str(e)}')
            return None
    
    def _build_complete_response(self, upload: PublicUpload, ocr_result: OCRResult, parcel: Parcel, verification):
        """
        Construit la réponse complète pour le frontend
        """
        from .spatial_verification import AlertSystem
        
        # Résumé des alertes
        alert_summary = AlertSystem.generate_alert_summary(verification)
        
        # Réponse complète
        response = {
            "upload_id": str(upload.id),
            "status": upload.processing_status,
            "processing_time": verification.processing_time,
            
            # Résultats OCR
            "ocr_result": {
                "coordinates_extracted": len(ocr_result.extracted_coordinates),
                "coordinates_valid": len(ocr_result.validated_coordinates),
                "confidence_score": ocr_result.confidence_score,
                "extraction_method": ocr_result.extraction_method,
                "coordinates": ocr_result.validated_coordinates
            },
            
            # Géométrie de la parcelle
            "parcel": {
                "id": str(parcel.id),
                "area": parcel.area,
                "perimeter": parcel.perimeter,
                "status": parcel.status,
                "geometry": parcel.to_geojson(),
                "verification_completed": parcel.verification_completed
            },
            
            # Analyse spatiale intelligente
            "spatial_analysis": alert_summary,
            
            # Conflits détaillés
            "conflicts": parcel.get_conflicts_geojson(),
            
            # URLs pour le frontend
            "map_endpoints": {
                "parcel_geojson": f"/api/upload/{upload.id}/geojson/",
                "conflicts_geojson": f"/api/upload/{upload.id}/conflicts/",
                "nearby_parcels": f"/api/upload/{upload.id}/nearby/",
                "comparison": f"/api/comparison/{upload.id}/"
            },
            
            # Log de traitement
            "processing_log": upload.processing_log[-5:] if upload.processing_log else []  # 5 dernières entrées
        }
        
        return response


# ============================================================================
# UTILITAIRES DE VALIDATION
# ============================================================================

def validate_benin_coords(x: float, y: float) -> bool:
    """Valide que les coordonnées sont dans les limites du Bénin (UTM 31N)"""
    BENIN_BOUNDS = {
        'X_MIN': 200000, 'X_MAX': 500000,
        'Y_MIN': 600000, 'Y_MAX': 1400000
    }
    return (BENIN_BOUNDS['X_MIN'] <= x <= BENIN_BOUNDS['X_MAX'] and
            BENIN_BOUNDS['Y_MIN'] <= y <= BENIN_BOUNDS['Y_MAX'])


def validate_coordinate_format(x: float, y: float) -> bool:
    """Valide le format des coordonnées"""
    try:
        # Vérifier que ce sont des nombres valides
        float(x)
        float(y)
        
        # Vérifier les plages raisonnables pour UTM
        if x < 0 or y < 0:
            return False
        if x > 1000000 or y > 10000000:  # Limites UTM générales
            return False
            
        return True
    except (ValueError, TypeError):
        return False


def check_spatial_coherence(coordinates: list, tolerance: float = 1.0) -> bool:
    """Vérifie la cohérence spatiale des coordonnées"""
    if len(coordinates) < 3:
        return False
    
    try:
        # Vérifier que les points ne sont pas tous identiques
        unique_points = set((coord['x'], coord['y']) for coord in coordinates)
        if len(unique_points) < 3:
            return False
        
        # Vérifier que le polygone peut être fermé
        first_point = (coordinates[0]['x'], coordinates[0]['y'])
        last_point = (coordinates[-1]['x'], coordinates[-1]['y'])
        
        # Calculer la distance entre premier et dernier point
        distance = ((first_point[0] - last_point[0])**2 + (first_point[1] - last_point[1])**2)**0.5
        
        # Si la distance est faible, considérer comme fermé
        return distance <= tolerance or len(coordinates) >= 4
        
    except Exception:
        return False


def coords_to_polygon_wkt(coordinates: list) -> str:
    """Convertit une liste de coordonnées en WKT Polygon"""
    if len(coordinates) < 3:
        raise ValueError("Au moins 3 coordonnées requises pour un polygone")
    
    # Extraire les paires de coordonnées
    coord_pairs = [(coord['x'], coord['y']) for coord in coordinates]
    
    # Fermer le polygone si nécessaire
    if coord_pairs[0] != coord_pairs[-1]:
        coord_pairs.append(coord_pairs[0])
    
    # Construire le WKT
    coord_strings = [f"{x} {y}" for x, y in coord_pairs]
    wkt = f"POLYGON(({', '.join(coord_strings)}))"
    
    return wkt


def pair_tokens_to_coords(tokens: list) -> list:
    """
    Convertit les tokens OCR en paires de coordonnées
    Compatible avec l'existant mais amélioré
    """
    coordinates = []
    
    # Logique de pairing améliorée
    i = 0
    while i < len(tokens) - 1:
        try:
            # Chercher un pattern borne + X + Y
            if i < len(tokens) - 2:
                token1, token2, token3 = tokens[i], tokens[i+1], tokens[i+2]
                
                # Pattern: B1 X Y
                if (token1.startswith('B') and 
                    validate_coordinate_format(float(token2), float(token3)) and
                    validate_benin_coords(float(token2), float(token3))):
                    
                    coordinates.append({
                        'borne': token1,
                        'x': float(token2),
                        'y': float(token3)
                    })
                    i += 3
                    continue
            
            # Pattern: X Y (sans borne)
            if i < len(tokens) - 1:
                token1, token2 = tokens[i], tokens[i+1]
                try:
                    x, y = float(token1), float(token2)
                    if (validate_coordinate_format(x, y) and validate_benin_coords(x, y)):
                        coordinates.append({
                            'borne': f'P{len(coordinates)+1}',  # Point générique
                            'x': x,
                            'y': y
                        })
                        i += 2
                        continue
                except ValueError:
                    pass
            
            i += 1
            
        except (ValueError, IndexError):
            i += 1
    
    return coordinates

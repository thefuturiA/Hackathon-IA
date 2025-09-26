from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import json


class PublicUpload(models.Model):
    """
    Modèle principal pour les uploads de levées topographiques
    Orchestration complète du workflow IA + géospatial
    """
    
    # Identification - Keep existing BigAutoField for compatibility
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="uploads/public/")
    session_id = models.CharField(max_length=64, blank=True)
    original_filename = models.CharField(max_length=255, default='unknown_file.pdf')
    
    # Statuts de traitement
    PROCESSING_STATUS = [
        ('uploaded', 'Téléchargé'),
        ('ocr_processing', 'Extraction OCR en cours'),
        ('ocr_completed', 'OCR terminé'),
        ('coordinates_extracted', 'Coordonnées extraites'),
        ('geometry_created', 'Géométrie créée'),
        ('spatial_verification', 'Vérification spatiale en cours'),
        ('verification_completed', 'Validation terminée'),
        ('comparison_completed', 'Comparaison foncière terminée'),
        ('completed', 'Traitement complet'),
        ('error', 'Erreur'),
    ]
    
    processing_status = models.CharField(max_length=50, choices=PROCESSING_STATUS, default='uploaded')
    processed = models.BooleanField(default=False)
    
    # Métadonnées de traitement
    processing_log = models.JSONField(default=list)  # Log détaillé du traitement
    error_message = models.TextField(blank=True, null=True)
    processing_time = models.FloatField(null=True, blank=True)  # Temps en secondes
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Upload de levée topographique"
        verbose_name_plural = "Uploads de levées topographiques"
    
    def __str__(self):
        return f"{self.original_filename} - {self.get_processing_status_display()}"
    
    def add_log_entry(self, step, message, data=None):
        """Ajoute une entrée au log de traitement"""
        entry = {
            'timestamp': timezone.now().isoformat(),
            'step': step,
            'message': message,
            'data': data or {}
        }
        self.processing_log.append(entry)
        self.save(update_fields=['processing_log'])


class OCRResult(models.Model):
    """
    Résultats de l'extraction OCR avec métadonnées détaillées
    """
    
    upload = models.OneToOneField(PublicUpload, on_delete=models.CASCADE, related_name='ocr_result')
    
    # Texte brut extrait
    raw_text = models.TextField()
    corrected_text = models.TextField(blank=True)
    
    # Métadonnées OCR
    confidence_score = models.FloatField(default=0.0)
    processing_method = models.CharField(
        max_length=20,
        choices=[
            ('tesseract', 'Tesseract'),
            ('paddleocr', 'PaddleOCR'),
            ('hybrid', 'Hybride'),
            ('ultra_precise', 'Ultra Précis')
        ],
        default='ultra_precise'
    )
    extraction_method = models.CharField(max_length=50, default='hybrid')
    extraction_metadata = models.JSONField(default=dict)
    coordinates_found = models.IntegerField(default=0)
    
    # Coordonnées extraites
    extracted_coordinates = models.JSONField(default=list)
    validated_coordinates = models.JSONField(default=list)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Résultat OCR"
        verbose_name_plural = "Résultats OCR"
    
    def __str__(self):
        return f"OCR - {self.upload.original_filename} ({self.coordinates_found} coords)"


class Parcel(models.Model):
    """
    Parcelle extraite avec géométrie et statut de validation
    """
    
    # Identification
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Keep existing BigAutoField for compatibility
    upload = models.OneToOneField(PublicUpload, on_delete=models.CASCADE, related_name='parcel')
    
    # Géométrie spatiale
    geometry = gis_models.PolygonField(srid=32631, null=True, blank=True)  # UTM Zone 31N
    centroid = gis_models.PointField(srid=32631, null=True, blank=True)
    area = models.FloatField(null=True, blank=True)  # Surface en m²
    perimeter = models.FloatField(null=True, blank=True)  # Périmètre en m
    
    # Statut de validation
    STATUS_CHOICES = [
        ('secure', 'Sécurisé - Aucun conflit détecté'),
        ('warning', 'Attention - Vérifications requises'),
        ('conflict', 'Conflit - Problèmes détectés'),
        ('invalid', 'Invalide - Géométrie incorrecte'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='invalid')
    issues = models.JSONField(default=list)  # Liste des problèmes détectés
    recommendations = models.JSONField(default=list)  # Recommandations
    
    # Métadonnées de vérification
    verification_completed = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    verification_details = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Parcelle"
        verbose_name_plural = "Parcelles"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['verification_completed']),
        ]
    
    def __str__(self):
        return f"Parcelle {self.id} - {self.get_status_display()}"
    
    def to_geojson(self):
        """Convertit la parcelle en format GeoJSON pour le frontend"""
        if not self.geometry:
            return None
            
        return {
            "type": "Feature",
            "properties": {
                "id": str(self.id),
                "upload_id": str(self.upload.id),
                "status": self.status,
                "area": self.area,
                "perimeter": self.perimeter,
                "issues": self.issues,
                "recommendations": self.recommendations,
                "verification_completed": self.verification_completed,
                "created_at": self.created_at.isoformat(),
            },
            "geometry": json.loads(self.geometry.geojson)
        }


# ============================================================================
# SPATIAL VERIFICATION MODELS - Résultats des vérifications spatiales
# ============================================================================

class SpatialVerification(models.Model):
    """
    Résultats de la vérification spatiale d'une parcelle
    """
    
    # Référence à la parcelle
    parcel = models.OneToOneField(Parcel, on_delete=models.CASCADE, related_name='spatial_verification')
    
    # Statut global de vérification
    VERIFICATION_STATUS = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('error', 'Erreur'),
    ]
    
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    
    # Résultats des vérifications
    has_conflicts = models.BooleanField(default=False)
    conflict_count = models.IntegerField(default=0)
    
    # Détails des conflits
    double_vente_detected = models.BooleanField(default=False)
    protected_area_overlap = models.BooleanField(default=False)
    restriction_overlap = models.BooleanField(default=False)
    cadastre_inconsistency = models.BooleanField(default=False)
    
    # Métadonnées de vérification
    verification_details = models.JSONField(default=dict)
    processing_time = models.FloatField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Vérification Spatiale"
        verbose_name_plural = "Vérifications Spatiales"
    
    def __str__(self):
        return f"Vérification {self.parcel.id} - {self.get_status_display()}"


class SpatialConflict(models.Model):
    """
    Conflit spatial détecté lors de la vérification
    """
    
    # Référence à la vérification
    verification = models.ForeignKey(SpatialVerification, on_delete=models.CASCADE, related_name='conflicts')
    
    # Type de conflit
    CONFLICT_TYPES = [
        ('intersection', 'Intersection avec parcelle existante'),
        ('within_protected', 'Dans une aire protégée'),
        ('within_restriction', 'Dans une zone de restriction'),
        ('overlap_dpl', 'Chevauchement avec DPL'),
        ('overlap_dpm', 'Chevauchement avec DPM'),
        ('cadastre_difference', 'Différence avec cadastre existant'),
        ('litigation_zone', 'Zone litigieuse'),
    ]
    
    conflict_type = models.CharField(max_length=30, choices=CONFLICT_TYPES)
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ], default='medium')
    
    # Géométrie du conflit
    conflict_geometry = gis_models.GeometryField(srid=32631, null=True, blank=True)
    overlap_area = models.FloatField(null=True, blank=True)  # Surface de chevauchement
    overlap_percentage = models.FloatField(null=True, blank=True)  # % de chevauchement
    
    # Référence à l'objet en conflit
    conflicting_layer = models.CharField(max_length=50)  # Type de couche
    conflicting_object_id = models.IntegerField()  # ID de l'objet en conflit
    
    # Description et recommandations
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Conflit Spatial"
        verbose_name_plural = "Conflits Spatiaux"
        indexes = [
            models.Index(fields=['conflict_type']),
            models.Index(fields=['severity']),
        ]
    
    def __str__(self):
        return f"Conflit {self.get_conflict_type_display()} - {self.get_severity_display()}"
    
    def to_geojson(self):
        """Convertit le conflit en format GeoJSON pour le frontend"""
        if not self.conflict_geometry:
            return None
            
        return {
            "type": "Feature",
            "properties": {
                "id": self.id,
                "conflict_type": self.conflict_type,
                "severity": self.severity,
                "description": self.description,
                "recommendation": self.recommendation,
                "overlap_area": self.overlap_area,
                "overlap_percentage": self.overlap_percentage,
                "conflicting_layer": self.conflicting_layer,
                "conflicting_object_id": self.conflicting_object_id,
            },
            "geometry": json.loads(self.conflict_geometry.geojson)
        }


# ============================================================================
# ENHANCED PARCEL MODEL METHODS
# ============================================================================

# Ajout de méthodes à la classe Parcel existante
def get_conflicts_geojson(self):
    """Retourne tous les conflits de cette parcelle en GeoJSON"""
    if not hasattr(self, 'spatial_verification'):
        return {"type": "FeatureCollection", "features": []}
    
    conflicts = self.spatial_verification.conflicts.all()
    features = [conflict.to_geojson() for conflict in conflicts if conflict.to_geojson()]
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def get_verification_summary(self):
    """Résumé de la vérification pour le frontend"""
    if not hasattr(self, 'spatial_verification'):
        return {
            "status": "not_verified",
            "conflicts": 0,
            "recommendations": []
        }
    
    verification = self.spatial_verification
    return {
        "status": verification.status,
        "has_conflicts": verification.has_conflicts,
        "conflict_count": verification.conflict_count,
        "double_vente": verification.double_vente_detected,
        "protected_area": verification.protected_area_overlap,
        "restrictions": verification.restriction_overlap,
        "cadastre_issues": verification.cadastre_inconsistency,
        "processing_time": verification.processing_time,
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None,
    }

# Ajouter les méthodes à la classe Parcel
Parcel.get_conflicts_geojson = get_conflicts_geojson
Parcel.get_verification_summary = get_verification_summary

"""
Serializers pour l'API REST ANDF
Optimisés pour l'intégration avec React + Leaflet frontend
"""

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import PublicUpload, OCRResult, Parcel, SpatialVerification, SpatialConflict
import json


class PublicUploadSerializer(serializers.ModelSerializer):
    """Serializer pour les uploads de documents"""
    
    class Meta:
        model = PublicUpload
        fields = [
            'id', 'original_filename', 'processing_status', 'processed',
            'processing_time', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'processing_status', 'processed', 'processing_time', 'created_at', 'updated_at', 'completed_at']


class OCRResultSerializer(serializers.ModelSerializer):
    """Serializer pour les résultats OCR"""
    
    class Meta:
        model = OCRResult
        fields = [
            'coordinates_found', 'extracted_coordinates', 'validated_coordinates',
            'confidence_score', 'extraction_method', 'created_at'
        ]


class SpatialConflictSerializer(serializers.ModelSerializer):
    """Serializer pour les conflits spatiaux"""
    
    conflict_geojson = serializers.SerializerMethodField()
    
    class Meta:
        model = SpatialConflict
        fields = [
            'id', 'conflict_type', 'severity', 'description', 'recommendation',
            'overlap_area', 'overlap_percentage', 'conflicting_layer',
            'conflicting_object_id', 'conflict_geojson', 'created_at'
        ]
    
    def get_conflict_geojson(self, obj):
        """Retourne la géométrie du conflit en GeoJSON"""
        return obj.to_geojson()


class SpatialVerificationSerializer(serializers.ModelSerializer):
    """Serializer pour les vérifications spatiales"""
    
    conflicts = SpatialConflictSerializer(many=True, read_only=True)
    
    class Meta:
        model = SpatialVerification
        fields = [
            'status', 'has_conflicts', 'conflict_count',
            'double_vente_detected', 'protected_area_overlap',
            'restriction_overlap', 'cadastre_inconsistency',
            'verification_details', 'processing_time',
            'created_at', 'completed_at', 'conflicts'
        ]


class ParcelGeoJSONSerializer(GeoFeatureModelSerializer):
    """Serializer GeoJSON pour les parcelles (optimisé pour Leaflet)"""
    
    verification_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Parcel
        geo_field = 'geometry'
        fields = [
            'id', 'area', 'perimeter', 'status', 'issues', 'recommendations',
            'verification_completed', 'verification_date', 'created_at', 'verification_summary'
        ]
    
    def get_verification_summary(self, obj):
        """Résumé de vérification pour le frontend"""
        return obj.get_verification_summary()


class ParcelDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une parcelle"""
    
    ocr_result = OCRResultSerializer(source='upload.ocr_result', read_only=True)
    spatial_verification = SpatialVerificationSerializer(read_only=True)
    upload_info = PublicUploadSerializer(source='upload', read_only=True)
    conflicts_geojson = serializers.SerializerMethodField()
    parcel_geojson = serializers.SerializerMethodField()
    
    class Meta:
        model = Parcel
        fields = [
            'id', 'area', 'perimeter', 'status', 'issues', 'recommendations',
            'verification_completed', 'verification_date', 'created_at', 'updated_at',
            'ocr_result', 'spatial_verification', 'upload_info',
            'conflicts_geojson', 'parcel_geojson'
        ]
    
    def get_conflicts_geojson(self, obj):
        """Conflits en format GeoJSON pour la carte"""
        return obj.get_conflicts_geojson()
    
    def get_parcel_geojson(self, obj):
        """Parcelle en format GeoJSON pour la carte"""
        return obj.to_geojson()


class UploadStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut de traitement (polling)"""
    
    progress_percentage = serializers.SerializerMethodField()
    current_step = serializers.SerializerMethodField()
    estimated_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicUpload
        fields = [
            'id', 'processing_status', 'processed', 'processing_time',
            'progress_percentage', 'current_step', 'estimated_remaining',
            'error_message', 'updated_at'
        ]
    
    def get_progress_percentage(self, obj):
        """Calcule le pourcentage de progression"""
        status_progress = {
            'uploaded': 10,
            'ocr_processing': 30,
            'ocr_completed': 50,
            'coordinates_extracted': 60,
            'geometry_created': 70,
            'spatial_verification': 85,
            'verification_completed': 95,
            'completed': 100,
            'error': 0
        }
        return status_progress.get(obj.processing_status, 0)
    
    def get_current_step(self, obj):
        """Description de l'étape actuelle"""
        step_descriptions = {
            'uploaded': 'Document téléchargé',
            'ocr_processing': 'Extraction des coordonnées en cours...',
            'ocr_completed': 'Coordonnées extraites',
            'coordinates_extracted': 'Validation des coordonnées',
            'geometry_created': 'Géométrie de la parcelle créée',
            'spatial_verification': 'Analyse spatiale intelligente en cours...',
            'verification_completed': 'Vérification terminée',
            'completed': 'Traitement complet terminé',
            'error': 'Erreur de traitement'
        }
        return step_descriptions.get(obj.processing_status, 'Statut inconnu')
    
    def get_estimated_remaining(self, obj):
        """Estimation du temps restant en secondes"""
        if obj.processing_status == 'completed':
            return 0
        
        # Estimations basées sur l'expérience
        remaining_estimates = {
            'uploaded': 45,
            'ocr_processing': 30,
            'ocr_completed': 20,
            'coordinates_extracted': 15,
            'geometry_created': 10,
            'spatial_verification': 5,
            'verification_completed': 2,
        }
        return remaining_estimates.get(obj.processing_status, 0)


class LayerInfoSerializer(serializers.Serializer):
    """Serializer pour les informations des couches ANDF"""
    
    layer_name = serializers.CharField()
    table_name = serializers.CharField()
    feature_count = serializers.IntegerField()
    extent = serializers.CharField()
    available = serializers.BooleanField()
    error = serializers.CharField(required=False)


class GeoJSONResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses GeoJSON"""
    
    type = serializers.CharField(default="FeatureCollection")
    features = serializers.ListField()
    metadata = serializers.DictField(required=False)


class SpatialAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse complète d'analyse spatiale
    Optimisé pour l'affichage frontend avec React + Leaflet
    """
    
    upload_id = serializers.UUIDField()
    status = serializers.CharField()
    processing_time = serializers.FloatField()
    
    # Résultats OCR
    ocr_result = serializers.DictField()
    
    # Géométrie de la parcelle
    parcel = serializers.DictField()
    
    # Analyse spatiale intelligente
    spatial_analysis = serializers.DictField()
    
    # Conflits en GeoJSON
    conflicts = serializers.DictField()
    
    # URLs pour le frontend
    map_endpoints = serializers.DictField()
    
    # Log de traitement
    processing_log = serializers.ListField()


class ComparisonDataSerializer(serializers.Serializer):
    """
    Serializer pour les données de comparaison ancien/nouveau cadastre
    """
    
    new_parcel = serializers.DictField()  # GeoJSON de la nouvelle parcelle
    existing_parcels = serializers.DictField()  # GeoJSON des parcelles existantes proches
    conflicts = serializers.DictField()  # GeoJSON des zones de conflit
    recommendations = serializers.ListField()  # Recommandations pour résoudre les conflits
    
    comparison_metadata = serializers.DictField()  # Métadonnées de comparaison

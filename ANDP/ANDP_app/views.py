"""
API REST complète pour l'analyse spatiale intelligente ANDF
Optimisée pour l'intégration React + Leaflet frontend
"""

import tempfile
import os
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.gis.geos import GEOSGeometry
from .models import PublicUpload, Parcel, SpatialVerification
from .services.ocr_integration import OCRSpatialIntegrator
from .services.andf_layers import ANDFLayerService
from .services.spatial_verification import AlertSystem
from .serializers import (
    PublicUploadSerializer, ParcelDetailSerializer, ParcelGeoJSONSerializer,
    UploadStatusSerializer, SpatialAnalysisResponseSerializer, LayerInfoSerializer,
    GeoJSONResponseSerializer, ComparisonDataSerializer
)
import logging

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("Bienvenue sur l'API ANDF - Analyse Spatiale Intelligente")


# ============================================================================
# API PRINCIPALE - WORKFLOW COMPLET
# ============================================================================

class IntelligentUploadAnalysisView(APIView):
    """
    API principale pour l'analyse spatiale intelligente
    Upload → OCR → Géométrie → Vérification ANDF → Alertes
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Traitement complet d'un document de levée topographique
        """
        upfile = request.FILES.get("file")
        if not upfile:
            return Response({
                "error": "Fichier requis",
                "message": "Veuillez télécharger un PDF ou une image de levée topographique"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validation du type de fichier
        allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
        file_ext = os.path.splitext(upfile.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response({
                "error": "Type de fichier non supporté",
                "message": f"Types acceptés: {', '.join(allowed_extensions)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Créer l'upload
            upload = PublicUpload.objects.create(
                file=upfile,
                original_filename=upfile.name,
                session_id=request.session.session_key or ""
            )
            
            upload.add_log_entry('upload_created', f'Document téléchargé: {upfile.name}')

            # Lancer le traitement complet avec l'intégrateur
            integrator = OCRSpatialIntegrator()
            result = integrator.process_upload_complete(upload)

            return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur traitement upload: {e}")
            return Response({
                "error": "Erreur de traitement",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API DE STATUT ET SUIVI
# ============================================================================

class UploadStatusView(APIView):
    """
    API pour suivre le statut de traitement (polling)
    """
    
    def get(self, request, upload_id):
        """Retourne le statut actuel du traitement"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            serializer = UploadStatusSerializer(upload)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération statut",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UploadResultView(APIView):
    """
    API pour récupérer les résultats complets
    """
    
    def get(self, request, upload_id):
        """Retourne les résultats complets de l'analyse"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not upload.processed:
                return Response({
                    "error": "Traitement non terminé",
                    "status": upload.processing_status
                }, status=status.HTTP_202_ACCEPTED)
            
            if not hasattr(upload, 'parcel'):
                return Response({
                    "error": "Aucune parcelle générée",
                    "message": "Le traitement n'a pas pu créer de géométrie valide"
                }, status=status.HTTP_404_NOT_FOUND)
            
            parcel = upload.parcel
            serializer = ParcelDetailSerializer(parcel)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération résultats",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API GEOJSON POUR CARTES (REACT + LEAFLET)
# ============================================================================

class ParcelGeoJSONView(APIView):
    """
    API GeoJSON pour afficher la parcelle sur la carte
    """
    
    def get(self, request, upload_id):
        """Retourne la parcelle en format GeoJSON"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel') or not upload.parcel.geometry:
                return Response({
                    "type": "FeatureCollection",
                    "features": [],
                    "metadata": {"error": "Aucune géométrie disponible"}
                })
            
            parcel_geojson = upload.parcel.to_geojson()
            
            return Response({
                "type": "FeatureCollection",
                "features": [parcel_geojson] if parcel_geojson else [],
                "metadata": {
                    "upload_id": str(upload_id),
                    "area": upload.parcel.area,
                    "status": upload.parcel.status
                }
            })
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération GeoJSON",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConflictsGeoJSONView(APIView):
    """
    API GeoJSON pour afficher les conflits sur la carte
    """
    
    def get(self, request, upload_id):
        """Retourne les conflits en format GeoJSON"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel'):
                return Response({
                    "type": "FeatureCollection",
                    "features": [],
                    "metadata": {"error": "Aucune parcelle disponible"}
                })
            
            conflicts_geojson = upload.parcel.get_conflicts_geojson()
            
            return Response(conflicts_geojson)
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération conflits",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LayerGeoJSONView(APIView):
    """
    API GeoJSON pour les couches ANDF (avec filtrage spatial)
    """
    
    def get(self, request, layer_name):
        """
        Retourne une couche ANDF en GeoJSON
        Paramètres: bbox, limit
        """
        try:
            # Paramètres de filtrage
            bbox_param = request.GET.get('bbox')
            limit = int(request.GET.get('limit', 1000))
            
            bbox = None
            if bbox_param:
                try:
                    bbox = [float(x) for x in bbox_param.split(',')]
                    if len(bbox) != 4:
                        raise ValueError("Bbox doit contenir 4 valeurs")
                except ValueError:
                    return Response({
                        "error": "Bbox invalide",
                        "message": "Format attendu: xmin,ymin,xmax,ymax"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les données
            geojson_data = ANDFLayerService.get_layer_geojson(layer_name, bbox, limit)
            
            return Response(geojson_data)
            
        except ValueError as e:
            return Response({
                "error": "Couche non trouvée",
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Erreur récupération couche",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComparisonView(APIView):
    """
    API pour la comparaison ancien/nouveau cadastre
    """
    
    def get(self, request, upload_id):
        """
        Retourne les données de comparaison pour superposition sur carte
        """
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel') or not upload.parcel.geometry:
                return Response({
                    "error": "Aucune géométrie disponible pour comparaison"
                }, status=status.HTTP_404_NOT_FOUND)
            
            parcel = upload.parcel
            
            # Nouvelle parcelle
            new_parcel_geojson = parcel.to_geojson()
            
            # Parcelles existantes proches
            nearby_parcels = ANDFLayerService.get_nearby_parcels(parcel.geometry, distance_meters=200)
            existing_parcels_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": nearby['properties'],
                        "geometry": nearby['geometry']
                    }
                    for nearby in nearby_parcels
                ]
            }
            
            # Conflits
            conflicts_geojson = parcel.get_conflicts_geojson()
            
            # Recommandations de résolution
            recommendations = self._generate_resolution_recommendations(parcel)
            
            comparison_data = {
                "new_parcel": {
                    "type": "FeatureCollection",
                    "features": [new_parcel_geojson] if new_parcel_geojson else []
                },
                "existing_parcels": existing_parcels_geojson,
                "conflicts": conflicts_geojson,
                "recommendations": recommendations,
                "comparison_metadata": {
                    "upload_id": str(upload_id),
                    "analysis_date": parcel.verification_date.isoformat() if parcel.verification_date else None,
                    "total_nearby": len(nearby_parcels),
                    "total_conflicts": parcel.get_verification_summary()['conflict_count']
                }
            }
            
            serializer = ComparisonDataSerializer(comparison_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                "error": "Erreur génération comparaison",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_resolution_recommendations(self, parcel):
        """Génère des recommandations pour résoudre les conflits"""
        recommendations = []
        
        if hasattr(parcel, 'spatial_verification'):
            verification = parcel.spatial_verification
            
            if verification.double_vente_detected:
                recommendations.append({
                    "type": "legal",
                    "priority": "high",
                    "action": "Vérification juridique des droits de propriété",
                    "description": "Consulter un notaire pour clarifier les droits"
                })
            
            if verification.protected_area_overlap:
                recommendations.append({
                    "type": "environmental",
                    "priority": "medium",
                    "action": "Demande d'autorisation environnementale",
                    "description": "Contacter les services de conservation"
                })
            
            if verification.conflict_count > 0:
                recommendations.append({
                    "type": "administrative",
                    "priority": "medium",
                    "action": "Révision du plan de bornage",
                    "description": "Ajuster les limites pour éviter les conflits"
                })
        
        return recommendations


# ============================================================================
# API D'INFORMATION SUR LES COUCHES
# ============================================================================

class LayerInfoView(APIView):
    """
    API pour obtenir des informations sur les couches ANDF disponibles
    """
    
    def get(self, request):
        """Retourne les informations sur toutes les couches"""
        try:
            layer_info = ANDFLayerService.get_layer_info()
            
            # Sérialiser les données
            serialized_layers = []
            for layer_name, info in layer_info.items():
                serialized_layers.append({
                    'layer_name': layer_name,
                    **info
                })
            
            return Response({
                "layers": serialized_layers,
                "total_layers": len(serialized_layers),
                "available_layers": len([l for l in serialized_layers if l.get('available', False)])
            })
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération informations couches",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API DE GESTION DES ALERTES
# ============================================================================

class AlertDashboardView(APIView):
    """
    API pour le tableau de bord des alertes
    """
    
    def get(self, request):
        """Retourne un résumé des alertes récentes"""
        try:
            # Récupérer les uploads récents avec conflits
            recent_uploads = PublicUpload.objects.filter(
                processed=True,
                parcel__status__in=['conflict', 'warning']
            ).order_by('-completed_at')[:20]
            
            alerts = []
            for upload in recent_uploads:
                if hasattr(upload, 'parcel') and hasattr(upload.parcel, 'spatial_verification'):
                    alert_summary = AlertSystem.generate_alert_summary(upload.parcel.spatial_verification)
                    alert_summary['upload_id'] = str(upload.id)
                    alert_summary['filename'] = upload.original_filename
                    alert_summary['completed_at'] = upload.completed_at.isoformat()
                    alerts.append(alert_summary)
            
            return Response({
                "alerts": alerts,
                "total_alerts": len(alerts),
                "critical_count": len([a for a in alerts if a.get('critical_alerts')]),
                "warning_count": len([a for a in alerts if a['status'] == 'warning'])
            })
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération alertes",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# API UTILITAIRES
# ============================================================================

@api_view(['GET'])
def health_check(request):
    """Vérification de l'état de l'API"""
    try:
        # Vérifier la connexion à la base de données
        layer_info = ANDFLayerService.get_layer_info()
        available_layers = len([l for l in layer_info.values() if l.get('available', False)])
        
        return Response({
            "status": "healthy",
            "database": "connected",
            "andf_layers": available_layers,
            "timestamp": timezone.now().isoformat()
        })
    except Exception as e:
        return Response({
            "status": "unhealthy",
            "error": str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def api_documentation(request):
    """Documentation de l'API"""
    return Response({
        "title": "API ANDF - Analyse Spatiale Intelligente",
        "version": "1.0.0",
        "description": "API pour l'analyse automatique des levées topographiques avec vérification ANDF",
        "endpoints": {
            "workflow": {
                "POST /api/upload/": "Upload et traitement complet d'un document",
                "GET /api/upload/{id}/status/": "Statut du traitement",
                "GET /api/upload/{id}/result/": "Résultats complets",
            },
            "geojson": {
                "GET /api/upload/{id}/geojson/": "Parcelle en GeoJSON",
                "GET /api/upload/{id}/conflicts/": "Conflits en GeoJSON",
                "GET /api/layers/{layer}/geojson/": "Couche ANDF en GeoJSON",
                "GET /api/comparison/{id}/": "Données de comparaison",
            },
            "management": {
                "GET /api/layers/info/": "Informations sur les couches",
                "GET /api/alerts/": "Tableau de bord des alertes",
                "GET /api/health/": "État de l'API",
            }
        },
        "frontend_integration": {
            "technology": "React + Tailwind + Leaflet/Mapbox",
            "cors_enabled": True,
            "real_time_updates": "Polling sur /api/upload/{id}/status/",
            "map_data": "GeoJSON endpoints pour visualisation"
        }
    })


# ============================================================================
# API GEOJSON POUR CARTES (REACT + LEAFLET) - SUITE
# ============================================================================

class ParcelGeoJSONView(APIView):
    """
    API GeoJSON pour afficher la parcelle sur la carte
    """
    
    def get(self, request, upload_id):
        """Retourne la parcelle en format GeoJSON"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel') or not upload.parcel.geometry:
                return Response({
                    "type": "FeatureCollection",
                    "features": [],
                    "metadata": {"error": "Aucune géométrie disponible"}
                })
            
            parcel_geojson = upload.parcel.to_geojson()
            
            return Response({
                "type": "FeatureCollection",
                "features": [parcel_geojson] if parcel_geojson else [],
                "metadata": {
                    "upload_id": str(upload_id),
                    "area": upload.parcel.area,
                    "status": upload.parcel.status
                }
            })
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération GeoJSON",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConflictsGeoJSONView(APIView):
    """
    API GeoJSON pour afficher les conflits sur la carte
    """
    
    def get(self, request, upload_id):
        """Retourne les conflits en format GeoJSON"""
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel'):
                return Response({
                    "type": "FeatureCollection",
                    "features": [],
                    "metadata": {"error": "Aucune parcelle disponible"}
                })
            
            conflicts_geojson = upload.parcel.get_conflicts_geojson()
            
            return Response(conflicts_geojson)
            
        except Exception as e:
            return Response({
                "error": "Erreur récupération conflits",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LayerGeoJSONView(APIView):
    """
    API GeoJSON pour les couches ANDF (avec filtrage spatial)
    """
    
    def get(self, request, layer_name):
        """
        Retourne une couche ANDF en GeoJSON
        Paramètres: bbox, limit
        """
        try:
            # Paramètres de filtrage
            bbox_param = request.GET.get('bbox')
            limit = int(request.GET.get('limit', 1000))
            
            bbox = None
            if bbox_param:
                try:
                    bbox = [float(x) for x in bbox_param.split(',')]
                    if len(bbox) != 4:
                        raise ValueError("Bbox doit contenir 4 valeurs")
                except ValueError:
                    return Response({
                        "error": "Bbox invalide",
                        "message": "Format attendu: xmin,ymin,xmax,ymax"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer les données
            geojson_data = ANDFLayerService.get_layer_geojson(layer_name, bbox, limit)
            
            return Response(geojson_data)
            
        except ValueError as e:
            return Response({
                "error": "Couche non trouvée",
                "message": str(e)
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Erreur récupération couche",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComparisonView(APIView):
    """
    API pour la comparaison ancien/nouveau cadastre
    """
    
    def get(self, request, upload_id):
        """
        Retourne les données de comparaison pour superposition sur carte
        """
        try:
            upload = get_object_or_404(PublicUpload, id=upload_id)
            
            if not hasattr(upload, 'parcel') or not upload.parcel.geometry:
                return Response({
                    "error": "Aucune géométrie disponible pour comparaison"
                }, status=status.HTTP_404_NOT_FOUND)
            
            parcel = upload.parcel
            
            # Nouvelle parcelle
            new_parcel_geojson = parcel.to_geojson()
            
            # Parcelles existantes proches
            nearby_parcels = ANDFLayerService.get_nearby_parcels(parcel.geometry, distance_meters=200)
            existing_parcels_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": nearby['properties'],
                        "geometry": nearby['geometry']
                    }
                    for nearby in nearby_parcels
                ]
            }
            
            # Conflits
            conflicts_geojson = parcel.get_conflicts_geojson()
            
            # Recommandations de résolution
            recommendations = self._generate_resolution_recommendations(parcel)
            
            comparison_data = {
                "new_parcel": {
                    "type": "FeatureCollection",
                    "features": [new_parcel_geojson] if new_parcel_geojson else []
                },
                "existing_parcels": existing_parcels_geojson,
                "conflicts": conflicts_geojson,
                "recommendations": recommendations,
                "comparison_metadata": {
                    "upload_id": str(upload_id),
                    "analysis_date": parcel.verification_date.isoformat() if parcel.verification_date else None,
                    "total_nearby": len(nearby_parcels),
                    "total_conflicts": parcel.get_verification_summary()['conflict_count']
                }
            }
            
            serializer = ComparisonDataSerializer(comparison_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                "error": "Erreur génération comparaison",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_resolution_recommendations(self, parcel):
        """Génère des recommandations pour résoudre les conflits"""
        recommendations = []
        
        if hasattr(parcel, 'spatial_verification'):
            verification = parcel.spatial_verification
            
            if verification.double_vente_detected:
                recommendations.append({
                    "type": "legal",
                    "priority": "high",
                    "action": "Vérification juridique des droits de propriété",
                    "description": "Consulter un notaire pour clarifier les droits"
                })
            
            if verification.protected_area_overlap:
                recommendations.append({
                    "type": "environmental",
                    "priority": "medium",
                    "action": "Demande d'autorisation environnementale",
                    "description": "Contacter les services de conservation"
                })
            
            if verification.conflict_count > 0:
                recommendations.append({
                    "type": "administrative",
                    "priority": "medium",
                    "action": "Révision du plan de bornage",
                    "description": "Ajuster les limites pour éviter les conflits"
                })
        
        return recommendations


# ============================================================================
# VUES LEGACY (COMPATIBILITÉ)
# ============================================================================

# Garder l'ancienne vue pour compatibilité
class UploadAndExtractView(APIView):
    """Vue legacy - redirige vers la nouvelle API"""
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        # Rediriger vers la nouvelle API
        view = IntelligentUploadAnalysisView()
        return view.post(request, *args, **kwargs)

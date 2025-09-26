from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.index, name='index'),
    
    # ============================================================================
    # API PRINCIPALE - WORKFLOW COMPLET
    # ============================================================================
    
    # Upload et traitement complet
    path('api/upload/', views.IntelligentUploadAnalysisView.as_view(), name='intelligent_upload'),
    
    # Suivi du statut
    path('api/upload/<uuid:upload_id>/status/', views.UploadStatusView.as_view(), name='upload_status'),
    path('api/upload/<uuid:upload_id>/result/', views.UploadResultView.as_view(), name='upload_result'),
    
    # ============================================================================
    # API GEOJSON POUR CARTES (REACT + LEAFLET)
    # ============================================================================
    
    # GeoJSON de la parcelle
    path('api/upload/<uuid:upload_id>/geojson/', views.ParcelGeoJSONView.as_view(), name='parcel_geojson'),
    
    # GeoJSON des conflits
    path('api/upload/<uuid:upload_id>/conflicts/', views.ConflictsGeoJSONView.as_view(), name='conflicts_geojson'),
    
    # GeoJSON des couches ANDF
    path('api/layers/<str:layer_name>/geojson/', views.LayerGeoJSONView.as_view(), name='layer_geojson'),
    
    # Données de comparaison ancien/nouveau cadastre
    path('api/comparison/<uuid:upload_id>/', views.ComparisonView.as_view(), name='comparison_data'),
    
    # ============================================================================
    # API DE GESTION ET INFORMATION
    # ============================================================================
    
    # Informations sur les couches
    path('api/layers/info/', views.LayerInfoView.as_view(), name='layer_info'),
    
    # Tableau de bord des alertes
    path('api/alerts/', views.AlertDashboardView.as_view(), name='alert_dashboard'),
    
    # ============================================================================
    # API UTILITAIRES
    # ============================================================================
    
    # Vérification de l'état de l'API
    path('api/health/', views.health_check, name='health_check'),
    
    # Documentation de l'API
    path('api/docs/', views.api_documentation, name='api_docs'),
    
    # ============================================================================
    # COMPATIBILITÉ LEGACY
    # ============================================================================
    
    # Ancienne API (redirige vers la nouvelle)
    path('upload/', views.UploadAndExtractView.as_view(), name='legacy_upload'),
]

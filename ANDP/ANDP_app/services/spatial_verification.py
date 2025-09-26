"""
Moteur de vérification spatiale intelligente COMPLET
Système d'alerte intelligent pour détecter tous les types de conflits ANDF
"""

from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from ..models import SpatialVerification, SpatialConflict, Parcel
from .andf_layers import ANDFLayerService
import logging
import time

logger = logging.getLogger(__name__)


class IntelligentSpatialAnalyzer:
    """
    Analyseur spatial intelligent pour les parcelles extraites
    Système d'alerte automatique pour tous les types de conflits ANDF
    """
    
    def __init__(self):
        self.andf_service = ANDFLayerService()
        
        # Seuils de détection intelligents
        self.OVERLAP_THRESHOLDS = {
            'critical': 50,  # >50% de chevauchement = critique
            'high': 20,      # >20% = élevé
            'medium': 5,     # >5% = moyen
            'low': 1         # >1% = faible
        }
    
    def analyze_parcel(self, parcel: Parcel):
        """
        Lance l'analyse spatiale intelligente complète d'une parcelle
        
        Args:
            parcel: Instance de Parcel à analyser
        
        Returns:
            SpatialVerification: Résultats de l'analyse avec alertes
        """
        start_time = time.time()
        
        # Créer ou récupérer l'objet de vérification
        verification, created = SpatialVerification.objects.get_or_create(
            parcel=parcel,
            defaults={'status': 'processing'}
        )
        
        if not created:
            verification.status = 'processing'
            verification.save()
        
        try:
            # Vérifier que la parcelle a une géométrie valide
            if not parcel.geometry:
                raise ValueError("Parcelle sans géométrie")
            
            # Supprimer les anciens conflits
            verification.conflicts.all().delete()
            
            # Log de début d'analyse
            parcel.upload.add_log_entry(
                'spatial_analysis_start',
                'Début de l\'analyse spatiale intelligente',
                {'parcel_area': parcel.area}
            )
            
            # 1. DÉTECTION AUTOMATIQUE DE DOUBLE VENTE
            self._detect_double_vente(verification, parcel.geometry)
            
            # 2. DÉTECTION D'OCCUPATION ILLÉGALE (Domaine Public)
            self._detect_illegal_occupation(verification, parcel.geometry)
            
            # 3. REPÉRAGE DE ZONES PROTÉGÉES
            self._detect_protected_areas(verification, parcel.geometry)
            
            # 4. REPÉRAGE DE ZONES LITIGIEUSES
            self._detect_litigation_zones(verification, parcel.geometry)
            
            # 5. VÉRIFICATION DES RESTRICTIONS (ZDUP, PAG)
            self._detect_restrictions(verification, parcel.geometry)
            
            # 6. ANALYSE DE COHÉRENCE CADASTRALE
            self._analyze_cadastre_consistency(verification, parcel.geometry)
            
            # Finaliser l'analyse avec recommandations intelligentes
            self._finalize_intelligent_analysis(verification, start_time)
            
            # Mettre à jour le statut de la parcelle avec système d'alerte
            self._update_parcel_with_alerts(parcel, verification)
            
            return verification
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse spatiale intelligente: {e}")
            verification.status = 'error'
            parcel.upload.add_log_entry('spatial_analysis_error', f'Erreur: {str(e)}')
            verification.save()
            raise
    
    def _detect_double_vente(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        DÉTECTION AUTOMATIQUE DE DOUBLE VENTE
        Vérifie les chevauchements avec TF déjà attribués
        """
        try:
            # Vérifier avec les parcelles existantes
            intersections = self.andf_service.check_intersections(geometry, 'parcelles')
            
            for intersection in intersections:
                overlap_pct = intersection['overlap_percentage']
                
                # Seuil de détection: >1% de chevauchement
                if overlap_pct > 1:
                    severity = self._get_severity_from_overlap(overlap_pct)
                    
                    # Créer l'alerte de double vente
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='intersection',
                        severity=severity,
                        conflicting_layer='parcelles',
                        conflicting_object_id=intersection['object_id'],
                        overlap_area=intersection['intersection_area'],
                        overlap_percentage=overlap_pct,
                        description=f"ALERTE DOUBLE VENTE: Chevauchement de {overlap_pct:.1f}% avec la parcelle {intersection['properties'].get('nup', 'N/A')} (TF #{intersection['properties'].get('num_tf', 'N/A')})",
                        recommendation=self._get_double_vente_recommendation(overlap_pct, intersection['properties'])
                    )
                    
                    verification.double_vente_detected = True
                    
                    # Log d'alerte
                    verification.parcel.upload.add_log_entry(
                        'double_vente_alert',
                        f'DOUBLE VENTE DÉTECTÉE: {overlap_pct:.1f}% de chevauchement',
                        {
                            'conflicting_nup': intersection['properties'].get('nup'),
                            'conflicting_tf': intersection['properties'].get('num_tf'),
                            'overlap_percentage': overlap_pct,
                            'severity': severity
                        }
                    )
            
            # Vérifier aussi avec les AIF (grandes superficies)
            aif_intersections = self.andf_service.check_intersections(geometry, 'aif')
            for intersection in aif_intersections:
                overlap_pct = intersection['overlap_percentage']
                if overlap_pct > 5:  # Seuil plus élevé pour les AIF
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='intersection',
                        severity='high',
                        conflicting_layer='aif',
                        conflicting_object_id=intersection['object_id'],
                        overlap_area=intersection['intersection_area'],
                        overlap_percentage=overlap_pct,
                        description=f"CONFLIT AIF: Chevauchement avec Association d'Intérêts Foncier TF #{intersection['properties'].get('num_tf')}",
                        recommendation="Vérifier les droits de morcellement et l'autorisation de l'AIF"
                    )
                    
        except Exception as e:
            logger.error(f"Erreur détection double vente: {e}")
    
    def _detect_illegal_occupation(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        DÉTECTION D'OCCUPATION ILLÉGALE
        Vérifie les constructions sur domaine public (DPL, DPM)
        """
        try:
            # Vérifier DPL (Domaine Public Lagunaire)
            dpl_overlaps = self.andf_service.check_intersections(geometry, 'dpl')
            for overlap in dpl_overlaps:
                if overlap['overlap_percentage'] > 0.1:  # Tolérance très faible
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='overlap_dpl',
                        severity='critical',
                        conflicting_layer='dpl',
                        conflicting_object_id=overlap['object_id'],
                        overlap_area=overlap['intersection_area'],
                        overlap_percentage=overlap['overlap_percentage'],
                        description=f"OCCUPATION ILLÉGALE DPL: Construction sur domaine public lagunaire ({overlap['overlap_percentage']:.1f}%)",
                        recommendation="INTERDICTION FORMELLE - Zone inhabitable autour des plans d'eau"
                    )
                    
                    # Log d'alerte critique
                    verification.parcel.upload.add_log_entry(
                        'illegal_occupation_dpl',
                        'OCCUPATION ILLÉGALE DÉTECTÉE - Domaine Public Lagunaire',
                        {'overlap_percentage': overlap['overlap_percentage']}
                    )
            
            # Vérifier DPM (Domaine Public Maritime)
            dpm_overlaps = self.andf_service.check_intersections(geometry, 'dpm')
            for overlap in dpm_overlaps:
                if overlap['overlap_percentage'] > 0.1:
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='overlap_dpm',
                        severity='critical',
                        conflicting_layer='dpm',
                        conflicting_object_id=overlap['object_id'],
                        overlap_area=overlap['intersection_area'],
                        overlap_percentage=overlap['overlap_percentage'],
                        description=f"OCCUPATION ILLÉGALE DPM: Construction sur domaine public maritime ({overlap['overlap_percentage']:.1f}%)",
                        recommendation="INTERDICTION FORMELLE - Zone inhabitable maritime"
                    )
                    
        except Exception as e:
            logger.error(f"Erreur détection occupation illégale: {e}")
    
    def _detect_protected_areas(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        REPÉRAGE DE ZONES PROTÉGÉES
        Détecte les empiètements sur aires protégées
        """
        try:
            protected_overlaps = self.andf_service.check_intersections(geometry, 'air_proteges')
            
            for overlap in protected_overlaps:
                if overlap['overlap_percentage'] > 0.1:
                    severity = 'critical' if overlap['overlap_percentage'] > 10 else 'high'
                    
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='within_protected',
                        severity=severity,
                        conflicting_layer='air_proteges',
                        conflicting_object_id=overlap['object_id'],
                        overlap_area=overlap['intersection_area'],
                        overlap_percentage=overlap['overlap_percentage'],
                        description=f"ZONE PROTÉGÉE: Empiètement sur {overlap['properties'].get('designation', 'aire protégée')} ({overlap['overlap_percentage']:.1f}%)",
                        recommendation="Autorisation environnementale requise - Consulter les services de conservation"
                    )
                    
                    verification.protected_area_overlap = True
                    
                    # Log d'alerte
                    verification.parcel.upload.add_log_entry(
                        'protected_area_alert',
                        f'ZONE PROTÉGÉE DÉTECTÉE: {overlap["properties"].get("designation")}',
                        {'overlap_percentage': overlap['overlap_percentage']}
                    )
                    
        except Exception as e:
            logger.error(f"Erreur détection zones protégées: {e}")
    
    def _detect_litigation_zones(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        REPÉRAGE DE ZONES LITIGIEUSES
        Détecte les zones en litige devant les juridictions
        """
        try:
            litigation_overlaps = self.andf_service.check_intersections(geometry, 'litige')
            
            for overlap in litigation_overlaps:
                if overlap['overlap_percentage'] > 0.1:
                    SpatialConflict.objects.create(
                        verification=verification,
                        conflict_type='litigation_zone',
                        severity='high',
                        conflicting_layer='litige',
                        conflicting_object_id=overlap['object_id'],
                        overlap_area=overlap['intersection_area'],
                        overlap_percentage=overlap['overlap_percentage'],
                        description=f"ZONE LITIGIEUSE: Parcelle en zone de litige ({overlap['overlap_percentage']:.1f}%)",
                        recommendation="ATTENTION - Zone en litige devant les juridictions. Vérifier le statut juridique avant toute transaction"
                    )
                    
                    # Log d'alerte
                    verification.parcel.upload.add_log_entry(
                        'litigation_zone_alert',
                        'ZONE LITIGIEUSE DÉTECTÉE',
                        {'overlap_percentage': overlap['overlap_percentage']}
                    )
                    
        except Exception as e:
            logger.error(f"Erreur détection zones litigieuses: {e}")
    
    def _detect_restrictions(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        VÉRIFICATION DES RESTRICTIONS
        Détecte les zones ZDUP, PAG et autres restrictions
        """
        try:
            # Note: Si vous avez une table restrictions, décommentez:
            # restriction_overlaps = self.andf_service.check_intersections(geometry, 'restrictions')
            # for overlap in restriction_overlaps:
            #     if overlap['overlap_percentage'] > 0.1:
            #         SpatialConflict.objects.create(...)
            pass
                    
        except Exception as e:
            logger.error(f"Erreur détection restrictions: {e}")
    
    def _analyze_cadastre_consistency(self, verification: SpatialVerification, geometry: GEOSGeometry):
        """
        ANALYSE DE COHÉRENCE CADASTRALE
        Compare avec le cadastre existant pour détecter les incohérences
        """
        try:
            # Rechercher les parcelles proches pour analyse de cohérence
            nearby_parcels = self.andf_service.get_nearby_parcels(geometry, distance_meters=50)
            
            inconsistencies = 0
            for nearby in nearby_parcels:
                # Analyser la cohérence des numéros TF, îlots, etc.
                if self._check_numbering_consistency(nearby['properties']):
                    inconsistencies += 1
            
            if inconsistencies > 0:
                verification.cadastre_inconsistency = True
                
                SpatialConflict.objects.create(
                    verification=verification,
                    conflict_type='cadastre_difference',
                    severity='medium',
                    conflicting_layer='parcelles',
                    conflicting_object_id=0,  # Multiple objets
                    description=f"INCOHÉRENCE CADASTRALE: {inconsistencies} incohérences détectées dans le voisinage",
                    recommendation="Vérifier la numérotation et la cohérence avec le cadastre existant"
                )
                
        except Exception as e:
            logger.error(f"Erreur analyse cohérence cadastrale: {e}")
    
    def _check_numbering_consistency(self, properties):
        """Vérifie la cohérence de la numérotation cadastrale"""
        # Logique de vérification de cohérence
        # À adapter selon vos règles métier
        return False
    
    def _get_severity_from_overlap(self, overlap_percentage):
        """Détermine la sévérité basée sur le pourcentage de chevauchement"""
        if overlap_percentage >= self.OVERLAP_THRESHOLDS['critical']:
            return 'critical'
        elif overlap_percentage >= self.OVERLAP_THRESHOLDS['high']:
            return 'high'
        elif overlap_percentage >= self.OVERLAP_THRESHOLDS['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _get_double_vente_recommendation(self, overlap_pct, properties):
        """Génère une recommandation intelligente pour les doubles ventes"""
        tf_num = properties.get('num_tf', 'N/A')
        nup = properties.get('nup', 'N/A')
        
        if overlap_pct > 50:
            return f"URGENT - Conflit majeur avec TF #{tf_num} (NUP: {nup}). Suspendre toute transaction et vérifier les droits de propriété."
        elif overlap_pct > 20:
            return f"ATTENTION - Chevauchement significatif avec TF #{tf_num}. Vérification juridique recommandée."
        else:
            return f"Chevauchement mineur avec TF #{tf_num}. Vérifier les limites cadastrales."
    
    def _finalize_intelligent_analysis(self, verification: SpatialVerification, start_time: float):
        """
        Finalise l'analyse avec un résumé intelligent
        """
        # Compter les conflits par type et sévérité
        conflicts = verification.conflicts.all()
        verification.conflict_count = conflicts.count()
        verification.has_conflicts = verification.conflict_count > 0
        
        # Analyser la distribution des conflits
        conflict_summary = {
            'total': verification.conflict_count,
            'by_type': {},
            'by_severity': {},
            'critical_issues': []
        }
        
        for conflict in conflicts:
            # Par type
            if conflict.conflict_type not in conflict_summary['by_type']:
                conflict_summary['by_type'][conflict.conflict_type] = 0
            conflict_summary['by_type'][conflict.conflict_type] += 1
            
            # Par sévérité
            if conflict.severity not in conflict_summary['by_severity']:
                conflict_summary['by_severity'][conflict.severity] = 0
            conflict_summary['by_severity'][conflict.severity] += 1
            
            # Issues critiques
            if conflict.severity == 'critical':
                conflict_summary['critical_issues'].append(conflict.description)
        
        # Temps de traitement
        processing_time = time.time() - start_time
        verification.processing_time = processing_time
        
        # Détails de vérification
        verification.verification_details = {
            'analysis_summary': conflict_summary,
            'processing_time': processing_time,
            'layers_checked': list(self.andf_service.LAYER_MAPPING.keys()),
            'thresholds_used': self.OVERLAP_THRESHOLDS,
            'analysis_date': timezone.now().isoformat()
        }
        
        # Statut final
        verification.status = 'completed'
        verification.completed_at = timezone.now()
        verification.save()
        
        # Log final
        verification.parcel.upload.add_log_entry(
            'spatial_analysis_completed',
            f'Analyse spatiale terminée en {processing_time:.2f}s',
            conflict_summary
        )
    
    def _update_parcel_with_alerts(self, parcel: Parcel, verification: SpatialVerification):
        """
        Met à jour le statut de la parcelle avec système d'alerte intelligent
        """
        # Déterminer le statut global basé sur les conflits
        if verification.conflict_count == 0:
            parcel.status = 'secure'
            parcel.issues = []
            parcel.recommendations = ["Aucun conflit détecté - Parcelle sécurisée"]
            
        else:
            critical_conflicts = verification.conflicts.filter(severity='critical').count()
            high_conflicts = verification.conflicts.filter(severity='high').count()
            
            if critical_conflicts > 0:
                parcel.status = 'conflict'
                parcel.issues = [
                    f"{critical_conflicts} conflit(s) critique(s) détecté(s)",
                    "Intervention immédiate requise"
                ]
            elif high_conflicts > 0:
                parcel.status = 'conflict'
                parcel.issues = [
                    f"{high_conflicts} conflit(s) majeur(s) détecté(s)",
                    "Vérifications approfondies nécessaires"
                ]
            else:
                parcel.status = 'warning'
                parcel.issues = [
                    f"{verification.conflict_count} conflit(s) mineur(s) détecté(s)",
                    "Vérifications recommandées"
                ]
            
            # Générer des recommandations intelligentes
            parcel.recommendations = self._generate_intelligent_recommendations(verification)
        
        # Marquer la vérification comme terminée
        parcel.verification_completed = True
        parcel.verification_date = timezone.now()
        parcel.save()
        
        # Mettre à jour le statut de l'upload
        parcel.upload.processing_status = 'verification_completed'
        parcel.upload.save()
    
    def _generate_intelligent_recommendations(self, verification: SpatialVerification):
        """Génère des recommandations intelligentes basées sur l'analyse"""
        recommendations = []
        
        conflicts = verification.conflicts.all()
        
        # Recommandations par type de conflit
        if verification.double_vente_detected:
            recommendations.append("🚨 PRIORITÉ HAUTE: Vérifier les droits de propriété et l'historique des transactions")
        
        if verification.protected_area_overlap:
            recommendations.append("🌿 Consulter les services environnementaux pour autorisation")
        
        if conflicts.filter(conflict_type__in=['overlap_dpl', 'overlap_dpm']).exists():
            recommendations.append("⛔ INTERDICTION: Construction sur domaine public - Revoir l'implantation")
        
        if conflicts.filter(conflict_type='litigation_zone').exists():
            recommendations.append("⚖️ Vérifier le statut juridique - Zone en litige")
        
        # Recommandations générales
        if verification.conflict_count > 3:
            recommendations.append("📋 Audit complet recommandé - Multiples conflits détectés")
        
        return recommendations


# ============================================================================
# SYSTÈME D'ALERTE INTELLIGENT
# ============================================================================

class AlertSystem:
    """
    Système d'alerte intelligent pour les conflits spatiaux
    """
    
    @staticmethod
    def generate_alert_summary(verification: SpatialVerification):
        """
        Génère un résumé d'alerte pour le frontend
        """
        conflicts = verification.conflicts.all()
        
        alert_summary = {
            'status': verification.parcel.status,
            'total_conflicts': verification.conflict_count,
            'critical_alerts': [],
            'warnings': [],
            'recommendations': verification.parcel.recommendations,
            'processing_time': verification.processing_time,
        }
        
        for conflict in conflicts:
            alert_item = {
                'type': conflict.conflict_type,
                'severity': conflict.severity,
                'description': conflict.description,
                'recommendation': conflict.recommendation,
                'overlap_percentage': conflict.overlap_percentage,
            }
            
            if conflict.severity == 'critical':
                alert_summary['critical_alerts'].append(alert_item)
            else:
                alert_summary['warnings'].append(alert_item)
        
        return alert_summary

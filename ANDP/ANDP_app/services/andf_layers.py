"""
Service de gestion des couches ANDF
Utilise les tables PostGIS importées via ogr2ogr
"""

from django.db import connection
from django.contrib.gis.geos import GEOSGeometry
import json
import logging

logger = logging.getLogger(__name__)


class ANDFLayerService:
    """
    Service pour interagir avec les couches ANDF importées dans PostGIS
    """
    
    # Mapping des couches ANDF avec leurs tables PostGIS
    LAYER_MAPPING = {
        'aif': 'aif',
        'air_proteges': 'air_proteges', 
        'dpl': 'dpl',
        'dpm': 'dpm',
        'parcelles': 'parcelles',
        'enregistrement_individuel': 'enregistrement_individuel',
        'litige': 'litige',
        # Ajoutez d'autres couches selon vos besoins
    }
    
    @classmethod
    def get_layer_info(cls):
        """Retourne les informations sur toutes les couches disponibles"""
        layer_info = {}
        
        with connection.cursor() as cursor:
            for layer_name, table_name in cls.LAYER_MAPPING.items():
                try:
                    # Vérifier si la table existe
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name = %s
                    """, [table_name])
                    
                    if cursor.fetchone()[0] > 0:
                        # Compter les features
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        feature_count = cursor.fetchone()[0]
                        
                        # Obtenir l'étendue spatiale
                        cursor.execute(f"""
                            SELECT ST_AsText(ST_Extent(geom)) FROM {table_name}
                        """)
                        extent = cursor.fetchone()[0]
                        
                        layer_info[layer_name] = {
                            'table_name': table_name,
                            'feature_count': feature_count,
                            'extent': extent,
                            'available': True
                        }
                    else:
                        layer_info[layer_name] = {
                            'table_name': table_name,
                            'available': False
                        }
                        
                except Exception as e:
                    logger.error(f"Erreur lors de la vérification de la couche {layer_name}: {e}")
                    layer_info[layer_name] = {
                        'table_name': table_name,
                        'available': False,
                        'error': str(e)
                    }
        
        return layer_info
    
    @classmethod
    def get_layer_geojson(cls, layer_name, bbox=None, limit=1000):
        """
        Retourne les données d'une couche en format GeoJSON
        
        Args:
            layer_name: Nom de la couche
            bbox: Bounding box [xmin, ymin, xmax, ymax] pour filtrer
            limit: Limite du nombre de features
        """
        if layer_name not in cls.LAYER_MAPPING:
            raise ValueError(f"Couche {layer_name} non reconnue")
        
        table_name = cls.LAYER_MAPPING[layer_name]
        
        # Construction de la requête
        base_query = f"""
            SELECT jsonb_build_object(
                'type', 'Feature',
                'properties', to_jsonb(row) - 'geom',
                'geometry', ST_AsGeoJSON(geom)::jsonb
            ) as feature
            FROM {table_name} row
        """
        
        conditions = []
        params = []
        
        # Filtre spatial si bbox fourni
        if bbox and len(bbox) == 4:
            conditions.append("ST_Intersects(geom, ST_MakeEnvelope(%s, %s, %s, %s, 32631))")
            params.extend(bbox)
        
        # Ajouter les conditions
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Ajouter la limite
        base_query += f" LIMIT {limit}"
        
        features = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(base_query, params)
                features = [row[0] for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de {layer_name}: {e}")
                raise
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    @classmethod
    def check_intersections(cls, geometry, layer_name, buffer_distance=0):
        """
        Vérifie les intersections avec une couche ANDF
        
        Args:
            geometry: Géométrie à vérifier (GEOSGeometry)
            layer_name: Nom de la couche ANDF
            buffer_distance: Distance de buffer en mètres
        
        Returns:
            Liste des intersections trouvées
        """
        if layer_name not in cls.LAYER_MAPPING:
            raise ValueError(f"Couche {layer_name} non reconnue")
        
        table_name = cls.LAYER_MAPPING[layer_name]
        
        # Préparer la géométrie
        geom_wkt = geometry.wkt
        
        # Requête d'intersection
        query = f"""
            SELECT 
                *,
                ST_AsGeoJSON(geom) as geometry_json,
                ST_Area(ST_Intersection(geom, ST_GeomFromText(%s, 32631))) as intersection_area,
                ST_Area(ST_GeomFromText(%s, 32631)) as parcel_area
            FROM {table_name}
            WHERE ST_Intersects(
                geom, 
                {'ST_Buffer(ST_GeomFromText(%s, 32631), %s)' if buffer_distance > 0 else 'ST_GeomFromText(%s, 32631)'}
            )
        """
        
        params = [geom_wkt, geom_wkt]
        if buffer_distance > 0:
            params.extend([geom_wkt, buffer_distance])
        else:
            params.append(geom_wkt)
        
        intersections = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    
                    # Calculer le pourcentage de chevauchement
                    if row_dict['intersection_area'] and row_dict['parcel_area']:
                        overlap_percentage = (row_dict['intersection_area'] / row_dict['parcel_area']) * 100
                    else:
                        overlap_percentage = 0
                    
                    intersections.append({
                        'layer': layer_name,
                        'object_id': row_dict['id'],
                        'properties': {k: v for k, v in row_dict.items() if k not in ['geom', 'geometry_json']},
                        'geometry': json.loads(row_dict['geometry_json']),
                        'intersection_area': row_dict['intersection_area'],
                        'overlap_percentage': overlap_percentage,
                    })
                    
            except Exception as e:
                logger.error(f"Erreur lors de la vérification d'intersection avec {layer_name}: {e}")
                raise
        
        return intersections
    
    @classmethod
    def check_within(cls, geometry, layer_name):
        """
        Vérifie si la géométrie est entièrement contenue dans une couche
        
        Args:
            geometry: Géométrie à vérifier
            layer_name: Nom de la couche ANDF
        
        Returns:
            Liste des objets qui contiennent la géométrie
        """
        if layer_name not in cls.LAYER_MAPPING:
            raise ValueError(f"Couche {layer_name} non reconnue")
        
        table_name = cls.LAYER_MAPPING[layer_name]
        geom_wkt = geometry.wkt
        
        query = f"""
            SELECT 
                *,
                ST_AsGeoJSON(geom) as geometry_json
            FROM {table_name}
            WHERE ST_Within(ST_GeomFromText(%s, 32631), geom)
        """
        
        within_objects = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(query, [geom_wkt])
                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    within_objects.append({
                        'layer': layer_name,
                        'object_id': row_dict['id'],
                        'properties': {k: v for k, v in row_dict.items() if k not in ['geom', 'geometry_json']},
                        'geometry': json.loads(row_dict['geometry_json']),
                    })
                    
            except Exception as e:
                logger.error(f"Erreur lors de la vérification within avec {layer_name}: {e}")
                raise
        
        return within_objects
    
    @classmethod
    def get_nearby_parcels(cls, geometry, distance_meters=100):
        """
        Trouve les parcelles existantes à proximité
        
        Args:
            geometry: Géométrie de référence
            distance_meters: Distance de recherche en mètres
        
        Returns:
            Liste des parcelles proches
        """
        geom_wkt = geometry.wkt
        
        query = """
            SELECT 
                *,
                ST_AsGeoJSON(geom) as geometry_json,
                ST_Distance(geom, ST_GeomFromText(%s, 32631)) as distance
            FROM parcelles
            WHERE ST_DWithin(geom, ST_GeomFromText(%s, 32631), %s)
            ORDER BY distance
            LIMIT 50
        """
        
        nearby_parcels = []
        with connection.cursor() as cursor:
            try:
                cursor.execute(query, [geom_wkt, geom_wkt, distance_meters])
                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))
                    nearby_parcels.append({
                        'object_id': row_dict['id'],
                        'properties': {k: v for k, v in row_dict.items() if k not in ['geom', 'geometry_json']},
                        'geometry': json.loads(row_dict['geometry_json']),
                        'distance': row_dict['distance'],
                    })
                    
            except Exception as e:
                logger.error(f"Erreur lors de la recherche de parcelles proches: {e}")
                raise
        
        return nearby_parcels

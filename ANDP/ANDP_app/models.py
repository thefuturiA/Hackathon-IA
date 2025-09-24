from django.db import models

# Create your models here.
from django.contrib.gis.db import models

class PublicUpload(models.Model):
    file = models.FileField(upload_to="uploads/public/")
    session_id = models.CharField(max_length=64)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Parcel(models.Model):
    geometry = models.PolygonField(srid=4326)
    status = models.CharField(
        max_length=50,
        choices=[("secure", "Sécurisée"), ("conflict", "Conflit"), ("restricted", "Restreinte")],
        default="secure"
    )
    issues = models.JSONField(default=list)
    upload = models.ForeignKey(PublicUpload, on_delete=models.CASCADE, related_name="parcels")
    created_at = models.DateTimeField(auto_now_add=True)

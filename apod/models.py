from django.db import models

class Apod(models.Model):
    date = models.DateField(unique=True)
    title = models.CharField(max_length=255)
    explanation = models.TextField()
    url = models.URLField()
    hdurl = models.URLField(blank=True, null=True)  
    media_type = models.CharField(max_length=10)
    copyright = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self): 
        return f"{self.date} - {self.title}"
    
class CelestialBody(models.Model):
    name = models.CharField(max_length=255, unique=True)
    body_type = models.CharField(max_length=100)
    right_ascension = models.CharField(max_length=50)
    declination = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    
class Collection(models.Model):
    apod = models.ForeignKey(Apod, on_delete=models.CASCADE)
    celestial_body = models.ForeignKey(CelestialBody, on_delete=models.CASCADE)
    collected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.celestial_body.name} - {self.apod.date}"
    
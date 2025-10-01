from django.db import models

# Create your models here.

class Analysis(models.Model):
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField()
    topics = models.JSONField(default=list)
    sentiment = models.CharField(max_length=10)
    keywords = models.JSONField(default=list)
    summary = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.text[:30]

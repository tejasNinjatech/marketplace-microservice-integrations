from django.db import models

# Create your models here.
from django.db import models

class Event(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sell_mode = models.CharField(max_length=50)

    def __str__(self):
        return self.name

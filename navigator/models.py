from django.db import models

# Create your models here.

class Room(models.Model):
    name = models.CharField(max_length=100)
    floor = models.IntegerField()
    order = models.IntegerField()
    location_type = models.CharField(max_length=10, choices=[('upstairs', 'Upstairs'), ('downstairs', 'Downstairs')], default='downstairs')

    def __str__(self):
        return f"{self.name} (Floor {self.floor}, Order {self.order})"

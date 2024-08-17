from django.db import models

class Location(models.Model):
    formatted_address = models.CharField(max_length=255, unique=True, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.formatted_address


class Address(models.Model):
    address = models.CharField(max_length=255, unique=True, db_index=True)
    location = models.ForeignKey(
        Location, related_name="addresses", on_delete=models.CASCADE
    )
    
    def save(self, *args, **kwargs):
        self.address = self.address.lower()
        super(Address, self).save(*args, **kwargs)

    def __str__(self):
        return self.address

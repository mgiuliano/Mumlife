from django.db import models

class PostcodeManager(models.Manager):
    def all_areas(self):
        """Return all postcode areas as a list."""
        return [p['postcode'] for p in self.all().values('postcode')]

    def get_related(self, area):
        """Given a postcode area (i.e.: SE22),
           return all Postcodes with the same region (i.e.: Southwark).

           Returns a QuerySet.
        """
        try:
            postcode = self.get(postcode=area.upper())
        except Postcode.DoesNotExist:
            return self.none()
        else:
            return self.filter(region=postcode.region)
    
class Postcode(models.Model):
    postcode = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    easting = models.IntegerField(null=True, blank=True)
    northing = models.IntegerField(null=True, blank=True)
    grid_ref = models.CharField(max_length=255, null=True, blank=True)
    town_area = models.TextField()
    region = models.CharField(max_length=255)
    postcodes = models.IntegerField(null=True, blank=True)
    active_postcodes = models.IntegerField(null=True, blank=True)

    objects = PostcodeManager()

    def __unicode__(self):
        return '{} [{} {}] / {}'.format(self.postcode, self.longitude, self.latitude, self.region)

    def __repr__(self):
        return '<Postcode {} [{} {}] / {}>'.format(self.postcode, self.longitude, self.latitude, self.region)

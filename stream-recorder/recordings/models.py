from django.conf import settings
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from django.template.defaultfilters import slugify
import uuid
    
    # Create your models here.
class RecordingSource(models.Model):
    title = models.CharField(max_length=200)
    source_url = models.URLField()
    created_date = models.DateTimeField(default=timezone.now)
    last_publish_date = models.DateTimeField(blank=True, null=True)
    rebroadcast_active = models.BooleanField(default=False)
    mySlug = models.SlugField(default=uuid.uuid4, blank=True)
    hls_url = models.URLField(blank=True, null=True)

    def mark_alive(self):
        self.last_publish_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        #if not self.id:
        # Newly created object, so set slug
        newname = self.title.replace('_', ' ')
        self.mySlug = slugify(newname)
        self.title = newname
        super(RecordingSource, self).save(*args, **kwargs)

# Create your models here.
class Recording(models.Model):
    source =models.ForeignKey(RecordingSource, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    transcript = models.TextField()
    triggers = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    last_publish_date = models.DateTimeField(blank=True, null=True)
    triggers = TreeManyToManyField('RecordingTrigger', related_name='catalogitems')
    mySlug = models.SlugField(default=uuid.uuid4, blank=True)

    def mark_alive(self):
        self.last_publish_date = timezone.now()
        self.save()

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        #if not self.id:
        # Newly created object, so set slug
        newname = self.title.replace('_', ' ')
        self.mySlug = slugify(newname)
        self.title = newname
        super(Recording, self).save(*args, **kwargs)

class RecordingTrigger(MPTTModel):
    name = models.CharField(default='', max_length=200, unique=True)
    description = models.TextField(max_length=500, default='', blank=True)
    icon = models.TextField(max_length=500, default='', blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    mySlug = models.SlugField(default=uuid.uuid4, blank=True)
    filterInclusively = models.BooleanField(default=True)
    filterPriority = models.IntegerField(default=10)
    created_on = models.DateTimeField(null=True, blank=True)

    def human_readable_name(self):
        return self.name.title()

    def __unicode__(self):
        return self.name
    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']
    

    def save(self, *args, **kwargs):
        #if not self.id:
        # Newly created object, so set slug
        newname = self.name.replace('_', ' ')
        self.mySlug = slugify(newname)
        self.name = newname
        super(RecordingTrigger, self).save(*args, **kwargs)
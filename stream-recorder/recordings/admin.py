from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin
from mptt.admin import MPTTModelAdmin
from django.forms import CheckboxSelectMultiple
from .models import RecordingTrigger, Recording, RecordingSource
from . import models as models

class RecordingTriggerAdmin(MPTTModelAdmin):
    list_display = ( 'name', )
    # specify pixel amount for this ModelAdmin only:
    mptt_level_indent = 20

class RecordingAdmin(admin.ModelAdmin):
    list_display = ( 'title', )
    search_fields = ['title', 'description']
    formfield_overrides = {
        models.TreeManyToManyField: {'widget': CheckboxSelectMultiple},
    }
class RecordingSourceAdmin(admin.ModelAdmin):
    list_display = ( 'title', )
    search_fields = ['title', 'description']

admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingTrigger, RecordingTriggerAdmin)
admin.site.register(RecordingSource, RecordingSourceAdmin)
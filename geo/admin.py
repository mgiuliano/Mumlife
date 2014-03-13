# geo/admin.py
from django.contrib import admin

class PostcodeAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'town_area', 'region')
    list_filter = ('region',)
    search_fields = ('postcode', 'town_area', 'region')

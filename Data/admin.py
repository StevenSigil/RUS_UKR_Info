from django.contrib import admin
from .models import City, State, Country

# Register your models here.
admin.site.register(City)
admin.site.register(State)
admin.site.register(Country)

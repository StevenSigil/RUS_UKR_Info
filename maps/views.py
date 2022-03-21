from django.shortcuts import render, redirect
from django.views.generic import ListView

import folium

from Data.models import City, State, Country
from maps.ExtData import get_city_geometry


class StatesListView(ListView):
    ''' Generic list view of all states '''
    template_name = 'maps/states.html'
    context_object_name = 'list_of_states'
    paginate_by = 10
    model = State


def geo_map(request, loc_type, loc_id):
    # Get location Data
    if loc_type == 'city':
        location = City.objects.get(id=loc_id)
    if loc_type == 'state':
        location = State.objects.get(id=loc_id)
    if loc_type == 'country':
        location = Country.objects.get(id=loc_id)

    # Get geojson data
    geometry = get_city_geometry(location, True)

    lat, lon = location.latitude, location.longitude

    coordinates = (lat, lon)

    m = folium.Map(coordinates, zoom_start=4, tiles='Stamen Terrain')

    # Popup for clicking on location
    popup_html = folium.Html(f'<b>{lat}</b><br/><b>{lon}</b>', True)
    popup = folium.Popup(popup_html)

    # Marker of specified location
    folium.Marker(coordinates, popup=popup).add_to(m)

    # GeoJson of location
    folium.GeoJson(geometry, name=location.name).add_to(m)

    # Visual layers
    folium.raster_layers.TileLayer('Stamen Terrain').add_to(m)
    folium.raster_layers.TileLayer('Stamen Toner').add_to(m)
    folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m)
    folium.LayerControl().add_to(m)

    # Get HTML of map
    m = m._repr_html_()

    return render(request, 'maps/geomap.html', {'map': m})


def map_view(request, latitude, longitude):

    coordinates = (latitude, longitude)

    m = folium.Map(coordinates, zoom_start=4, tiles='Stamen Terrain')

    # Popup for clicking on location
    popup_html = folium.Html(f'<b>{latitude}</b><br/><b>{longitude}</b>', True)
    popup = folium.Popup(popup_html)

    # Marker of specified location
    folium.Marker(coordinates, popup=popup).add_to(m)

    # Visual layers
    folium.raster_layers.TileLayer('Stamen Terrain').add_to(m)
    folium.raster_layers.TileLayer('Stamen Toner').add_to(m)
    folium.raster_layers.TileLayer('Stamen Watercolor').add_to(m)
    folium.LayerControl().add_to(m)

    m = m._repr_html_()
    return render(request, 'maps/index.html', {'map': m})

from Data.models import City, State, Country
from helpers.object_helpers import search_list_for_obj

# from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
# from OSMPythonTools.nominatim import Nominatim

import requests
import json


def get_city_geometry(loc: City or State or Country, write: bool = False):

    url = 'https://nominatim.openstreetmap.org/search?'
    params = dict({
        'q': loc.name,
        'polygon_geojson': 1,
        'format': 'jsonv2'
    })
    if loc.country:
        params['country'] = loc.country

    query_string = url + '&'.join([str(k)+'='+str(v) for k, v in params.items()])

    response = requests.get(url, params)
    data = response.json()

    if write:
        with open('../Data/Test1-data.json', 'w', encoding='utf-8') as wf:
            json.dump(data, wf, indent=4, ensure_ascii=False)
        print("\nFILE WRITTEN TO:\t~/Data/Test1-data.json")

    # Attempt to find the right object in response - should be osm_type=relation,geojson.coordinates.count>2
    objs_with_relation = search_list_for_obj(data, 'osm_type', 'relation')

    # Multiple matches - Do further matching -- 'error' already printed from search
    if type(objs_with_relation) == list:
        return

    # Single match - Continue to get geo data
    if type(objs_with_relation) == dict:
        print('\nFOUND CLOSEST MATCH WITH DISPLAY NAME:\t', objs_with_relation['display_name'])

        # Return geojson for plotting
        geojson = objs_with_relation['geojson']
        return geojson

    return print("\n\nSOMETHING WENT VERY WRONG!!!")

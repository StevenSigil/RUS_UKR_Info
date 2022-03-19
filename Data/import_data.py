from .models import *


def create_city_model(city_id=1, single_city=None):
    print("\nCITY ID:\t", city_id)

    # If a city object is not passed in - open json data and find the instance
    if not single_city:
        city_data = get_json_data('cities')
        # Target City - Should only return 1 entry in dict fmt.
        ci_data = search_list_for_obj(city_data, 'id', city_id)
    else:
        ci_data = single_city

    # Check if state is in DB - Create if not
    db_state = query_db_for_state(ci_data['state_id'])
    if not db_state:
        create_state_model(ci_data['state_id'])

    # Check if country is in DB - Create if not
    db_country = query_db_for_country(ci_data['country_id'])
    if not db_country:
        create_country_model(ci_data['country_id'])

    Ci = City.create(**ci_data)
    print(f'Created CITY: {Ci.name}\tID:{Ci.id}')
    return Ci.save()


def create_state_model(state_id=5, single_state=None):
    print("\nSTATE ID:\t", state_id)

    # If a state object is not passed in - open json data and find the instance
    if not single_state:
        state_data = get_json_data('states')
        # Target State
        st_data = search_list_for_obj(state_data, 'id', state_id)
    else:
        st_data = single_state

    # Check if country is in DB - Create if not
    db_country = query_db_for_country(st_data['country_id'])
    if not db_country:
        create_country_model(st_data['country_id'])

    St = State.create(**st_data)
    print(f'Created STATE: {St.name}\tID:{St.id}')
    return St.save()


def create_country_model(country_id=1, single_country=None):
    print("\nCOUNTRY ID:\t", 'country_id')

    # If a country object is not passed in - open json data and find the instance
    if not single_country:
        country_data = get_json_data('countries')
        # Target Country
        co_data = search_list_for_obj(country_data, 'id', country_id)
    else:
        co_data = single_country

    Co = Country.create(**co_data)
    print(f'Created COUNTRY: {Co.name}\tID:{Co.id}')
    return Co.save()


def get_json_data(filename):
    import json

    file = f'../Data/{filename}.json'
    with open(file, encoding='utf-8') as df:
        jd = json.loads(df.read())
    return jd


def search_list_for_obj(lst: list, key: str, value: str):
    ret_lst = [el for el in lst if el[key] == value]

    if len(ret_lst) == 1:
        return ret_lst[0]
    print('\nFOUND MULTIPLE OBJECTS IN LIST!')
    return ret_lst


def run_cities():
    cities = get_json_data('cities')
    for city in cities:
        c_id = city['id']
        create_city_model(c_id, city)


def run_states():
    states = get_json_data('states')
    for state in states:
        s_id = state['id']
        create_state_model(s_id, state)


def run_countries():
    countries = get_json_data('countries')
    for country in countries:
        c_id = country['id']
        create_country_model(c_id)

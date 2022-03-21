from helpers.object_helpers import search_list_for_obj
from .models import *


def convert_DT_to_UTC(dt: str):
    ''' 
        Expecting `dt` to be a string formatted in ISO-8601 format without TZ info but known to be from GMT timezone - Converts to UTC ISO-8601 format
    '''
    # Get the tz offset part of string at my location (GMT)
    gmt_offset_str = datetime.now().astimezone().isoformat()[-6:]
    # Add offset to the `dt` string
    dt = dt + gmt_offset_str
    # transform to ISO 8601 format, TZ info will only be 'Z'
    utc_dt = datetime.fromisoformat(dt).astimezone(utc).replace(tzinfo=None).isoformat() + 'Z'

    return utc_dt


def create_message_model(msg_id=1, single_message=None):
    ''' Intended to be used on a json file from Telegram channel history download '''

    # If a message object is not passed in - open json data and find the instance
    if not single_message:
        data = get_json_data('messages')
        data = data['messages']
        # Retrieve only the objects with 'type':'message'
        m_data = search_list_for_obj(data, 'type', 'message')
        # Target message from `msg_id`
        message = search_list_for_obj(m_data, 'id', msg_id)

        if not message or len(message) == 0:
            raise Exception(f'\n\nMESSAGE WITH ID: "{msg_id}" NOT FOUND!')
    else:
        message = single_message

    # Transform time value to ISO-UTCz format
    message['date'] = convert_DT_to_UTC(message['date'])

    # Create & return Message instance...
    Msg = Message.create(**message)
    Msg.save()
    print(f'Created MESSAGE: {Msg.date}\tID:{Msg.id}')
    return Msg


def run_messages():
    data = get_json_data('messages')['messages']
    # Retrieve only the objects with 'type':'message'
    msg_lst = search_list_for_obj(data, 'type', 'message')

    for msg in msg_lst[0:20]:
        m_id = msg['id']
        create_message_model(None, msg)


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


# def get_required_keys():
#     # TEMP: Getting required keys - used in create_message_model
#     rKeys = []
#     nrKeys = []

#     lenOfMsgLst = len(msg_lst)

#     for msg in msg_lst:
#         keys = msg.keys()
#         for k in keys:
#             matches = search_list_for_obj(msg_lst, k, None)
#             print(f"KEY:     {k}\nFOUND:   {len(matches)}\nOF:      {lenOfMsgLst}")

#             if len(matches) == lenOfMsgLst and k not in rKeys:
#                 rKeys.append(k)
#             elif len(matches) != lenOfMsgLst and k not in nrKeys:
#                 nrKeys.append(k)

#     print('\n\nREQUIRED KEYS:\n\t', rKeys, '\nREQUIRED COUNT:\t', len(rKeys))
#     print('\n\nOPTIONAL KEYS:\n\t', nrKeys, '\nOPTIONAL COUNT:\t', len(nrKeys))
#     return rKeys

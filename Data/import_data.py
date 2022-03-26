import spacy
from datetime import datetime

from helpers.object_helpers import search_list_for_obj
from helpers.nlp_messages import setup_spacy, matches_subjVerbDobj, check_token_is_place
from Data.models import *


def create_EventMessage_from_TelegramMessage(telegram_message: TelegramMessage):
    ''' Converts `TelegramMessage` instance into a new `MessageEvent` instance. 
        Attempts to lift relevant keywords from `TelegramMessage.text` for brevity 
        when displaying on maps.
    '''

    # Start Spacy and convert `telegram_message.text` to a `Spacy...Doc`
    original_message = telegram_message
    event_date = datetime.isoformat(telegram_message.date)
    doc = setup_spacy(telegram_message.text)

    subject = None
    action = None
    text = telegram_message.text  # Changes if tokens in text matches subjVerbDobj pattern
    is_multi_sentence = None
    contains_places = None
    cities = []
    states = []
    countries = []
    classification = None  # TODO

    # Check how many sentences are in text -> assign to `is_multi_sentence`
    is_multi_sentence = bool(len([sent for sent in doc.sents]) > 1)

    for token in doc:

        # Get subject->action->context extracts
        matches_pattern = matches_subjVerbDobj(token)
        if matches_pattern:
            # Lift `subject`, `action`, `text` from result
            subject = matches_pattern['subj']
            action = matches_pattern['token']
            text = ' '.join(list(matches_pattern.values()))

        # Get City, State, Country places - Check if `token` is a 'GPE' `entity`
        if token.ent_type_ == 'GPE':
            # Use exact matcher -> sub func will handle if no exact match found.
            entity = check_token_is_place(token, True)
        else:
            entity = check_token_is_place(token, False)

        if entity:
            if type(entity) == Country:
                countries.append(entity)
            if type(entity) == State:
                states.append(entity)
            if type(entity) == City:
                cities.append(entity)

        contains_places = bool(entity)

        # TODO GET CLASSIFICATION!
        # TODO HANDLE MULTI-SENTENCE CONDITIONS

    # All variables retrieved to create `EventMessage`
    newME = MessageEvent(text=text,
                         original_message=original_message,
                         event_date=event_date,
                         subject=subject,
                         action=action,
                         classification=classification,
                         is_multi_sentence=is_multi_sentence,
                         contains_places=contains_places,
                         )

    newME.save()

    # Reverse relation additions
    if cities:
        [city.messageevent_set.add(newME.id) for city in cities]
    if states:
        [state.messageevent_set.add(newME.id) for state in states]
    if countries:
        [country.messageevent_set.add(newME.id) for country in countries]

    return newME


def create_TelegramMessage_model(msg_id=1, single_message=None):
    ''' Creates a new `TelegramMessage` instance. 
        Intended to be used on a json file from a Telegram channel history download. 
            - Reference formatting of ~/../Data/message.json - or Telegram docs.
    '''

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

    # Create & return TelegramMessage instance...
    Msg = TelegramMessage.create(**message)
    Msg.save()
    print(f'Created MESSAGE: {Msg.date}\tID:{Msg.id}')
    return Msg


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

    # If a country object is not passed in ->
    # open json data and find the instance
    if not single_country:
        country_data = get_json_data('countries')
        # Target Country
        co_data = search_list_for_obj(country_data, 'id', country_id)
    else:
        co_data = single_country

    Co = Country.create(**co_data)
    print(f'Created COUNTRY: {Co.name}\tID:{Co.id}')
    return Co.save()


#####################################################################################
################################## HELPERS/RUNNERS ##################################
def get_json_data(filename):
    import json

    file = f'../Data/{filename}.json'
    with open(file, encoding='utf-8') as df:
        jd = json.loads(df.read())
    return jd


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


def run_messages():
    data = get_json_data('messages')['messages']
    # Retrieve only the objects with 'type':'message'
    msg_lst = search_list_for_obj(data, 'type', 'message')

    for msg in msg_lst[0:20]:
        m_id = msg['id']
        create_TelegramMessage_model(None, msg)

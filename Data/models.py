from django.db import models
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers

import json
import uuid

from pytz import timezone, utc
from datetime import datetime


class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=260)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    wikiDataId = models.CharField(max_length=10)
    state = models.ForeignKey('State',
                              models.PROTECT,
                              related_name='cities',
                              related_query_name='city',
                              null=True)
    country = models.ForeignKey('Country',
                                models.PROTECT,
                                related_name='cities',
                                related_query_name='city',
                                null=True)
    # Transformed keys: state_id, state_code, state_name, country_id, country_code, country_name

    @classmethod
    def create(cls, **kwargs):
        model_fields = [f.name for f in cls._meta.get_fields()]
        relevant_kwargs = build_model_fields_from_kwargs(model_fields, kwargs)

        # Set related fields
        relevant_kwargs['state'] = query_db_for_state(kwargs['state_id'])[0]
        relevant_kwargs['country'] = query_db_for_country(kwargs['country_id'])[0]

        return cls(**relevant_kwargs)

    def __str__(self):
        return json.dumps(model_to_dict(self))


class State(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=260)
    state_code = models.CharField(max_length=4)
    type = models.CharField(max_length=100, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    country = models.ForeignKey('Country',
                                models.PROTECT,
                                related_name='states',
                                related_query_name='state',
                                null=True)
    # Transformed keys: country_id, country_code, country_name

    @classmethod
    def create(cls, **kwargs):
        model_fields = [f.name for f in cls._meta.get_fields()]
        relevant_kwargs = build_model_fields_from_kwargs(model_fields, kwargs)

        # Set related field
        relevant_kwargs['country'] = query_db_for_country(kwargs['country_id'])[0]

        return cls(**relevant_kwargs)

    def __str__(self):
        return json.dumps(model_to_dict(self))


class Country(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=260)
    iso3 = models.CharField(max_length=4)
    iso2 = models.CharField(max_length=4)
    numeric_code = models.IntegerField()
    phone_code = models.CharField(max_length=15)
    capital = models.CharField(max_length=260)
    currency = models.CharField(max_length=5)
    currency_name = models.CharField(max_length=260)
    currency_symbol = models.CharField(max_length=10)
    tld = models.CharField(max_length=10)
    native = models.CharField(max_length=260, null=True)
    region = models.CharField(max_length=100)
    subregion = models.CharField(max_length=100)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    emoji = models.CharField(max_length=10)
    emojiU = models.CharField(max_length=100)

    @classmethod
    def create(cls, **kwargs):
        model_fields = [f.name for f in cls._meta.get_fields()]
        relevant_kwargs = build_model_fields_from_kwargs(model_fields, kwargs)
        return cls(**relevant_kwargs)

    def __str__(self):
        return json.dumps(model_to_dict(self))


class TelegramMessage(models.Model):
    id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=100)
    date = models.DateTimeField(editable=True)  # ############### TRANSFORMS ON SAVE
    from_name = models.CharField(max_length=260)  # ############# TRANSFORMS ON FIELD: 'from'
    from_id = models.CharField(max_length=260)
    text = models.TextField()
    edited = models.DateTimeField(editable=True, null=True)  # ## TRANSFORMS ON SAVE
    reply_to_message_id = models.ForeignKey('self', models.PROTECT, null=True, related_name='+')
    # TODO find and change to appropriate file-fields!
    file = models.CharField(max_length=260, null=True)
    thumbnail = models.CharField(max_length=260, null=True)
    media_type = models.CharField(max_length=100, null=True)
    mime_type = models.CharField(max_length=100, null=True)
    duration_seconds = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    photo = models.CharField(max_length=260, null=True)
    forwarded_from = models.CharField(max_length=260, null=True)

    @classmethod
    def create(cls, **kwargs):
        # Transform 'from' key in data to 'from_name' to match model
        if 'from' in kwargs.keys():
            kwargs['from_name'] = kwargs.pop('from')

        # Remove `reply_to_message_id` from `kwargs` and set non-directly
        if 'reply_to_message_id' in kwargs.keys():
            reply_message_id = kwargs.pop('reply_to_message_id')
            found_reply = TelegramMessage.objects.filter(id=reply_message_id)
            if found_reply:
                cls.set(found_reply)

        # Get relevant kwargs from passed in info
        model_fields = [f.name for f in cls._meta.get_fields()]
        relevant_kwargs = build_model_fields_from_kwargs(model_fields, kwargs)

        # Convert ISO time to datetime.datetime instance on 'date' field
        dt_field = relevant_kwargs['date']
        date_field = transform_iso_to_dt(dt_field)
        if date_field:
            relevant_kwargs['date'] = date_field
        else:
            raise Exception(
                f"FIELD: 'date' MUST BE IN AN ISO FORMAT TO BE SAVED!\nRECEIVED:\t{dt_field}")

        # Convert ISO time to datetime.datetime instance on 'edited' field
        if 'edited' in relevant_kwargs.keys():
            edited_field = transform_iso_to_dt(relevant_kwargs['edited'])
            if edited_field:
                relevant_kwargs['edited'] = edited_field
            else:
                raise Exception(
                    f"FIELD: 'edited' MUST BE IN AN ISO FORMATE TO BE SAVED!\nRECEIVED:\t{relevant_kwargs['edited']}")

        return cls(**relevant_kwargs)

    def __str__(self):
        return json.dumps(model_to_dict(self), cls=DjangoJSONEncoder)


class MessageEvent(models.Model):
    ''' TelegramMessage that has been parsed/classified via NLP - with City,
        State, Country info extracted - and `classification` of event identified, ready
        to display on map.
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_message = models.ForeignKey(
        'TelegramMessage', on_delete=models.CASCADE, related_name='parsed')
    event_date = models.DateTimeField(editable=True, null=True)
    subject = models.CharField(max_length=260, null=True)  # # NLP parsed SUBJ
    action = models.TextField(null=True)  # NLP parsed SUBJ-parent group of tokens
    text = models.TextField()  # NLP parsed text

    # Derrived from `action` field - reduced to choices in `EventTypes`
    classification = models.ForeignKey(
        'EventClassification', on_delete=models.SET_DEFAULT, default=get_na_event_type, null=True)

    is_multi_sentence = models.BooleanField(default=False)
    contains_places = models.BooleanField(default=False)
    # Can have many Cities, States, and/or Countries
    cities = models.ManyToManyField('City', serialize=True)
    states = models.ManyToManyField('State', serialize=True)
    countries = models.ManyToManyField('Country', serialize=True)

    def __str__(self):
        return serializers.serialize('json', MessageEvent.objects.filter(id=self.id))
        # return json.dumps(model_to_dict(self), cls=DjangoJSONEncoder)


class EventClassification(models.Model):
    class EventTypes(models.TextChoices):
        # TODO Use below (commented-out) specific types - with icons later...
        NA = 'NA'  # <---------------- Default value for `MessageEvent`
        ACTION_AGGRESSOR = 'ACTA'  # # NORMAL PIN - RED
        ACTION_DEFENDER = 'ACTD'  # ## NORMAL PIN - VIOLET
        AREA_EXPAND = 'AREX'  # ###### ADD GeoBoundary
        AREA_CONTRACT = 'ARCT'  # #### REMOVE GeoBoundary
        DIPLOMATIC = 'DIPL'  # ####### NORMAL PIN - TBD color

        # AIR_STRIKE = 'AIRS'
        # SIREN = 'SIRN'
        # DEATH = 'DEAT'
        # EQUIPMENT_MOVEMENT = 'EQMV'
        # TALKING = 'TALK'
        # BUILDING_STRIKE = 'BLDS'
        # FIRE = 'FIRE'
        # JET = 'JET'
        # HELICOPTER = 'HELI'
        # VESSEL = 'VESL'
        # PROTEST = 'PROT'
        # EXPLOSION = 'EXPL'
        # DRONE = 'DRON'
        # REFUGEE = 'RFUG'
        # ARREST = 'ARST'
        # RAIL_ROAD = 'RAIL'
        # NO_ACCESS = 'NOAC'
        # PHONE = 'PHON'
        # SANCTION = 'SANC'

    eType = models.CharField(max_length=4, choices=EventTypes.choices, default='NA')
    icon = models.FileField(upload_to='events/icons/', null=True)  # location of icon in storage

    def __str__(self):
        return json.dumps(model_to_dict(self), cls=DjangoJSONEncoder)


# TODO Get/Make custom markers/icons for mapping - use in view like `folium.features.CustomIcon()` in Markers


###############################################################################################
###################################### HELPER FUNCTIONS  ######################################

def get_na_event_type(self):
    ''' Gets/Creates `EventClassification` with default `EventType` set to NA '''
    return EventClassification.objects.get_or_create(eType="NA")


def transform_iso_to_dt(dt_str: str):
    ''' Returns either a datetime.datetime instance or `False` if unable to transform from iso-string '''
    try:
        ret = datetime.fromisoformat(dt_str)
    except:
        try:
            ret = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return False
        return ret
    return ret


def query_db_for_country(c_id):
    ''' Helper func. for 'create' methods in classes.
        Returns None if not found.
    '''
    query = Country.objects.filter(id=c_id)

    if query.exists() and len(query) == 1:
        return query
    return None


def query_db_for_state(s_id):
    ''' Helper func. for 'create' methods in classes.
        Returns None if not found.
    '''
    query = State.objects.filter(id=s_id)

    if query.exists() and len(query) == 1:
        return query
    return None


def query_db_for_city(c_id):
    ''' Helper func. for 'create' methods in classes.
        Returns None if not found.
    '''
    query = City.objects.filter(id=c_id)

    if query.exists() and len(query) == 1:
        return query
    return None


def build_model_fields_from_kwargs(fields, kwargs):
    ''' Intended to be used to filter out kwargs from raw input so `kwargs` 
        match to `fields` before setting related fields and creating Model 
        instances.
    '''
    kwargs_keys = kwargs.keys()
    build_obj = {}

    for key in kwargs_keys:
        if key in fields:
            build_obj[key] = kwargs[key]
        else:
            build_obj[key] = None
    return build_obj

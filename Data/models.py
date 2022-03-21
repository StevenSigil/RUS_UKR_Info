from django.db import models
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

import json

from pytz import timezone, utc
from datetime import datetime


class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
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
    name = models.CharField(max_length=200)
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
    name = models.CharField(max_length=250)
    iso3 = models.CharField(max_length=4)
    iso2 = models.CharField(max_length=4)
    numeric_code = models.IntegerField()
    phone_code = models.CharField(max_length=15)
    capital = models.CharField(max_length=200)
    currency = models.CharField(max_length=5)
    currency_name = models.CharField(max_length=200)
    currency_symbol = models.CharField(max_length=10)
    tld = models.CharField(max_length=10)
    native = models.CharField(max_length=200, null=True)
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


class Message(models.Model):
    id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=100)
    date = models.DateTimeField(editable=True)  # ############### TRANSFORMS ON SAVE
    from_name = models.CharField(max_length=250)  # ############# TRANSFORMS ON FIELD: 'from'
    from_id = models.CharField(max_length=250)
    text = models.TextField()
    edited = models.DateTimeField(editable=True, null=True)  # ## TRANSFORMS ON SAVE
    reply_to_message_id = models.ForeignKey('self', models.PROTECT, null=True)
    # TODO find and change to appropriate file-fields!
    file = models.CharField(max_length=250, null=True)
    thumbnail = models.CharField(max_length=250, null=True)
    media_type = models.CharField(max_length=100, null=True)
    mime_type = models.CharField(max_length=100, null=True)
    duration_seconds = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    photo = models.CharField(max_length=250, null=True)
    forwarded_from = models.CharField(max_length=250, null=True)

    @classmethod
    def create(cls, **kwargs):
        # Transform 'from' key in data to 'from_name' to match model
        if 'from' in kwargs.keys():
            kwargs['from_name'] = kwargs.pop('from')

        # Get relevant kwargs from passed in info
        model_fields = [f.name for f in cls._meta.get_fields()]
        relevant_kwargs = build_model_fields_from_kwargs(model_fields, kwargs)

        # Convert ISO time to datetime.datetime instance on 'date' field
        d_field = relevant_kwargs['date']
        date_field = transform_iso_to_dt(d_field)
        if date_field:
            relevant_kwargs['date'] = date_field
        else:
            raise Exception(
                f"FIELD: 'date' MUST BE IN AN ISO FORMAT TO BE SAVED!\nRECEIVED:\t{d_field}")

        # Convert ISO time to datetime.datetime instance on 'edited' field
        e_field = relevant_kwargs['edited']
        if e_field:
            edited_field = transform_iso_to_dt(e_field)
            if edited_field:
                relevant_kwargs['edited'] = edited_field
            else:
                raise Exception(
                    f"FIELD: 'edited' MUST BE IN AN ISO FORMATE TO BE SAVED!\nRECEIVED:\t{e_field}")

        return cls(**relevant_kwargs)

    def __str__(self):
        return json.dumps(model_to_dict(self), cls=DjangoJSONEncoder)


###############################################################################################
###################################### HELPER FUNCTIONS  ######################################
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

    # import re
    # regex = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
    # match_iso = re.compile(regex).match
    # try:
    #     if match_iso8601(dt_str) is not None:
    #         return True
    # except:
    #     pass
    # return False


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

    for f in fields:
        if f in kwargs_keys:
            build_obj[f] = kwargs[f]
        else:
            build_obj[f] = None
    return build_obj

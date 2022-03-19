from django.db import models
from django.forms.models import model_to_dict

import json


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

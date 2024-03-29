from typing import List, Iterable, Tuple

from mongoengine import *

from src.enums import ServiceType


class SubscribeSource(DynamicDocument):
    service_type = EnumField(ServiceType)
    service_func = StringField()
    name = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service_type', '+service_func']},
            {'fields': ['+service_type', '+service_func', '+name']},
        ]
    }

    @classmethod
    def add_subs(cls, stype: ServiceType, sfunc: str, name: str, channel: str):
        cls.objects(service_type=stype, service_func=sfunc, name=name).update_one(service_type=stype, service_func=sfunc, name=name, upsert=True)
        SubscribeChannel.objects(service_type=stype, service_func=sfunc, name=name).update_one(channel=channel, upsert=True)

    @classmethod
    def delete_subs(cls, stype: ServiceType, sfunc: str, name: str, channel: str):
        SubscribeChannel.objects(service_type=stype, service_func=sfunc, name=name, channel=channel).delete()
        if SubscribeChannel.objects(service_type=stype, service_func=sfunc, name=name).count() == 0:
            cls.objects(service_type=stype, service_func=sfunc, name=name).delete()

    @classmethod
    def export_subs_by_channel(cls, stype: ServiceType, sfunc: str, channel: str):
        for it in SubscribeChannel.objects(service_type=stype, service_func=sfunc, channel=channel):
            yield it.name

    @classmethod
    def get_subs(cls, stype: ServiceType, sfunc: str) -> Iterable[Tuple[str, List[str]]]:
        for it in cls.objects(service_type=stype, service_func=sfunc):
            channels = list(cls.get_channels(stype, sfunc, it.name))
            yield it.name, channels

    @classmethod
    def get_subs_by_channel(cls, stype: ServiceType, sfunc: str, channel: str) -> Iterable[Tuple[str, List[str]]]:
        for it in SubscribeChannel.objects(service_type=stype, service_func=sfunc, channel=channel):
            channels = list(cls.get_channels(stype, sfunc, it.name))
            yield it.name, channels

    @classmethod
    def get_channels(cls, stype: ServiceType, sfunc: str, name: str) -> Iterable[str]:
        for it in SubscribeChannel.objects(service_type=stype, service_func=sfunc, name=name):
            yield it.channel


class SubscribeChannel(DynamicDocument):
    service_type = EnumField(ServiceType)
    service_func = StringField()
    name = StringField()
    channel = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service_type', '+service_func', '+name']},
            {'fields': ['+service_type', '+service_func', '+channel']},
        ]
    }


class MissingSubs(DynamicDocument):
    service_type = EnumField(ServiceType)
    service_func = StringField()
    name = StringField()
    reason = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service_type', '+service_func', '+name']},
        ]
    }

    @classmethod
    def report(cls, service_type, service_func, name, reason):
        cls(service_type=service_type, service_func=service_func, name=name, reason=reason).save()

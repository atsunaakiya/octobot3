from typing import Optional

from mongoengine import *

from src.enums import ServiceType


class UserInfo(DynamicDocument):
    service = EnumField(ServiceType)
    username = StringField()
    nickname = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service']},
            {'fields': ['+service', '+username']},
        ]
    }

    @classmethod
    def set_nickname(cls, s: ServiceType, u: str, nickname: str):
        cls.objects(username=u, service=s).update_one(nickname=nickname, upsert=True)

    @classmethod
    def get_nickname(cls, s: ServiceType, u: str) -> Optional[str]:
        q = cls.objects(username=u, service=s)
        if q.count() == 0:
            return None
        else:
            return q[0].nickname


class UserRel(DynamicDocument):
    service = EnumField(ServiceType)
    from_user = StringField()
    to_user = StringField()
    item_id = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service', '+from_user']},
            {'fields': ['+service', '+from_user', '+to_user']},
            {'fields': ['+service', '+item_id']},
        ]
    }

    @classmethod
    def update_rel(cls, service: ServiceType, from_user: str, to_user: str, item_id: str):
        cls.objects(service=service, from_user=from_user, to_user=to_user, item_id=item_id).update_one(service=service, from_user=from_user, to_user=to_user, item_id=item_id, upsert=True)

    @classmethod
    def count_rels(cls, service: ServiceType, to_user: str) -> int:
        return cls.objects(service=service, to_user=to_user).count()

from mongoengine import *

from src.enums import ServiceType


class PostRecord(DynamicDocument):
    pull_service = EnumField(ServiceType)
    pull_id = StringField()
    post_service = EnumField(ServiceType)
    post_id = StringField()
    channel = StringField()

    meta = {
        'indexes': [
            {'fields': ['+pull_service', '+pull_id', '+post_service', '+post_id', '+channel']},
        ]
    }

    @classmethod
    def put_record(cls, pull_service: ServiceType, pull_id: str, post_service: ServiceType, post_id: str, channel: str):
        cls.objects(pull_service=pull_service, pull_id=pull_id,
                    post_service=post_service, post_id=post_id, channel=channel
                    ).update_one(
                    pull_service=pull_service, pull_id=pull_id,
                    post_service=post_service, post_id=post_id, channel=channel,
                    upsert=True
                    )
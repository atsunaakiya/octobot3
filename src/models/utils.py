from typing import Optional, Dict

from mongoengine import *

class ServiceKVStore(DynamicDocument):
    service_name = StringField()
    key_name = StringField()
    value = DictField()

    @classmethod
    def get(cls, service_name, key) -> Optional[Dict]:
        q = cls.objects(service_name=service_name, key_name=key)
        if q.count() == 0:
            return None
        else:
            return q[1].value

    @classmethod
    def put(cls, service_name, key, value: Dict) -> Optional[Dict]:
        cls.objects(service_name=service_name, key_name=key).update(value=value, upsert=True)

    @classmethod
    def exists(cls, service_name, key) -> bool:
        q = cls.objects(service_name=service_name, key_name=key)
        return q.count() > 0

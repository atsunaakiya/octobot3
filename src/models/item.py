from typing import Optional, Union, List, Tuple, Iterable, IO

from mongoengine import *

from src.data import FullItem, IndexItem
from src.enums import ServiceType, TaskStage, TaskStatus


class ItemInfo(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    source_id = StringField()
    url = StringField()
    content = StringField()
    image_urls = ListField()

    @classmethod
    def add_index(cls, idx: IndexItem, channels: List[str]):
        cls.objects(service=idx.service, item_id=idx.item_id).update_one(item_id=idx.item_id, upsert=True)
        for ch in channels:
            ItemChannel.objects(service=idx.service, item_id=idx.item_id, channel=ch).update_one(channel=ch, upsert=True)

    @classmethod
    def add_item(cls, item: FullItem, channels: List[str]):
        cls.objects(service=item.service, item_id=item.item_id).update_one(
            source_id=item.source_id,
            url=item.url,
            content=item.content,
            image_urls=item.image_urls,
            upsert=True
        )
        for ch in channels:
            ItemChannel.objects(service=item.service, item_id=item.item_id, channel=ch).update_one(channel=ch, upsert=True)

    @classmethod
    def poll_status_index(cls, stage: TaskStage, status: TaskStatus, limit=0) -> Iterable[FullItem]:
        for st in TaskStatusInfo.objects(stage=stage, stage_status=status):
            item = TaskStatusInfo.objects(service=st.service, item_id=st.item_id)[0]
            yield IndexItem(
                item_id=item.item_id,
                service=item.service
            )
            limit -= 1
            if limit == 0:
                return

    @classmethod
    def poll_status(cls, stage: TaskStage, status: TaskStatus, limit=0) -> Iterable[FullItem]:
        for st in TaskStatusInfo.objects(stage=stage, stage_status=status):
            item = cls.objects(service=st.service, item_id=st.item_id)[0]
            yield FullItem(
                item_id=item.item_id,
                service=item.service,
                content=item.content,
                source_id=item.source_id,
                url=item.url,
                image_urls=item.image_urls
            )
            limit -= 1
            if limit == 0:
                return

    @classmethod
    def get_status(cls, service: ServiceType, item_id: str) -> Tuple[TaskStage, TaskStatus]:
        q = TaskStatusInfo.objects(service=service, item_id=item_id)
        if q.count() == 0:
            return TaskStage.Indexing, TaskStatus.Queued
        else:
            it = q[0]
            return it.stage, it.stage_status

    @classmethod
    def set_status(cls, service: ServiceType, item_id: str, stage: TaskStage, status: TaskStatus):
        TaskStatusInfo.objects(service=service, item_id=item_id).update_one(stage=stage, stage_status=status, upsert=True)

    @classmethod
    def save_image(cls, item: FullItem, url: str, buffer: IO):
        ImageCache.objects(service=item.service, item_id=item.item_id, url=url).update(url=url, upsert=True)
        cache = ImageCache.objects(service=item.service, item_id=item.item_id, url=url)[0]
        cache.file.replace(buffer, content_type="image/png")
        cache.file.close()
        cache.save()

    @classmethod
    def count_status(cls):
        fetching = TaskStatusInfo.objects(stage=TaskStage.Fetching, stage_status=TaskStatus.Queued).count()
        downloading = TaskStatusInfo.objects(stage=TaskStage.Downloading, stage_status=TaskStatus.Queued).count()
        posting = TaskStatusInfo.objects(stage=TaskStage.Posting, stage_status=TaskStatus.Queued).count()
        cleaning = TaskStatusInfo.objects(stage=TaskStage.Cleaning, stage_status=TaskStatus.Queued).count()
        done = TaskStatusInfo.objects(stage=TaskStage.Done, stage_status=TaskStatus.Queued).count()
        failed = TaskStatusInfo.objects(stage_status=TaskStatus.Failed).count()
        return {
            'fetching': fetching,
            'downloading': downloading,
            'posting': posting,
            'cleaning': cleaning,
            'done': done,
            'failed': failed
        }


    @classmethod
    def get_channels(cls, item: FullItem):
        return [
            c.channel
            for c in ItemChannel.objects(service=item.service, item_id=item.item_id)
        ]

    @classmethod
    def get_images(cls, item: FullItem):
        return [
            ImageCache.objects(service=item.service, item_id=item.item_id, url=u)[0].file
            for u in item.image_urls
        ]

    @classmethod
    def clean_cache(cls, item: FullItem):
        for c in ImageCache.objects(service=item.service, item_id=item.item_id):
            c.file.delete()
            c.save()
        ImageCache.objects(service=item.service, item_id=item.item_id).delete()

    @classmethod
    def exists(cls, service, item_id):
        return TaskStatusInfo.objects(service=service, item_id=item_id).count() > 0


class ItemChannel(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    channel = StringField()


class TaskStatusInfo(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    stage = EnumField(TaskStage)
    stage_status = EnumField(TaskStatus)


class ImageCache(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    url = StringField()
    file = FileField()

from typing import Optional, Union, List, Tuple, Iterable, IO

from mongoengine import *

from src.data import FullItem, IndexItem
from src.enums import ServiceType, TaskStage, TaskStatus, SecondaryTaskStatus


class ItemInfo(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    source_id = StringField()
    url = StringField()
    content = StringField()
    image_urls = ListField()
    tags = ListField(null=True)
    attachment_urls = ListField(null=True)

    meta = {
        'indexes': [
            {'fields': ['+service', '+item_id']},
        ]
    }

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
            upsert=True,
            tags=item.tags,
            attachment_urls=item.attachment_urls
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

    def to_full_item(self):
        return FullItem(
            item_id=self.item_id,
            service=self.service,
            content=self.content,
            source_id=self.source_id,
            url=self.url,
            image_urls=self.image_urls,
            tags=self.tags,
            attachment_urls=self.attachment_urls
        )

    @classmethod
    def poll_status(cls, stage: TaskStage, status: TaskStatus, limit=0) -> Iterable[FullItem]:
        for st in TaskStatusInfo.objects(stage=stage, stage_status=status).order_by('poll_counter'):
            item = cls.objects(service=st.service, item_id=st.item_id)[0]
            st.poll_counter += 1
            st.save()
            yield item.to_full_item()
            limit -= 1
            if limit == 0:
                return

    @classmethod
    def abandon_tasks(cls, src_stage: TaskStage, src_status: TaskStatus, poll_limit: int, dst_stage: TaskStage, dst_status: TaskStatus):
        TaskStatusInfo.objects(stage=src_stage, stage_status=src_status,
                               poll_counter__gt=poll_limit).update(
            stage=dst_stage, stage_status=dst_status
        )


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
    def save_attachment_image(cls, item: FullItem, index: int, buffer: IO):
        AttachmentImageCache.objects(service=item.service, item_id=item.item_id, image_index=index).delete()
        cache = AttachmentImageCache(service=item.service, item_id=item.item_id, image_index=index)
        cache.file.replace(buffer, content_type="image/png")
        cache.file.close()
        cache.save()

    @classmethod
    def count_status(cls):
        fetching = TaskStatusInfo.objects(stage=TaskStage.Fetching, stage_status=TaskStatus.Queued).count()
        downloading = TaskStatusInfo.objects(stage=TaskStage.Downloading, stage_status=TaskStatus.Queued).count()
        posting = TaskStatusInfo.objects(stage=TaskStage.Posting, stage_status=TaskStatus.Queued).count()
        posting_pend = TaskStatusInfo.objects(stage=TaskStage.Posting, stage_status=TaskStatus.Pending).count()
        cleaning = TaskStatusInfo.objects(stage=TaskStage.Cleaning, stage_status=TaskStatus.Queued).count()
        done = TaskStatusInfo.objects(stage=TaskStage.Done, stage_status=TaskStatus.Queued).count()
        failed = TaskStatusInfo.objects(stage_status=TaskStatus.Failed).count()
        return {
            'fetching': fetching,
            'downloading': downloading,
            'posting': posting + posting_pend,
            'cleaning': cleaning,
            'done': done,
            'failed': failed
        }

    @classmethod
    def get_item(cls, service, item_id) -> FullItem:
        item = cls.objects(service=service, item_id=item_id)[0]
        return item.to_full_item()

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
            if ImageCache.objects(service=item.service, item_id=item.item_id, url=u).count() > 0
        ]

    @classmethod
    def get_attachment_images(cls, item: FullItem):
        return [
            f.file
            for f in AttachmentImageCache.objects(service=item.service, item_id=item.item_id).order_by('image_index')
        ]

    @classmethod
    def clean_cache(cls, item: FullItem):
        for c in ImageCache.objects(service=item.service, item_id=item.item_id):
            c.file.delete()
            c.save()
        ImageCache.objects(service=item.service, item_id=item.item_id).delete()
        for c in AttachmentImageCache.objects(service=item.service, item_id=item.item_id):
            c.file.delete()
            c.save()
        AttachmentImageCache.objects(service=item.service, item_id=item.item_id).delete()

    @classmethod
    def exists(cls, service, item_id):
        return TaskStatusInfo.objects(service=service, item_id=item_id).count() > 0

    @classmethod
    def clean_pending_items(cls):
        stages = [TaskStage.Fetching, TaskStage.Downloading]
        TaskStatusInfo.objects(stage__in=stages, stage_status=TaskStatus.Pending).update(stage_status=TaskStatus.Failed)
        SecondaryTask.objects(status=SecondaryTaskStatus.Pending).update(status=SecondaryTaskStatus.Queued)

        for t in TaskStatusInfo.objects(stage=TaskStage.Posting, stage_status=TaskStatus.Queued):
            if SecondaryTask.task_done(t.service, t.item_id):
                ItemInfo.set_status(t.service, t.item_id, TaskStage.Cleaning, TaskStatus.Queued)
                print("Cleaning finished task:", t.service, t.item_id)

    @classmethod
    def get_failures(cls, service: ServiceType, stage: TaskStage):
        return [
            cls.get_item(service=service, item_id=st.item_id)
            for st in TaskStatusInfo.objects(stage=stage, service=service, stage_status=TaskStatus.Failed).order_by('-item_id')
        ]

    @classmethod
    def retry_failure(cls, service: ServiceType, item_id: str):
        TaskStatusInfo.objects(service=service, item_id=item_id).update(stage_status=TaskStatus.Queued, poll_counter=0)

class ItemChannel(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    channel = StringField()

    meta = {
        'indexes': [
            {'fields': ['+service', '+item_id', '+channel']},
        ]
    }


class TaskStatusInfo(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    stage = EnumField(TaskStage)
    stage_status = EnumField(TaskStatus)
    poll_counter = IntField(default=0)

    meta = {
        'indexes': [
            {'fields': ['+service', '+item_id']},
            {'fields': ['+stage', '+stage_status']},
            {'fields': ['+stage', '+stage_status', '+poll_counter']},
        ]
    }


class ImageCache(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    url = StringField()
    file = FileField()

    meta = {
        'indexes': [
            {'fields': ['+service', '+item_id', '+url']},
        ]
    }


class AttachmentImageCache(DynamicDocument):
    service = EnumField(ServiceType)
    item_id = StringField()
    image_index = IntField()
    file = FileField()

    meta = {
        'indexes': [
            {'fields': ['+service', '+item_id', '+url']},
        ]
    }


class SecondaryTask(DynamicDocument):
    pull_service = EnumField(ServiceType)
    item_id = StringField()
    post_service = EnumField(ServiceType)
    post_conf = StringField()
    status = EnumField(SecondaryTaskStatus)
    poll_counter = IntField(default=0)
    channel = StringField()

    meta = {
        'indexes': [
            {'fields': ['+pull_service', '+item_id', '+post_service', '+post_conf', '+channel']},
            {'fields': ['+status', '+poll_counter']},
            {'fields': ['+status', '+poll_counter']},
            {'fields': ['+post_service', '+post_conf', '+status']},
            {'fields': ['+pull_service', '+item_id', '+status']},
        ]
    }

    @classmethod
    def add_task(cls, pull_service: ServiceType, item_id: str, post_service: ServiceType, post_conf: str, channel: str):
        cls.objects(
            pull_service=pull_service, item_id=item_id,
            post_service=post_service, post_conf=post_conf,
            channel=channel
        ).update_one(status=SecondaryTaskStatus.Queued, upsert=True)

    @classmethod
    def acquire_task(cls, pull_service: ServiceType, item_id: str, post_service: ServiceType, post_conf: str, channel: str):
        cls.objects(
            pull_service=pull_service, item_id=item_id,
            post_service=post_service, post_conf=post_conf,
            channel=channel
        ).update_one(status=SecondaryTaskStatus.Pending)

    @classmethod
    def release_task(cls, pull_service: ServiceType, item_id: str, post_service: ServiceType, post_conf: str, channel: str):
        cls.objects(
            pull_service=pull_service, item_id=item_id,
            post_service=post_service, post_conf=post_conf,
            channel=channel
        ).update_one(status=SecondaryTaskStatus.Queued)

    @classmethod
    def poll_tasks(cls, limit=1) -> Iterable[Tuple[ServiceType, str, ServiceType, str, str, int]]:
        for it in cls.objects(status=SecondaryTaskStatus.Queued).order_by('poll_counter'):
            it.poll_counter += 1
            it.save()
            yield it.pull_service, it.item_id, it.post_service, it.post_conf, it.channel, it.poll_counter
            limit -= 1
            if limit <= 0:
                break

    @classmethod
    def close_task(cls, pull_service: ServiceType, item_id: str, post_service: ServiceType, post_conf: str, channel: str):
        cls.objects(
            pull_service=pull_service, item_id=item_id,
            post_service=post_service, post_conf=post_conf,
            channel=channel
        ).update_one(status=SecondaryTaskStatus.Finished)

    @classmethod
    def migrate_task(cls, post_service1, post_conf1, post_service2, post_conf2):
        cls.objects(
            post_service=post_service1, post_conf=post_conf1, status=SecondaryTaskStatus.Queued
        ).update(post_service=post_service2, post_conf=post_conf2)

    @classmethod
    def task_done(cls, pull_service: ServiceType, item_id: str):
        return cls.objects(pull_service=pull_service, item_id=item_id, status__in=[SecondaryTaskStatus.Queued, SecondaryTaskStatus.Pending]).count() == 0

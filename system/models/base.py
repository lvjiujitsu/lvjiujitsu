import uuid

from django.db import models


class BaseQuerySet(models.QuerySet):
    def recent_first(self):
        return self.order_by("-created_at")


class BaseManager(models.Manager.from_queryset(BaseQuerySet)):
    pass


class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BaseManager()

    class Meta:
        abstract = True


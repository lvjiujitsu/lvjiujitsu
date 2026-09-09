from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        return self.alive().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    pass


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField("excluído em", null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        base_manager_name = "all_objects"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def delete(self, *args, **kwargs):
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at"])
        return 1, {self._meta.label: 1}

    def hard_delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def restore(self):
        if self.deleted_at is None:
            return False
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        return True

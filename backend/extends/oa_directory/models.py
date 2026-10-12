"""外部编号与本应用部门、用户的对应关系，以及持久化事件收件箱。"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class DirectorySource(models.Model):
    id = models.UUIDField(primary_key=True)
    app_id = models.UUIDField(null=True, unique=True)
    client_id = models.CharField(max_length=128)
    tenant_id = models.PositiveBigIntegerField(null=True)
    issuer = models.CharField(max_length=255)
    replace_organization = models.BooleanField(default=False)
    initialized_at = models.DateTimeField(null=True)
    # 全量导入和事件处理共用条件更新租约，避免同时修改部门树。
    claim_token = models.CharField(max_length=36, blank=True)
    claim_until = models.DateTimeField(null=True)


class DirectoryDepartment(models.Model):
    source = models.ForeignKey(DirectorySource, on_delete=models.CASCADE)
    uid = models.CharField(max_length=80)
    native = models.OneToOneField(settings.DEPT_MODEL, null=True, on_delete=models.SET_NULL)
    parent_uid = models.CharField(max_length=80, blank=True)
    details = models.JSONField(default=dict)
    active = models.BooleanField(default=True)
    version = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['source', 'uid'], name='oa_directory_department_uid')]


class DirectoryMember(models.Model):
    source = models.ForeignKey(DirectorySource, on_delete=models.CASCADE)
    uid = models.CharField(max_length=80)
    native = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    details = models.JSONField(default=dict)
    active = models.BooleanField(default=True)
    disabled_by_directory = models.BooleanField(default=False)
    version = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['source', 'uid'], name='oa_directory_member_uid')]


class DirectoryMembership(models.Model):
    member = models.ForeignKey(DirectoryMember, on_delete=models.CASCADE, related_name='memberships')
    department = models.ForeignKey(DirectoryDepartment, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['member', 'department'], name='oa_directory_membership')]


class DirectoryEvent(models.Model):
    # 接收事件时不等待全量导入事务释放来源记录的外键锁；来源在验签后由应用校验。
    source = models.ForeignKey(DirectorySource, on_delete=models.CASCADE, db_constraint=False)
    event_id = models.UUIDField()
    event_type = models.CharField(max_length=80)
    object_type = models.CharField(max_length=20)
    object_id = models.CharField(max_length=80)
    version = models.PositiveBigIntegerField()
    state = models.CharField(max_length=20, default='pending')
    received_at = models.DateTimeField(default=timezone.now)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['source', 'event_id'], name='oa_directory_event_id')]
        indexes = [models.Index(fields=['state', 'next_attempt_at'], name='oa_directory_event_pending')]

#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：backend 
@File    ：models.py
@Author  ：李小涛
@Date    ：2025/12/29 下午4:09 
@Explain : 文件列表
"""

import os

import uuid
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from application import settings
from apps.system.models import table_prefix
from extends.drf.models import CustomModel


def media_file_name(instance, filename):
    """
    动态生成文件保存路径：
    - 根目录来自 instance.folder（前端传入），默认为 'files'
    - 子目录使用 instance.uuid（必须存在，否则 fallback 到 'unknown'）
    - 文件名原样保留（不修改大小写或扩展名）
    - 安全清理 folder 路径，防止路径穿越
    """
    # 使用 instance.uuid（Django 会自动填充）
    uuid_val = getattr(instance, 'uuid', 'unknown')

    # 处理 folder：默认为 'files'，并清理路径
    raw_folder = (getattr(instance, 'folder', '') or 'files').strip('/')
    # 过滤掉空段和危险段（如 '..'）
    safe_parts = [part for part in raw_folder.split('/') if part and part != '..']
    safe_folder = '/'.join(safe_parts) or 'files'

    # 构造最终路径： <safe_folder>/<uuid>/<original_filename>
    return os.path.join(safe_folder, str(uuid_val), filename)


class FileModel(CustomModel):
    uuid = models.UUIDField(
        verbose_name="唯一标识",
        default=uuid.uuid4,
        editable=False,  # 不在 Admin 或表单中显示/编辑
        unique=True,  # 数据库层面保证唯一
        help_text="系统自动生成的唯一ID，用于文件路径隔离"
    )
    name = models.CharField(verbose_name="文件名称", max_length=200, blank=True)
    folder = models.CharField(verbose_name="存储子目录", max_length=200, blank=True, help_text="如 'user/avatar', 'order/attachments'")
    path = models.FileField(verbose_name="文件地址", upload_to=media_file_name, blank=True, null=True)
    size = models.CharField(verbose_name="文件大小", max_length=36, blank=True)
    md5sum = models.CharField(verbose_name="文件md5", max_length=36, blank=True)
    file_suffix = models.CharField(verbose_name='文件后缀', max_length=36, blank=True)
    # 指向某个模型的类型（比如 user 或 Product）
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联模型类型")
    # 指向该模型的某个实例的主键（比如 user 的 id=5）
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="关联对象ID")

    def get_related_object(self):
        """根据 content_type 和 object_id 获取关联的对象实例"""
        if self.content_type and self.object_id:
            try:
                return self.content_type.get_object_for_this_type(id=self.object_id)
            except ObjectDoesNotExist:
                return None
        return None

    class Meta:
        db_table = table_prefix + "file"
        verbose_name = "附件"
        verbose_name_plural = verbose_name
        db_table_comment = verbose_name
        ordering = ("-id",)


@receiver(pre_delete, sender='system.FileModel')  # 使用字符串引用避免循环导入，或者直接用 FileModel 类
def delete_file_on_database_record_delete(sender, instance, **kwargs):
    """
    在 FileModel 数据库记录删除前，物理删除文件
    """
    if instance.path:
        file_path = instance.path.path
        media_root = os.path.abspath(settings.MEDIA_ROOT)

        # 1. 确认文件存在且是本地文件
        if os.path.isfile(file_path):
            # 安全校验：确保要删除的文件在 MEDIA_ROOT 内，防止误删系统文件
            abs_file_path = os.path.abspath(file_path)
            if abs_file_path.startswith(media_root):
                try:
                    os.remove(abs_file_path)
                    # print(f"成功删除物理文件: {abs_file_path}")
                except OSError as e:
                    # 记录错误日志，不要阻断删除流程
                    print(f"删除物理文件失败 {abs_file_path}: {e}")
            else:
                print(f"跳过删除：文件路径 {abs_file_path} 不在 MEDIA_ROOT ({media_root}) 内")

        # 2. 尝试清理空目录 (可选，保持你原有的逻辑)
        uuid_dir = os.path.dirname(file_path)
        if os.path.isdir(uuid_dir) and uuid_dir.startswith(media_root):
            try:
                # 只有当目录为空时才删除
                if not os.listdir(uuid_dir):
                    os.rmdir(uuid_dir)
                    # print(f"成功删除空目录: {uuid_dir}")
            except OSError:
                pass

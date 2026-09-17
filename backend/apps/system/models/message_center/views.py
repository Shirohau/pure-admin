from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action

from extends.drf.response import success_response
from extends.drf.views_mixins import *
from .filters import MessageCenterFilter, MessageCenterTargetUserFilter
from .models import MessageCenter, MessageCenterTargetUser
from .serializers import (
    MessageCenterSerializer,
    MessageCenterCreateSerializer,
    MessageCenterUpdateSerializer,
    MessageCenterTargetUserSerializer,
    MessageCenterTargetUserCreateSerializer,
    MessageCenterTargetUserUpdateSerializer,
)


@extend_schema(tags=["消息中心"])
class MessageCenterViewSet(CrudViewSet):
    queryset = MessageCenter.objects.all()
    serializer_class = MessageCenterSerializer
    create_serializer_class = MessageCenterCreateSerializer
    update_serializer_class = MessageCenterUpdateSerializer
    filterset_class = MessageCenterFilter

    @extend_schema(summary="获取当前用户消息列表", extensions={'x-function': 'MyMessages'})
    @action(methods=["GET"], detail=False)
    def my_messages(self, request):
        """获取当前用户的消息列表"""
        user = request.user
        self.extra_filter_class = []
        queryset = self.get_queryset().filter(
            target_user=user
        ).distinct().order_by('-create_dt')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(message="获取消息列表成功", data=serializer.data)

    @extend_schema(summary="获取未读消息数量", extensions={'x-function': 'UnreadCount'})
    @action(methods=["GET"], detail=False)
    def unread_count(self, request):
        """获取当前用户未读消息数量"""
        user = request.user
        count = MessageCenterTargetUser.objects.filter(
            users=user,
            is_read=False
        ).count()
        return success_response(message="获取未读消息数量成功", data={"count": count})


@extend_schema(tags=["消息中心目标用户"])
class MessageCenterTargetUserViewSet(CrudViewSet):
    queryset = MessageCenterTargetUser.objects.all()
    serializer_class = MessageCenterTargetUserSerializer
    create_serializer_class = MessageCenterTargetUserCreateSerializer
    update_serializer_class = MessageCenterTargetUserUpdateSerializer
    filterset_class = MessageCenterTargetUserFilter

    @extend_schema(summary="标记消息为已读", extensions={'x-function': 'MarkRead'})
    @action(methods=["POST"], detail=False)
    def mark_read(self, request):
        """标记当前用户的消息为已读"""
        user = request.user
        message_ids = request.data.get('message_ids', None)
        queryset = MessageCenterTargetUser.objects.filter(users=user, is_read=False)
        if message_ids:
            queryset = queryset.filter(messagecenter_id__in=message_ids)
        updated_count = queryset.update(is_read=True)
        return success_response(message=f"已标记 {updated_count} 条消息为已读", data={"count": updated_count})

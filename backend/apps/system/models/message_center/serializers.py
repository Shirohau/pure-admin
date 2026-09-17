from extends.drf.serializers import CustomSerializer
from .models import MessageCenter, MessageCenterTargetUser


class MessageCenterSerializer(CustomSerializer):
    skip_field_permissions = True

    class Meta:
        model = MessageCenter
        fields = '__all__'


class MessageCenterCreateSerializer(CustomSerializer):
    class Meta:
        model = MessageCenter
        fields = '__all__'


class MessageCenterUpdateSerializer(CustomSerializer):
    class Meta:
        model = MessageCenter
        fields = '__all__'


class MessageCenterTargetUserSerializer(CustomSerializer):

    class Meta:
        model = MessageCenterTargetUser
        fields = '__all__'


class MessageCenterTargetUserCreateSerializer(CustomSerializer):
    class Meta:
        model = MessageCenterTargetUser
        fields = '__all__'


class MessageCenterTargetUserUpdateSerializer(CustomSerializer):
    class Meta:
        model = MessageCenterTargetUser
        fields = '__all__'

from rest_framework import serializers
from chats.models import User, Conversation, Message


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = [
            'user_id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'password',
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True} 
        }

    # methods to handle password hashing  
    def create(self, validated_data):
        """Create user with hashed password"""
        return User.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        """Update user and hash password if provided"""
        password = validated_data.pop('password', None)
        
        # Update other fields
        instance = super().update(instance, validated_data)
        
        # Hash and set password if provided
        if password:
            instance.set_password(password)
            instance.save()
        
        return instance


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the Message model."""
    sender = UserSerializer(read_only=True)
    conversation = serializers.PrimaryKeyRelatedField(queryset=Conversation.objects.all())
    message_body = serializers.CharField()

    class Meta:
        model = Message
        fields = [
            'message_id',
            'conversation',
            'sender',
            'message_body',
            'sent_at'
        ]
        read_only_fields = ['message_id', 'sender', 'sent_at']

    def create(self, validated_data):
        """
        Custom create method to set the sender to the authenticated user.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authenticated user is required to send a message.")
        validated_data['sender'] = request.user
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for the Conversation model."""
    participants = UserSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    title = serializers.CharField(max_length=100, allow_blank=True, required=False)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'title',
            'participants',
            'participant_ids',
            'messages',
            'created_at',
            'participant_count'
        ]
        read_only_fields = ['conversation_id', 'participants', 'messages', 'created_at', 'participant_ids']

    def get_participant_count(self, obj):
        return obj.participants.count()

    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        conversation = Conversation.objects.create(**validated_data)
        users = User.objects.filter(user_id__in=participant_ids)
        conversation.participants.set(users)
        return conversation

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from chats.models import Conversation, Message, User
from chats.serializers import ConversationSerializer, MessageSerializer, UserSerializer
from rest_framework.exceptions import PermissionDenied
from chats.permissions import IsParticipantOfConversation

# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
  

    def get_queryset(self):
        """
        Restrict regular users to their own profile; admins can see all users.
        """
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(user_id=self.request.user.user_id)

    def perform_create(self, serializer):
        """
        Ensure only admins can create users.
        """
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can create users.")
        serializer.save()

    def perform_update(self, serializer):
        """
        Allow users to update their own profile; admins can update any user.
        """
        if not self.request.user.is_staff and \
            str(self.request.user.user_id) != str(self.kwargs.get('pk')):
            raise PermissionDenied("You can only update your own profile.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Ensure only admins can delete users.
        """
        if not self.request.user.is_staff:
            raise PermissionDenied("Only admins can delete users.")
        instance.delete()

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, and creating conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [
        IsAuthenticated,
        # IsParticipantOfConversation
    ]

    def get_queryset(self):
        """
        Return conversations where the authenticated user is a participant.
        """
        return Conversation.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """
        Ensure the authenticated user is added to the participants when creating a conversation.
        """
        serializer.save()
        participant_ids = serializer.validated_data.get('participant_ids', [])
        if self.request.user.user_id not in participant_ids:
            serializer.instance.participants.add(self.request.user)
    
    ## Custom () => REVIEW LATER

    def perform_update(self, serializer):
        """
        Update a conversation instance, ensuring the authenticated user remains a participant.
        """
        participant_ids = serializer.validated_data.get('participant_ids', None)
        if participant_ids is not None:
            # Ensure the authenticated user cannot remove themselves from the conversation
            if self.request.user.user_id not in participant_ids:
                serializer.validated_data['participant_ids'].append(self.request.user.user_id)
        serializer.save()

    def perform_destroy(self, instance):
        """
        Delete a conversation, ensuring only participants can delete it.
        """
        # Verify the user is a participant
        if self.request.user not in instance.participants.all():
            raise PermissionDenied(
                "You are not a participant in this conversation."
            )
        instance.delete()


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, and creating messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [
        IsAuthenticated,
        # IsParticipantOfConversation
    ]

    def get_queryset(self):
        """
        Return messages from conversations where the authenticated user is a participant.
        """
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).select_related('sender', 'conversation')

    def perform_create(self, serializer):
        """
        Create a new message, ensuring it belongs to a valid conversation.
        """
        conversation = serializer.validated_data['conversation']
        if not conversation.participants.filter(user_id=self.request.user.user_id).exists():
            raise PermissionDenied(
                "You are not a participant in this conversation."
            )
        serializer.save(sender=self.request.user)

    ## Custom () => REVIEW LATER

    def perform_update(self, serializer):
        """
        Update a message, ensuring only the sender can modify it and the conversation is valid.
        """
        message = self.get_object()
        if message.sender != self.request.user:
            raise PermissionDenied(
                "You can only update your own messages."
        )
        if not message.conversation.participants.filter(
            user_id=self.request.user.user_id
            ).exists():
            raise PermissionDenied(
                "You are no longer a participant in this conversation."
            )
        serializer.save()

    def perform_destroy(self, instance):
        """
        Delete a message, ensuring only the sender can delete it and the conversation is valid.
        """
        if instance.sender != self.request.user:
            raise PermissionDenied(
                "You can only delete your own messages."
            )
        if not instance.conversation.participants.filter(user_id=self.request.user.user_id).exists():
            raise PermissionDenied(
                "You are no longer a participant in this conversation."
            )
        instance.delete()


from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message, User
from .serializers import ConversationSerializer, MessageSerializer, UserSerializer

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
            return Response(
                {"detail": "Only admins can create users."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_update(self, serializer):
        """
        Allow users to update their own profile; admins can update any user.
        """
        if not self.request.user.is_staff and str(self.request.user.user_id) != str(self.kwargs.get('pk')):
            return Response(
                {"detail": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        """
        Ensure only admins can delete users.
        """
        if not self.request.user.is_staff:
            return Response(
                {"detail": "Only admins can delete users."},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()
class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, and creating conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

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


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, and creating messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

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
            return Response(
                {"detail": "You are not a participant in this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save(sender=self.request.user)

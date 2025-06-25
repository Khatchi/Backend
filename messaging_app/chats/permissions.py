from rest_framework import permissions
from chats.models import Conversation

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to:
    - Allow only authenticated users to access the API.
    - Allow only conversation participants to view, send (create),
    - update, and delete messages.
    """
    def has_permission(self, request, view):
        # Ensure the user is authenticated for all API access
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # For Conversation objects: Allow access if user is a participant
        if isinstance(obj, Conversation):
            return obj.participants.filter(user_id=request.user.user_id).exists()
        
        # For Message objects: Restrict view, create, update, and delete to conversation participants
        # if request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        #     return obj.conversation.participants.filter(
        #         user_id=request.user.user_id).exists()

        # () ==> A better implementation...

        # For Message, Check if user is participant of the conversation.
        if hasattr(obj, 'conversation'):
            return obj.conversation.participants.filter(
                user_id=request.user.user_id
            ).exists()
        
        # deny access if neither condition is met
        return False
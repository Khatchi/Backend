from django.urls import path, include
from rest_framework.routers import DefaultRouter
from chats.views import ConversationViewSet, MessageViewSet, UserViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from chats.auth import CustomTokenObtainPairView

# Creates a router and register our endpoints
router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

# Defines url patterns for chats app
urlpatterns = [
    path('', include(router.urls)),

    # Session Auth --> for browsable API
    path('api-auth/', include('rest_framework.urls')),

    # JWT Auth
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
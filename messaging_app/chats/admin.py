from django.contrib import admin

# Register your models here.

# register User model with the admin site
from .models import User, Message, Conversation

admin.site.register(User)
admin.site.register(Message)
admin.site.register(Conversation)
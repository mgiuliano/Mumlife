# api/serializers.py
"""
Mumlife API
Uses the Django REST framework.

"""
import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from mumlife.models import Member, Kid, Friendships, Message

logger = logging.getLogger('api.serializers')


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member


class KidSerializer(serializers.ModelSerializer):
    gender_display = serializers.RelatedField(source='get_gender_display')
    age = serializers.RelatedField(source='age')
    visibility_display = serializers.RelatedField(source='get_visibility_display')
    parents = serializers.RelatedField(source='parents', many=True)

    class Meta:
        model = Kid
        fields = ('id', 'fullname', \
                  'gender', 'gender_display', \
                  'dob', 'age', \
                  'visibility', 'visibility_display', \
                  'parents')


class FriendshipsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendships


class MessageSerializer(serializers.ModelSerializer):
    tags = serializers.RelatedField(source='get_tags')
    visibility_display = serializers.RelatedField(source='get_visibility_display')
    replies = serializers.PrimaryKeyRelatedField(source='replies', many=True, read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'area', 'timestamp', \
                  'name', 'location', 'eventdate', 'eventenddate', \
                  'visibility', 'visibility_display', \
                  'occurrence', 'occurs_until', \
                  'tags', 'body', 'picture', \
                  'is_reply', 'replies')

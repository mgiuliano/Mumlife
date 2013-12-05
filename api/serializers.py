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
    status_display = serializers.RelatedField(source='get_status_display')
    area = serializers.RelatedField(source='area')
    gender_display = serializers.RelatedField(source='get_gender_display')
    age = serializers.RelatedField(source='age')
    location = serializers.RelatedField(source='geocode')
    tags = serializers.RelatedField(source='tags')

    class Meta:
        model = Member
        fields = ('id', 'fullname', 'slug', \
                  'status', 'status_display', \
                  'postcode', 'area', \
                  'gender', 'gender_display', \
                  'dob', 'age', \
                  'picture', 'about', \
                  'interests', 'units', \
                  'spouse', 'friendships', \
                  'location', 'tags')


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
        fields = ('id', 'member', 'area', 'timestamp', \
                  'name', 'location', 'eventdate', \
                  'visibility', 'visibility_display', \
                  'tags', 'body', \
                  'is_reply', 'replies')

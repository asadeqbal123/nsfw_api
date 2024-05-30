from rest_framework import serializers

class ImageURLSerializer(serializers.Serializer):
    url = serializers.URLField()

class VideoURLSerializer(serializers.Serializer):
    url = serializers.URLField()
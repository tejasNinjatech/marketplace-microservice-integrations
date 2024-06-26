from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    start_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"])
    end_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"])
    class Meta:
        model = Event
        fields = '__all__'

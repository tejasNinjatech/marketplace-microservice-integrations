from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.dateparse import parse_datetime
from django_filters.rest_framework import DjangoFilterBackend
from events.models import Event
from events.serializers import EventSerializer
from events.filters import EventFilter

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EventFilter

    def create(self, request, *args :list, **kwargs: dict) -> Response :
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            Event.objects.create(**serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            event_data = serializer.initial_data
            Event.objects.filter(external_id=event_data['external_id']).update(**event_data)
            return Response(event_data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['get'])
    def list_events(self, request) -> Response:
        """
        This method not needed but just written to write date filter by django. 
        Same feature is available in list api by using django-filter
        """
        start_date = parse_datetime(request.query_params.get('starts_at'))
        end_date = parse_datetime(request.query_params.get('ends_at'))
        events = Event.objects.filter(start_date__gte=start_date, end_date__lte=end_date, sell_mode='online')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        This API call with create bulk records 
        API: http://web:8000/api/events/bulk_create/
        Params: [
            {'end_date': '2021-06-30T22:00:00', 'external_id': '291', 'name': 'Camela en concierto', 'sell_mode': 'online', 'start_date': '2021-07-31T21:20:00},
            {}
        ]
        """
        serializer = EventSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        Event.objects.bulk_create([Event(**item) for item in serializer.validated_data])

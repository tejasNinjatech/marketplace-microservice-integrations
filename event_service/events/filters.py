import django_filters
from .models import Event

class EventFilter(django_filters.FilterSet):
    start_date = django_filters.IsoDateTimeFilter(field_name="start_date", lookup_expr='gte')
    end_date = django_filters.IsoDateTimeFilter(field_name="end_date", lookup_expr='lte')

    class Meta:
        model = Event
        fields = ['start_date', 'end_date']


# README.md

## Project Overview

This project integrates a Django backend with Benthos to process and store event data from an external XML API. The system ensures efficient data handling, caching, and rate limiting to prevent API overload.

## Problem Statement

The goal is to efficiently fetch, process, and store event data from an external XML API. The key challenges include handling large volumes of data, ensuring API rate limits are respected, transforming XML data to JSON, avoiding duplicate data processing, and integrating seamlessly with the Django backend.

### Solution Approach

**Efficient Data Fetching**: Use Benthos to periodically fetch data from the external XML API.
**Data Transformation**: Convert the fetched XML data to JSON format using Benthos.
**Rate Limiting**: Implement rate limiting in Benthos to respect the API rate limits.
**Caching**: Use Redis to cache processed data to avoid duplicate processing.
**Data Storage**: Send the processed data to a Django backend for storage in a PostgreSQL database.
**Bulk Processing**: Handle bulk data processing for efficiency.

### Architecture: The architecture consists of the following components

**External XML API**: The source of event data.
**Benthos**: A high-performance data streaming service used to fetch, transform, and process the data.
**Rate Limiting**: Ensures API calls stay within limits.
**XML to JSON Conversion**: Converts XML data to JSON.
**Caching**: Uses Redis to cache event data.
**HTTP Requests**: Sends processed data to the Django API.

### Django Backend

Django is used to create the backend API that will store the event data. The data is received from Benthos after it processes the XML data.

#### Key Django Components

1. **Models**: Define the structure of the event data.
2. **Serializers**: Validate and transform data for storage.
3. **Views**: Handle the HTTP requests.
4. **URLs**: Map URLs to the views.
5. **django-filter**: Filter list APIs by date.

##### Models

```python
from django.db import models

class Event(models.Model):
    external_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    sell_mode = models.CharField(max_length=50)
```

##### Serializers

```python
from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    start_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"])
    end_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"])

    class Meta:
        model = Event
        fields = ['external_id', 'name', 'start_date', 'end_date', 'sell_mode']
```

##### Views

1. **EventViewSet**: ViewSet for handling GET, POST, PUT, PATCH, and DELETE requests for events.
2. **create**: Handles single record creation. If a key is not in the cache, it updates the record.
3. **list_events**: Provides a way to filter events by date.
4. **bulk_create**: Handles bulk creation of event records.

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event
from .serializers import EventSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EventFilter

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            Event.objects.create(**serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            event_data = serializer.data
            Event.objects.filter(external_id=event_data['external_id']).update(**event_data)
            return Response(event_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def list_events(self, request):
        start_date = request.query_params.get('starts_at')
        end_date = request.query_params.get('ends_at')
        events = Event.objects.filter(start_date__gte=start_date, end_date__lte=end_date, sell_mode='online')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = EventSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        Event.objects.bulk_create([Event(**item) for item in serializer.validated_data])
```

### Benthos Configuration

Benthos is used to process XML data, convert it to JSON, check the cache, and send new data to the Django API.

#### Key Components in Benthos

1. **Rate Limiting**: Ensures API calls are within rate limits.
2. **XML to JSON Conversion**: Converts XML data to JSON.
3. **Cache**: Stores processed data to avoid duplicate processing.
4. **HTTP Requests**: Sends processed data to the Django API.
5. **benthos.yaml**: Runs every minute, calls APIs, and processes data.
6. **benthos_bulk.yaml**: Calls XML-based input API and processes a list of events to send to the Django service for saving.

#### Benthos Configuration YML

```yaml
input:
  http_client:
    url: https://provider.code-challenge.feverup.com/api/events
    verb: GET
    retry_period: 5m
    stream:
      enabled: false
  processors:
    - rate_limit:
        resource: rate_limit_resource
pipeline:
  processors:
    - xml:
        operator: to_json
    - bloblang: |
        root = this.eventList.output.base_event.map_each(event -> {
          "external_id": event.get("-base_event_id"),
          "name": event.get("-title"),
          "start_date": event.event.get("-event_start_date"),
          "end_date": event.event.get("-event_end_date"),
          "sell_mode": event.get("-sell_mode")
        })
    - mapping: root = this.filter(event -> event.sell_mode == "online")
    - unarchive:
        format: json_array
    - branch:
        request_map: |
          root = {
            "external_id": this.external_id,
            "name": this.name,
            "start_date": this.start_date,
            "end_date": this.end_date,
            "sell_mode": this.sell_mode
          }
        processors:
          - cache:
              resource: events_cache
              operator: get
              key: ${! this.external_id }
          - bloblang: |
              root = if this == null {
                deleted()
              } else {
                this
              }
    - for_each:
        - http:
            url: http://web:8000/api/events/
            verb: POST
            headers:
              Content-Type: application/json
            retries: 0
        - cache:
            resource: events_cache
            operator: set
            key: ${! this.external_id }
            ttl: 1h
cache_resources:
  - label: events_cache
    redis:
      url: redis://redis:6379
rate_limit_resources:
  - label: rate_limit_resource
    local:
      count: 1
      interval: 1m
```

### Running the Services

#### Using Docker Setup

```sh
docker-compose up --build web db redis
```

```sh
docker-compose exec web python manage.py makemigrations
```

```sh
docker-compose exec web python manage.py migrate
```

```sh
docker-compose up --build data_loader_service
```

**Migration Note**: Ensure the db and web services are running when performing migrations.

#### Running Django without Docker

**Postgres and Redis**: Install Postgres and Redis and update Django settings accordingly.

1. **Install Dependencies**: Ensure you have Python and Django installed.

    ```sh
    pip install -r requirements.txt
    ```

2. **Migrate the Database**:

    ```sh
    python manage.py migrate
    ```

3. **Run the Django Server**:

    ```sh
    python manage.py runserver
    ```

#### Running Benthos

1. **Install Benthos**: Follow instructions on [Benthos official site](https://www.benthos.dev/docs/guides/getting_started).

2. **Run Benthos**:
  
    ```sh
    benthos -c benthos.yaml
    ```

3. **Run Benthos Bulk if Needed**:
  
    ```sh
    benthos -c benthos_bulk.yaml
    ```

### Redis

Using Redis for caching event IDs in Benthos to avoid duplicate API calls.

### API Endpoints

- **Django API Endpoint**: `http://localhost:8000/api/events/`
- **Django Bulk Create API Endpoint**: `http://localhost:8000/api/events/bulk_create/`
- **Benthos Input Endpoint**: `https://provider.code-challenge.feverup.com/api/events`
- **Swagger API Endpoint**: `http://127.0.0.1:8000/swagger/`

### Why Use Benthos with API

Using Benthos with the API provides several advantages:

1. **Efficient Data Processing**: Benthos can handle large volumes of data efficiently.
2. **Rate Limiting**: Ensures compliance with API rate limits.
3. **Data Transformation**: Converts XML to JSON and formats the data as needed.
4. **Caching**: Prevents duplicate data processing and reduces load on the backend.
5. **Integration**: Seamlessly integrates with various data sources and sinks, making it versatile for different data pipelines.

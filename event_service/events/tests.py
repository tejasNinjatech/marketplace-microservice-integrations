from django.test import TestCase
from .models import Event

class EventServiceTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            external_id="1",
            name="Test Event",
            start_date="2022-01-01T00:00:00Z",
            end_date="2022-01-02T00:00:00Z",
            sell_mode="online"
        )

    def test_event_creation(self):
        event = Event.objects.get(external_id="1")
        self.assertEqual(event.name, "Test Event")

    def test_list_events(self):
        response = self.client.get('/api/events/', {'starts_at': '2022-01-01T00:00:00Z', 'ends_at': '2022-01-02T00:00:00Z'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

if __name__ == '__main__':
    unittest.main()
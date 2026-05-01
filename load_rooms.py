import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vr_office.settings')
django.setup()

from navigator.models import Room

# Load rooms from JSON
with open('data/rooms_84.json', 'r') as f:
    rooms_data = json.load(f)

Room.objects.all().delete()  # Clear existing

for i, room in enumerate(rooms_data):
    name = room['name']
    side = room.get('side', 'downstairs')
    location_type = 'upstairs' if side in ['top', 'up'] else 'downstairs'
    Room.objects.create(
        name=name,
        floor=0,  # Assuming single floor
        order=i,
        location_type=location_type
    )

print(f"Loaded {len(rooms_data)} rooms")
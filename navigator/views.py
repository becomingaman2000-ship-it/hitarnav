from django.shortcuts import render
from .models import Room
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.

def ar_indoor_navigator(request):
    return render(request, 'navigator/ar-indoor-navigator.html')

def analyze_rooms(request):
    rooms = Room.objects.order_by('floor', 'order')
    return render(request, 'navigator/ar-indoor-navigator.html', {'rooms': rooms})

def room_map(request):
    upstairs_rooms = Room.objects.filter(location_type='upstairs').order_by('floor', 'order')
    downstairs_rooms = Room.objects.filter(location_type='downstairs').order_by('floor', 'order')
    return render(request, 'navigator/room_map.html', {
        'upstairs_rooms': upstairs_rooms,
        'downstairs_rooms': downstairs_rooms
    })


@csrf_exempt
def upload_rooms(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    # Accept either {"rooms": [...]} or a direct list
    rooms_list = data.get('rooms') if isinstance(data, dict) and 'rooms' in data else data
    if not isinstance(rooms_list, list):
        return JsonResponse({'error': 'expected list of rooms'}, status=400)

    # Replace existing rooms with new import
    Room.objects.all().delete()
    objs = []
    for i, r in enumerate(rooms_list):
        # r may be string or object
        if isinstance(r, str):
            name = r
            location_type = 'downstairs'
        elif isinstance(r, dict):
            name = r.get('label') or r.get('name') or str(r)
            side = r.get('side') or r.get('location') or ''
            location_type = 'upstairs' if side == 'top' or side == 'up' else 'downstairs'
        else:
            name = str(r)
            location_type = 'downstairs'

        objs.append(Room(name=name, floor=0, order=i, location_type=location_type))

    Room.objects.bulk_create(objs)
    return JsonResponse({'created': len(objs)})


@csrf_exempt
def clear_rooms(request):
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'POST or DELETE required'}, status=405)
    count, _ = Room.objects.all().delete()
    return JsonResponse({'deleted': count})


def rooms_count(request):
    n = Room.objects.count()
    return JsonResponse({'count': n})


def get_rooms(request):
    # Return list of room names in order
    qs = Room.objects.order_by('order')
    rooms = [r.name for r in qs]
    return JsonResponse({'rooms': rooms})

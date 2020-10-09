from django.shortcuts import render
from django.conf import settings

def demo(request):
    alt_api = request.GET.get('url', None)
    if alt_api:
        API = alt_api
    else:
        API = settings.SITE_URL

    context = {
        'API': API
    }
    return render(request, 'demo.html', context)
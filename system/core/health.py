from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

CHROME_DEVTOOLS_PROBE_PATH = ".well-known/appspecific/com.chrome.devtools.json"


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def chrome_devtools_probe(request):
    return HttpResponse(status=204, content_type="application/json")

from django.contrib import admin
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE"])
def echo_view(request):
    return Response({"method": request.method, "path": request.path})


urlpatterns = [
    path("admin/drf-idem/", include("drf_idem.urls")),
    path("admin/", admin.site.urls),
    path("api/test/", echo_view),
    path("api/payments/", echo_view),
    path("api/orders/", echo_view),
]

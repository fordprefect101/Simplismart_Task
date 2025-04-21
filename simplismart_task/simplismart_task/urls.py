from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="SimpliSmart API",
        default_version='v1',
        description="API for SimpliSmart Task Management",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@simplismart.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def api_root(request):
    return {
        "message": "Welcome to SimpliSmart API",
        "endpoints": {
            "users": "/api/users/",
            "login": "/api/login/",
            "clusters": "/api/clusters/",
            "resource-usage": "/api/resource-usage/",
            "documentation": "/api/docs/",
        }
    }

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

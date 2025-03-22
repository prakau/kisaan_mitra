from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/crops/', include('crops.urls')),
    path('api/v1/weather/', include('weather.urls')),
    path('api/v1/pest-detection/', include('pest_detection.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/chatbot/', include('chatbot.urls')),
    path('api/v1/ai/', include('ai_integration.urls')),
    path('docs/', include_docs_urls(title='Kisaan Mitra API')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site
admin.site.site_header = 'Kisaan Mitra Administration'
admin.site.site_title = 'Kisaan Mitra Admin Portal'
admin.site.index_title = 'Welcome to Kisaan Mitra Admin Portal'

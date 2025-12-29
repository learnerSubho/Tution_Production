from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
import os
from . import views

def firebase_sw(request):
    file_path = os.path.join(settings.BASE_DIR, 'firebase-messaging-sw.js')
    return FileResponse(
        open(file_path, 'rb'),
        content_type='application/javascript'
    )

urlpatterns = [
    path('firebase-messaging-sw.js', firebase_sw),  # 🔥 MUST be first
    path('admin/', admin.site.urls),
    path('teacher/', include('TeacherPanel.urls')),
    path('student/', include('StudentPanel.urls')),
    path('',views.home,name='home'),
    path('technical_support/',views.technical_support,name='technical_support'),
    path('faq/',views.faq,name='faq'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )

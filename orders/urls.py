from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # صفحة تسجيل الدخول هي الصفحة الرئيسية الآن
    path('', views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("signup", views.signup_view, name="signup"),
    path('scan_qr/', views.scan_qr, name='scan_qr'),
    path('attendance/', views.attendance_view, name='attendance'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from . import views

urlpatterns = [
    # Doktor listeleme ve detay
    path('', views.doctor_list, name='doctor_list'),
    path('<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    
    # Doktor program yönetimi
    path('program/', views.doctor_schedule, name='doctor_schedule'),
    path('program/ekle/', views.add_doctor_availability, name='add_doctor_availability'),
    path('program/<int:availability_id>/duzenle/', views.edit_doctor_availability, name='edit_doctor_availability'),
    path('program/<int:availability_id>/sil/', views.delete_doctor_availability, name='delete_doctor_availability'),
    
    # İzin yönetimi
    path('izin/', views.doctor_leave_list, name='doctor_leave_list'),
    path('izin/ekle/', views.add_doctor_leave, name='add_doctor_leave'),
    path('izin/<int:leave_id>/duzenle/', views.edit_doctor_leave, name='edit_doctor_leave'),
    path('izin/<int:leave_id>/sil/', views.delete_doctor_leave, name='delete_doctor_leave'),
    
    # Performans
    path('performans/', views.doctor_performance, name='doctor_performance'),
] 
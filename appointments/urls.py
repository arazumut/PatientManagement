from django.urls import path
from . import views

urlpatterns = [
    # Randevu listeleme ve yönetim
    path('', views.appointment_list, name='appointment_list'),
    path('ekle/', views.add_appointment, name='add_appointment'),
    path('<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('<int:appointment_id>/duzenle/', views.edit_appointment, name='edit_appointment'),
    path('<int:appointment_id>/iptal/', views.cancel_appointment, name='cancel_appointment'),
    path('<int:appointment_id>/onayla/', views.confirm_appointment, name='confirm_appointment'),
    path('<int:appointment_id>/tamamla/', views.complete_appointment, name='complete_appointment'),
    
    # Doktor programı yönetimi
    path('program/', views.schedule_list, name='schedule_list'),
    path('program/ekle/', views.add_schedule, name='add_schedule'),
    path('program/<int:schedule_id>/duzenle/', views.edit_schedule, name='edit_schedule'),
    path('program/<int:schedule_id>/sil/', views.delete_schedule, name='delete_schedule'),
    
    # Randevu arama ve filtreleme
    path('ara/', views.search_appointments, name='search_appointments'),
    
    # Hasta için randevu işlemleri
    path('hastam/', views.patient_appointments, name='patient_appointments'),
    path('doktor/<int:doctor_id>/musait-zamanlar/', views.doctor_available_slots, name='doctor_available_slots'),
    
    # Takvim görünümü
    path('takvim/', views.appointment_calendar, name='appointment_calendar'),
] 
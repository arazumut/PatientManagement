from django.urls import path
from . import views

urlpatterns = [
    # Hasta listeleme ve detay sayfaları
    path('', views.patient_list, name='patient_list'),
    path('ekle/', views.add_patient, name='add_patient'),
    path('<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<int:patient_id>/duzenle/', views.edit_patient, name='edit_patient'),
    
    # Tıbbi kayıtlar
    path('<int:patient_id>/kayit/ekle/', views.add_medical_record, name='add_medical_record'),
    path('kayit/<int:record_id>/', views.medical_record_detail, name='medical_record_detail'),
    path('kayit/<int:record_id>/duzenle/', views.edit_medical_record, name='edit_medical_record'),
    
    # Reçete yönetimi
    path('kayit/<int:record_id>/recete/ekle/', views.add_prescription, name='add_prescription'),
    path('recete/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('recete/<int:prescription_id>/ilac/ekle/', views.add_medication, name='add_medication'),
    
    # Hasta notları
    path('<int:patient_id>/not/ekle/', views.add_patient_note, name='add_patient_note'),
    path('not/<int:note_id>/duzenle/', views.edit_patient_note, name='edit_patient_note'),
    path('not/<int:note_id>/sil/', views.delete_patient_note, name='delete_patient_note'),
] 
from django import forms
from .models import MedicalRecord, Prescription, Medication, PatientNote
from accounts.models import PatientProfile, DoctorProfile
import random
import string

class PatientProfileForm(forms.ModelForm):
    """Hasta profil formu"""
    class Meta:
        model = PatientProfile
        fields = ['tc_number', 'date_of_birth', 'blood_group', 'allergies', 
                  'chronic_diseases', 'emergency_contact_name', 'emergency_contact_phone']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'allergies': forms.Textarea(attrs={'rows': 3}),
            'chronic_diseases': forms.Textarea(attrs={'rows': 3}),
        }

class MedicalRecordForm(forms.ModelForm):
    """Tıbbi kayıt formu"""
    class Meta:
        model = MedicalRecord
        fields = ['doctor', 'diagnosis', 'diagnosis_details', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'diagnosis_details': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Admin olmayan kullanıcılar için doktor seçimi filtrelenmeli
        if 'instance' in kwargs and kwargs['instance']:
            # Düzenlemede sadece kayıt sahibi doktor seçili olmalı
            self.fields['doctor'].queryset = DoctorProfile.objects.filter(id=kwargs['instance'].doctor.id)
            self.fields['doctor'].widget.attrs['disabled'] = 'disabled'
        else:
            self.fields['doctor'].queryset = DoctorProfile.objects.all()

class PrescriptionForm(forms.ModelForm):
    """Reçete formu"""
    class Meta:
        model = Prescription
        fields = ['prescription_number', 'date_prescribed']
        widgets = {
            'date_prescribed': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Otomatik reçete numarası oluştur
        if not self.initial.get('prescription_number'):
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.initial['prescription_number'] = f"R{random_chars}"

class MedicationForm(forms.ModelForm):
    """İlaç formu"""
    class Meta:
        model = Medication
        fields = ['name', 'dosage', 'frequency', 'duration', 'instructions']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3}),
        }

class PatientNoteForm(forms.ModelForm):
    """Hasta notu formu"""
    class Meta:
        model = PatientNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 4}),
        } 
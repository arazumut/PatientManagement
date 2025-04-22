from django import forms
from .models import Appointment, Schedule, Notification
from accounts.models import DoctorProfile, PatientProfile
from django.utils import timezone
from datetime import timedelta

class ScheduleForm(forms.ModelForm):
    """Doktor programı oluşturma formu"""
    class Meta:
        model = Schedule
        fields = ['doctor', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.profile.user_type == 'doctor':
            # Doktor kendisi için program oluşturuyorsa, doktor seçimini kısıtla
            doctor_profile = DoctorProfile.objects.get(user_profile=user.profile)
            self.fields['doctor'].queryset = DoctorProfile.objects.filter(id=doctor_profile.id)
            self.fields['doctor'].widget.attrs['disabled'] = 'disabled'
            self.fields['doctor'].initial = doctor_profile
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')
        doctor = cleaned_data.get('doctor')
        
        # Başlangıç zamanı bitiş zamanından önce olmalıdır
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Başlangıç zamanı bitiş zamanından önce olmalıdır.")
        
        # Seçilen tarih bugün veya sonrası olmalıdır
        if date and date < timezone.now().date():
            raise forms.ValidationError("Geçmiş bir tarih seçemezsiniz.")
        
        # Çakışan program kontrolü
        if doctor and date and start_time and end_time:
            existing_schedules = Schedule.objects.filter(
                doctor=doctor,
                date=date
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            for schedule in existing_schedules:
                # Yeni program mevcut programla çakışıyor mu kontrol et
                if (start_time < schedule.end_time and end_time > schedule.start_time):
                    raise forms.ValidationError(
                        f"Bu zaman dilimi başka bir programla çakışıyor: "
                        f"{schedule.start_time.strftime('%H:%M')} - {schedule.end_time.strftime('%H:%M')}"
                    )
        
        return cleaned_data

class AppointmentForm(forms.ModelForm):
    """Randevu oluşturma formu"""
    doctor = forms.ModelChoiceField(queryset=DoctorProfile.objects.all(), label='Doktor')
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Tarih')
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'reason', 'notes']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Kullanıcı hasta ise, patient değerini otomatik ayarla
        if user and user.profile.user_type == 'patient':
            self.patient = PatientProfile.objects.get(user_profile=user.profile)
        
        # Eğer düzenleme ise ve randevu onaylanmışsa, doktor ve tarih değiştirilemez
        if self.instance.pk and self.instance.status == 'confirmed':
            self.fields['doctor'].widget.attrs['disabled'] = 'disabled'
            self.fields['date'].widget.attrs['disabled'] = 'disabled'
        
        # Ayarlanabilir alanları göster
        self.available_slots = []
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        date = cleaned_data.get('date')
        
        # Seçilen tarih bugün veya sonrası olmalıdır
        if date and date < timezone.now().date():
            raise forms.ValidationError("Geçmiş bir tarih seçemezsiniz.")
        
        return cleaned_data

class AppointmentSlotForm(forms.Form):
    """Randevu zaman dilimi seçme formu"""
    slot = forms.ChoiceField(choices=[], label='Randevu Saati')
    
    def __init__(self, *args, **kwargs):
        available_slots = kwargs.pop('available_slots', [])
        super().__init__(*args, **kwargs)
        
        # Mevcut zaman dilimlerini seçenek olarak ekle
        slot_choices = [(f"{slot['start']}|{slot['end']}", f"{slot['start']} - {slot['end']}") for slot in available_slots]
        self.fields['slot'].choices = slot_choices
        
        if not slot_choices:
            self.fields['slot'].widget.attrs['disabled'] = 'disabled'
            self.fields['slot'].help_text = "Seçilen gün ve doktor için uygun randevu saati bulunmamaktadır."

class AppointmentSearchForm(forms.Form):
    """Randevu arama formu"""
    APPOINTMENT_STATUS = (
        ('', 'Tümü'),
        ('pending', 'Beklemede'),
        ('confirmed', 'Onaylandı'),
        ('cancelled', 'İptal Edildi'),
        ('completed', 'Tamamlandı'),
    )
    
    doctor = forms.ModelChoiceField(
        queryset=DoctorProfile.objects.all(),
        required=False,
        label='Doktor',
        empty_label='Tüm Doktorlar'
    )
    patient = forms.CharField(
        required=False,
        label='Hasta Adı/T.C.',
        widget=forms.TextInput(attrs={'placeholder': 'Hasta adı veya T.C. no'})
    )
    date_from = forms.DateField(
        required=False,
        label='Başlangıç Tarihi',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label='Bitiş Tarihi',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    status = forms.ChoiceField(
        choices=APPOINTMENT_STATUS,
        required=False,
        label='Durum'
    )

class NotificationForm(forms.ModelForm):
    """Bildirim formu"""
    class Meta:
        model = Notification
        fields = ['notification_type'] 
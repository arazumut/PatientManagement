from django import forms
from .models import DoctorAvailability, DoctorLeave
from accounts.models import DoctorProfile
from django.utils import timezone

class DoctorAvailabilityForm(forms.ModelForm):
    """Doktor müsaitlik formu"""
    class Meta:
        model = DoctorAvailability
        fields = ['doctor', 'day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
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
        
        # Başlangıç zamanı bitiş zamanından önce olmalıdır
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Başlangıç zamanı bitiş zamanından önce olmalıdır.")
        
        return cleaned_data

class DoctorLeaveForm(forms.ModelForm):
    """Doktor izin formu"""
    class Meta:
        model = DoctorLeave
        fields = ['doctor', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.profile.user_type == 'doctor':
            # Doktor kendisi için izin oluşturuyorsa, doktor seçimini kısıtla
            doctor_profile = DoctorProfile.objects.get(user_profile=user.profile)
            self.fields['doctor'].queryset = DoctorProfile.objects.filter(id=doctor_profile.id)
            self.fields['doctor'].widget.attrs['disabled'] = 'disabled'
            self.fields['doctor'].initial = doctor_profile
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Başlangıç tarihi bitiş tarihinden önce olmalıdır
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Başlangıç tarihi bitiş tarihinden önce olmalıdır.")
        
        # Başlangıç tarihi bugün veya sonrası olmalıdır
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError("Geçmiş bir tarih için izin eklenemez.")
        
        return cleaned_data

class DoctorFilterForm(forms.Form):
    """Doktor arama ve filtreleme formu"""
    SPECIALTY_CHOICES = [('', 'Tüm Uzmanlıklar')] + list(DoctorProfile.SPECIALTIES)
    
    name = forms.CharField(
        label='Doktor Adı',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Doktor adı veya soyadı'})
    )
    specialty = forms.ChoiceField(
        label='Uzmanlık Alanı',
        choices=SPECIALTY_CHOICES,
        required=False
    ) 
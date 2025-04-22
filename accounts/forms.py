from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, DoctorProfile, PatientProfile
from django.core.exceptions import ValidationError
import re

class UserRegistrationForm(UserCreationForm):
    """Kullanıcı kayıt formu"""
    USER_TYPE_CHOICES = (
        ('doctor', 'Doktor'),
        ('patient', 'Hasta'),
    )
    
    email = forms.EmailField(required=True, label='E-posta')
    first_name = forms.CharField(required=True, label='Ad')
    last_name = forms.CharField(required=True, label='Soyad')
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, label='Kullanıcı Tipi')
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'user_type']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return email

class UserProfileForm(forms.ModelForm):
    """Kullanıcı profil düzenleme formu"""
    first_name = forms.CharField(required=True, label='Ad')
    last_name = forms.CharField(required=True, label='Soyad')
    email = forms.EmailField(required=True, label='E-posta')
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'profile_picture']
        labels = {
            'phone_number': 'Telefon Numarası',
            'address': 'Adres',
            'profile_picture': 'Profil Fotoğrafı',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']
        profile.user.email = self.cleaned_data['email']
        profile.user.save()
        
        if commit:
            profile.save()
        
        return profile

class DoctorProfileForm(forms.ModelForm):
    """Doktor profil bilgileri formu"""
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'license_number', 'about', 'experience_years']
        labels = {
            'specialty': 'Uzmanlık Alanı',
            'license_number': 'Lisans/Diploma Numarası',
            'about': 'Hakkında',
            'experience_years': 'Deneyim (Yıl)',
        }

class PatientProfileForm(forms.ModelForm):
    """Hasta profil bilgileri formu"""
    class Meta:
        model = PatientProfile
        fields = ['tc_number', 'date_of_birth', 'blood_group', 'allergies', 
                  'chronic_diseases', 'emergency_contact_name', 'emergency_contact_phone']
        labels = {
            'tc_number': 'T.C. Kimlik Numarası',
            'date_of_birth': 'Doğum Tarihi',
            'blood_group': 'Kan Grubu',
            'allergies': 'Alerjiler',
            'chronic_diseases': 'Kronik Hastalıklar',
            'emergency_contact_name': 'Acil Durum Kişisi',
            'emergency_contact_phone': 'Acil Durum Telefonu',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_tc_number(self):
        tc_number = self.cleaned_data.get('tc_number')
        
        # TC Kimlik Numarası doğrulama
        if not tc_number.isdigit():
            raise ValidationError("T.C. Kimlik Numarası sadece rakamlardan oluşmalıdır.")
        
        if len(tc_number) != 11:
            raise ValidationError("T.C. Kimlik Numarası 11 haneli olmalıdır.")
        
        if tc_number[0] == '0':
            raise ValidationError("T.C. Kimlik Numarası 0 ile başlayamaz.")
        
        # Temel doğrulama algoritması (basitleştirilmiş)
        if sum(int(tc_number[i]) for i in range(0, 10, 2)) * 7 - sum(int(tc_number[i]) for i in range(1, 9, 2)) % 10 != int(tc_number[9]):
            raise ValidationError("Geçersiz T.C. Kimlik Numarası.")
        
        # Mevcut instance dışında aynı TC numarasına sahip başka kayıt var mı kontrolü
        if PatientProfile.objects.exclude(pk=getattr(self.instance, 'pk', None)).filter(tc_number=tc_number).exists():
            raise ValidationError("Bu T.C. Kimlik Numarası zaten kayıtlı.")
        
        return tc_number 
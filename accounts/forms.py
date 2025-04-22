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
    
    first_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=254, 
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES, 
        required=True, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'user_type')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Adding form control classes to default fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Bu e-posta adresi zaten kullanılıyor.")
        return email

class UserProfileForm(forms.ModelForm):
    """Kullanıcı profil bilgileri formu"""
    
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Doğum Tarihi'
    )
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'birth_date', 'profile_picture', 'address']
        labels = {
            'phone': 'Telefon',
            'profile_picture': 'Profil Resmi',
            'address': 'Adres',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

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
        widgets = {
            'specialty': forms.Select(attrs={'class': 'form-select'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

class PatientProfileForm(forms.ModelForm):
    """Hasta profil bilgileri formu"""
    GENDER_CHOICES = (
        ('male', 'Erkek'),
        ('female', 'Kadın'),
        ('other', 'Diğer'),
    )
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cinsiyet'
    )
    
    class Meta:
        model = PatientProfile
        fields = ['tc_number', 'date_of_birth', 'gender', 'blood_group', 'allergies', 'chronic_diseases', 'emergency_contact_name', 'emergency_contact_phone']
        labels = {
            'tc_number': 'T.C. Kimlik No',
            'date_of_birth': 'Doğum Tarihi',
            'blood_group': 'Kan Grubu',
            'allergies': 'Alerjiler',
            'chronic_diseases': 'Kronik Hastalıklar',
            'emergency_contact_name': 'Acil Durumda İrtibat Kişisi',
            'emergency_contact_phone': 'Acil Durumda İrtibat Telefonu',
        }
        widgets = {
            'tc_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'chronic_diseases': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
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
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('doctor', 'Doktor'),
        ('patient', 'Hasta'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='patient')
    profile_picture = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_user_type_display()}"

# Doktor profili için ek bilgiler
class DoctorProfile(models.Model):
    SPECIALTIES = (
        ('cardiology', 'Kardiyoloji'),
        ('dermatology', 'Dermatoloji'),
        ('endocrinology', 'Endokrinoloji'),
        ('gastroenterology', 'Gastroenteroloji'),
        ('neurology', 'Nöroloji'),
        ('oncology', 'Onkoloji'),
        ('orthopedics', 'Ortopedi'),
        ('pediatrics', 'Pediatri'),
        ('psychiatry', 'Psikiyatri'),
        ('urology', 'Üroloji'),
        ('general', 'Genel Cerrahi'),
        ('internal', 'İç Hastalıkları'),
        ('other', 'Diğer'),
    )
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=20, choices=SPECIALTIES)
    license_number = models.CharField(max_length=20)
    about = models.TextField(blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Dr. {self.user_profile.user.get_full_name()} - {self.get_specialty_display()}"

# Hasta profili için ek bilgiler
class PatientProfile(models.Model):
    BLOOD_GROUPS = (
        ('A+', 'A Rh+'),
        ('A-', 'A Rh-'),
        ('B+', 'B Rh+'),
        ('B-', 'B Rh-'),
        ('AB+', 'AB Rh+'),
        ('AB-', 'AB Rh-'),
        ('0+', '0 Rh+'),
        ('0-', '0 Rh-'),
    )
    
    GENDER_CHOICES = (
        ('male', 'Erkek'),
        ('female', 'Kadın'),
        ('other', 'Diğer'),
    )
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='patient_profile')
    tc_number = models.CharField(max_length=11, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='other')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    chronic_diseases = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user_profile.user.get_full_name()} - TC: {self.tc_number}"

# Sinyaller: Otomatik profil oluşturma
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

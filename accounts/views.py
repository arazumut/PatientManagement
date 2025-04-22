from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth import logout
from .models import UserProfile, DoctorProfile, PatientProfile
from .forms import UserRegistrationForm, UserProfileForm, DoctorProfileForm, PatientProfileForm
from appointments.models import Appointment
from doctors.models import DoctorAvailability, DoctorPerformance
from patients.models import MedicalRecord
from django.utils import timezone
from django.http import Http404, HttpResponseForbidden

@login_required
def dashboard(request):
    """Kullanıcı rolüne göre dashboard sayfasını gösterir"""
    try:
        user_profile = request.user.profile
        
        # Ortak istatistikler
        today_appointments = []
        all_appointments = []
        
        if user_profile.user_type == 'admin':
            # Admin dashboardu
            total_patients = PatientProfile.objects.count()
            total_doctors = DoctorProfile.objects.count()
            all_appointments = Appointment.objects.all()
            today_appointments = Appointment.objects.filter(
                appointment_date=timezone.now().date()
            )
            
            # Bu ay yapılan toplam randevu sayısı
            current_month = timezone.now().month
            current_year = timezone.now().year
            monthly_appointments = Appointment.objects.filter(
                appointment_date__month=current_month,
                appointment_date__year=current_year
            ).count()
            
            # Son eklenen hastalar
            recent_patients = PatientProfile.objects.order_by('-user_profile__user__date_joined')[:5]
            
            context = {
                'user_profile': user_profile,
                'total_patients': total_patients,
                'total_doctors': total_doctors,
                'today_appointments': today_appointments,
                'monthly_appointments': monthly_appointments,
                'recent_patients': recent_patients,
                'all_appointments': all_appointments,
            }
            
            return render(request, 'accounts/dashboard_admin.html', context)
        
        elif user_profile.user_type == 'doctor':
            # Doktor dashboardu
            try:
                doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
                all_appointments = Appointment.objects.filter(doctor=doctor_profile)
                today_appointments = all_appointments.filter(
                    appointment_date=timezone.now().date()
                )
                
                # Toplam hasta sayısı (bu doktora gelmiş benzersiz hastalar)
                total_patients = PatientProfile.objects.filter(
                    appointments__doctor=doctor_profile
                ).distinct().count()
                
                # Tamamlanan ve iptal edilen randevular
                completed_appointments = all_appointments.filter(status='completed').count()
                cancelled_appointments = all_appointments.filter(status='cancelled').count()
                
                # Doktorun programı - bugün ve gelecek 6 gün
                availability = DoctorAvailability.objects.filter(doctor=doctor_profile)
                
                # Yaklaşan randevular
                upcoming_appointments = all_appointments.filter(
                    appointment_date__gte=timezone.now().date(),
                    status__in=['pending', 'confirmed']
                ).order_by('appointment_date', 'start_time')[:5]
                
                context = {
                    'user_profile': user_profile,
                    'doctor_profile': doctor_profile,
                    'today_appointments': today_appointments,
                    'total_patients': total_patients,
                    'completed_appointments': completed_appointments,
                    'cancelled_appointments': cancelled_appointments,
                    'availability': availability,
                    'upcoming_appointments': upcoming_appointments,
                    'all_appointments': all_appointments,
                }
                
                return render(request, 'accounts/dashboard_doctor.html', context)
            except DoctorProfile.DoesNotExist:
                messages.error(request, "Doktor profili bulunamadı. Lütfen yönetici ile iletişime geçin.")
                return render(request, 'accounts/dashboard.html', {'user_profile': user_profile})
        
        elif user_profile.user_type == 'patient':
            # Hasta dashboardu
            try:
                patient_profile = PatientProfile.objects.get(user_profile=user_profile)
                all_appointments = Appointment.objects.filter(patient=patient_profile)
                upcoming_appointments = all_appointments.filter(
                    appointment_date__gte=timezone.now().date(),
                    status__in=['pending', 'confirmed']
                ).order_by('appointment_date', 'start_time')
                
                # Geçmiş randevular
                past_appointments = all_appointments.filter(
                    appointment_date__lt=timezone.now().date()
                ).order_by('-appointment_date', '-start_time')[:5]
                
                # Tıbbi kayıtlar
                medical_records = MedicalRecord.objects.filter(patient=patient_profile).order_by('-date')[:5]
                
                # Bugünkü randevular
                today_appointments = all_appointments.filter(
                    appointment_date=timezone.now().date()
                )
                
                context = {
                    'user_profile': user_profile,
                    'patient_profile': patient_profile,
                    'upcoming_appointments': upcoming_appointments,
                    'past_appointments': past_appointments,
                    'medical_records': medical_records,
                    'today_appointments': today_appointments,
                    'all_appointments': all_appointments,
                }
                
                return render(request, 'accounts/dashboard_patient.html', context)
            except PatientProfile.DoesNotExist:
                messages.error(request, "Hasta profili bulunamadı. Lütfen yönetici ile iletişime geçin.")
                return render(request, 'accounts/dashboard.html', {'user_profile': user_profile})
        
        # Varsayılan dashboard
        messages.info(request, f"Hoş geldiniz {request.user.get_full_name() or request.user.username}!")
        return render(request, 'accounts/dashboard.html', {'user_profile': user_profile})
    except Exception as e:
        messages.error(request, f"Bir hata oluştu: {str(e)}")
        return render(request, 'accounts/dashboard.html', {'user_profile': request.user.profile if hasattr(request.user, 'profile') else None})

def register(request):
    """Yeni kullanıcı kaydı için view"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Kullanıcıyı kaydet
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password1'])
            new_user.save()
            
            # Kullanıcı profili oluştur (UserProfile sinyallerle otomatik oluşturulur)
            user_profile = UserProfile.objects.get(user=new_user)
            user_profile.user_type = user_form.cleaned_data['user_type']
            user_profile.save()
            
            messages.success(request, "Hesabınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.")
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': user_form})

@login_required
def profile(request):
    """Kullanıcı profil sayfası"""
    user_profile = request.user.profile
    
    if user_profile.user_type == 'doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        except DoctorProfile.DoesNotExist:
            doctor_profile = None
            messages.warning(request, "Doktor profiliniz henüz oluşturulmamış. Lütfen doktor bilgilerinizi ekleyin.")
            return redirect('create_doctor_profile')
        
        appointments = Appointment.objects.filter(doctor=doctor_profile)
        
        context = {
            'user_profile': user_profile,
            'doctor_profile': doctor_profile,
            'appointments': appointments,
        }
        return render(request, 'accounts/profile_doctor.html', context)
    
    elif user_profile.user_type == 'patient':
        try:
            patient_profile = PatientProfile.objects.get(user_profile=user_profile)
        except PatientProfile.DoesNotExist:
            patient_profile = None
        
        appointments = Appointment.objects.filter(patient=patient_profile)
        
        context = {
            'user_profile': user_profile,
            'patient_profile': patient_profile,
            'appointments': appointments,
        }
        return render(request, 'accounts/profile_patient.html', context)
    
    # Admin veya standart profil
    return render(request, 'accounts/profile.html', {'user_profile': user_profile})

@login_required
def edit_profile(request):
    """Kullanıcı profil düzenleme"""
    user_profile = request.user.profile
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_profile.user_type == 'doctor':
            try:
                doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
            except DoctorProfile.DoesNotExist:
                doctor_profile = DoctorProfile(user_profile=user_profile)
            
            doctor_form = DoctorProfileForm(request.POST, instance=doctor_profile)
            if user_form.is_valid() and doctor_form.is_valid():
                user_form.save()
                doctor_form.save()
                messages.success(request, "Profiliniz başarıyla güncellendi.")
                return redirect('profile')
        
        elif user_profile.user_type == 'patient':
            try:
                patient_profile = PatientProfile.objects.get(user_profile=user_profile)
            except PatientProfile.DoesNotExist:
                patient_profile = PatientProfile(user_profile=user_profile)
            
            patient_form = PatientProfileForm(request.POST, instance=patient_profile)
            if user_form.is_valid() and patient_form.is_valid():
                user_form.save()
                patient_form.save()
                messages.success(request, "Profiliniz başarıyla güncellendi.")
                return redirect('profile')
        
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Profiliniz başarıyla güncellendi.")
                return redirect('profile')
    
    else:
        user_form = UserProfileForm(instance=user_profile)
        
        if user_profile.user_type == 'doctor':
            try:
                doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
                doctor_form = DoctorProfileForm(instance=doctor_profile)
            except DoctorProfile.DoesNotExist:
                doctor_form = DoctorProfileForm()
            
            return render(request, 'accounts/edit_profile_doctor.html', {
                'user_form': user_form,
                'doctor_form': doctor_form,
            })
        
        elif user_profile.user_type == 'patient':
            try:
                patient_profile = PatientProfile.objects.get(user_profile=user_profile)
                patient_form = PatientProfileForm(instance=patient_profile)
            except PatientProfile.DoesNotExist:
                patient_form = PatientProfileForm()
            
            return render(request, 'accounts/edit_profile_patient.html', {
                'user_form': user_form,
                'patient_form': patient_form,
            })
    
    return render(request, 'accounts/edit_profile.html', {'user_form': user_form})

@login_required
def create_doctor_profile(request):
    """Doktor profili oluşturma sayfası"""
    user_profile = request.user.profile
    
    # Kullanıcı tipi doktor değilse yönlendir
    if user_profile.user_type != 'doctor':
        messages.error(request, "Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
        return redirect('dashboard')
    
    # Eğer zaten doktor profili varsa yönlendir
    try:
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        messages.info(request, "Doktor profiliniz zaten oluşturulmuş.")
        return redirect('profile')
    except DoctorProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        if form.is_valid():
            doctor_profile = form.save(commit=False)
            doctor_profile.user_profile = user_profile
            doctor_profile.save()
            messages.success(request, "Doktor profiliniz başarıyla oluşturuldu.")
            return redirect('profile')
    else:
        form = DoctorProfileForm()
    
    return render(request, 'accounts/doctor_profile_form.html', {'form': form})

def home(request):
    """Ana sayfayı gösterir"""
    return render(request, 'home.html')

def logout_view(request):
    """Kullanıcı çıkış view'i"""
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız.")
    return redirect('home')

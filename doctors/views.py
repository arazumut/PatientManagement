from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponseForbidden, JsonResponse
from accounts.models import DoctorProfile, UserProfile
from .models import DoctorAvailability, DoctorLeave, DoctorPerformance
from .forms import DoctorAvailabilityForm, DoctorLeaveForm, DoctorFilterForm
from appointments.models import Appointment, Schedule
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import json

def user_is_doctor_or_admin(user):
    """Kullanıcının doktor veya admin olup olmadığını kontrol eder"""
    try:
        return user.profile.user_type in ['doctor', 'admin']
    except:
        return False

@login_required
def doctor_list(request):
    """Doktor listesini görüntüler"""
    doctors = DoctorProfile.objects.all()
    
    # Filtreleme
    filter_form = DoctorFilterForm(request.GET)
    if filter_form.is_valid():
        # İsim filtresi
        if filter_form.cleaned_data['name']:
            name_query = filter_form.cleaned_data['name']
            doctors = doctors.filter(
                Q(user_profile__user__first_name__icontains=name_query) |
                Q(user_profile__user__last_name__icontains=name_query)
            )
        
        # Uzmanlık filtresi
        if filter_form.cleaned_data['specialty']:
            doctors = doctors.filter(specialty=filter_form.cleaned_data['specialty'])
    
    # Her doktorun toplam hasta ve randevu sayısını hesapla
    doctors = doctors.annotate(
        appointment_count=Count('appointments', distinct=True),
        patient_count=Count('appointments__patient', distinct=True)
    )
    
    return render(request, 'doctors/doctor_list.html', {
        'doctors': doctors,
        'filter_form': filter_form
    })

@login_required
def doctor_detail(request, doctor_id):
    """Doktor detay sayfasını görüntüler"""
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    # Düzenli çalışma programını al
    availabilities = DoctorAvailability.objects.filter(doctor=doctor)
    
    # Randevu istatistiklerini hesapla
    total_appointments = Appointment.objects.filter(doctor=doctor).count()
    completed_appointments = Appointment.objects.filter(doctor=doctor, status='completed').count()
    pending_appointments = Appointment.objects.filter(doctor=doctor, status='pending').count()
    
    # Yaklaşan izinleri al
    upcoming_leaves = DoctorLeave.objects.filter(
        doctor=doctor,
        end_date__gte=timezone.now().date()
    ).order_by('start_date')
    
    # Yaklaşan randevuları al (sadece doktor ve admin görebilir)
    upcoming_appointments = []
    if user_is_doctor_or_admin(request.user):
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).order_by('appointment_date', 'start_time')
    
    context = {
        'doctor': doctor,
        'availabilities': availabilities,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
        'upcoming_leaves': upcoming_leaves,
        'upcoming_appointments': upcoming_appointments,
    }
    
    return render(request, 'doctors/doctor_detail.html', context)

@login_required
def doctor_schedule(request):
    """Doktor çalışma programını görüntüler"""
    user_profile = request.user.profile
    
    if user_profile.user_type == 'admin':
        availabilities = DoctorAvailability.objects.all().order_by('doctor', 'day_of_week', 'start_time')
        doctors = DoctorProfile.objects.all()
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        availabilities = DoctorAvailability.objects.filter(doctor=doctor_profile).order_by('day_of_week', 'start_time')
        doctors = [doctor_profile]
    else:
        # Hasta için farklı bir görünüm sunulabilir
        doctors = DoctorProfile.objects.all()
        availabilities = DoctorAvailability.objects.all().order_by('doctor', 'day_of_week', 'start_time')
    
    return render(request, 'doctors/doctor_schedule.html', {
        'availabilities': availabilities,
        'doctors': doctors
    })

@login_required
def add_doctor_availability(request):
    """Yeni doktor müsaitlik programı ekleme"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Program başarıyla eklendi.")
            return redirect('doctor_schedule')
    else:
        form = DoctorAvailabilityForm(user=request.user)
    
    return render(request, 'doctors/doctor_availability_form.html', {
        'form': form,
        'title': 'Yeni Program Ekle'
    })

@login_required
def edit_doctor_availability(request, availability_id):
    """Doktor müsaitlik programı düzenleme"""
    availability = get_object_or_404(DoctorAvailability, id=availability_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her programı düzenleyebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if availability.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu programı düzenleme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST, instance=availability, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Program başarıyla güncellendi.")
            return redirect('doctor_schedule')
    else:
        form = DoctorAvailabilityForm(instance=availability, user=request.user)
    
    return render(request, 'doctors/doctor_availability_form.html', {
        'form': form,
        'availability': availability,
        'title': 'Programı Düzenle'
    })

@login_required
def delete_doctor_availability(request, availability_id):
    """Doktor müsaitlik programı silme"""
    availability = get_object_or_404(DoctorAvailability, id=availability_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her programı silebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if availability.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu programı silme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        availability.delete()
        messages.success(request, "Program başarıyla silindi.")
        return redirect('doctor_schedule')
    
    return render(request, 'doctors/doctor_availability_confirm_delete.html', {
        'availability': availability
    })

@login_required
def doctor_leave_list(request):
    """Doktor izinlerini listeler"""
    user_profile = request.user.profile
    
    if user_profile.user_type == 'admin':
        leaves = DoctorLeave.objects.all().order_by('-start_date')
        doctors = DoctorProfile.objects.all()
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        leaves = DoctorLeave.objects.filter(doctor=doctor_profile).order_by('-start_date')
        doctors = [doctor_profile]
    else:
        # Hastalar izinleri göremez
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    return render(request, 'doctors/doctor_leave_list.html', {
        'leaves': leaves,
        'doctors': doctors
    })

@login_required
def add_doctor_leave(request):
    """Yeni doktor izni ekleme"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = DoctorLeaveForm(request.POST, user=request.user)
        if form.is_valid():
            leave = form.save()
            
            # Bu tarihlerdeki mevcut randevuları kontrol et
            check_affected_appointments(leave)
            
            messages.success(request, "İzin başarıyla eklendi.")
            return redirect('doctor_leave_list')
    else:
        form = DoctorLeaveForm(user=request.user)
    
    return render(request, 'doctors/doctor_leave_form.html', {
        'form': form,
        'title': 'Yeni İzin Ekle'
    })

@login_required
def edit_doctor_leave(request, leave_id):
    """Doktor izni düzenleme"""
    leave = get_object_or_404(DoctorLeave, id=leave_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her izni düzenleyebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if leave.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu izni düzenleme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = DoctorLeaveForm(request.POST, instance=leave, user=request.user)
        if form.is_valid():
            updated_leave = form.save()
            
            # Bu tarihlerdeki mevcut randevuları kontrol et
            check_affected_appointments(updated_leave)
            
            messages.success(request, "İzin başarıyla güncellendi.")
            return redirect('doctor_leave_list')
    else:
        form = DoctorLeaveForm(instance=leave, user=request.user)
    
    return render(request, 'doctors/doctor_leave_form.html', {
        'form': form,
        'leave': leave,
        'title': 'İzni Düzenle'
    })

@login_required
def delete_doctor_leave(request, leave_id):
    """Doktor izni silme"""
    leave = get_object_or_404(DoctorLeave, id=leave_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her izni silebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if leave.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu izni silme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        leave.delete()
        messages.success(request, "İzin başarıyla silindi.")
        return redirect('doctor_leave_list')
    
    return render(request, 'doctors/doctor_leave_confirm_delete.html', {
        'leave': leave
    })

@login_required
def doctor_performance(request):
    """Doktor performans istatistikleri"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    user_profile = request.user.profile
    
    if user_profile.user_type == 'admin':
        # Admin tüm doktorların performansını görebilir
        performances = DoctorPerformance.objects.all().order_by('doctor', '-month')
        doctors = DoctorProfile.objects.all()
        
        # Seçilen doktor (varsa)
        selected_doctor_id = request.GET.get('doctor_id')
        if selected_doctor_id:
            selected_doctor = get_object_or_404(DoctorProfile, id=selected_doctor_id)
            performances = performances.filter(doctor=selected_doctor)
        else:
            selected_doctor = None
            
    elif user_profile.user_type == 'doctor':
        # Doktor sadece kendi performansını görebilir
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        performances = DoctorPerformance.objects.filter(doctor=doctor_profile).order_by('-month')
        doctors = [doctor_profile]
        selected_doctor = doctor_profile
    
    # Son 12 ay için performans kayıtlarını kontrol et ve güncelle
    update_performance_records()
    
    # Performans grafiği verileri
    chart_data = prepare_performance_chart_data(performances)
    
    return render(request, 'doctors/doctor_performance.html', {
        'performances': performances,
        'doctors': doctors,
        'selected_doctor': selected_doctor,
        'chart_data': json.dumps(chart_data)
    })

def update_performance_records():
    """Doktorlar için performans kayıtlarını günceller"""
    # Tüm doktorları al
    doctors = DoctorProfile.objects.all()
    
    # Son 12 ay için tarih aralığı
    today = timezone.now().date()
    current_month_start = datetime(today.year, today.month, 1).date()
    
    for i in range(12):
        # Ayın ilk günü
        month_date = (current_month_start - timedelta(days=30*i)).replace(day=1)
        
        # Ayın son günü
        _, last_day = calendar.monthrange(month_date.year, month_date.month)
        month_end = month_date.replace(day=last_day)
        
        for doctor in doctors:
            # Bu ay için performans kaydı var mı kontrol et
            performance, created = DoctorPerformance.objects.get_or_create(
                doctor=doctor,
                month=month_date,
                defaults={
                    'total_appointments': 0,
                    'completed_appointments': 0,
                    'cancelled_appointments': 0,
                }
            )
            
            # Eğer kayıt varsa ve ay tamamlanmışsa güncelle
            if month_end < today:
                # Bu ay için randevu istatistiklerini hesapla
                total_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date__gte=month_date,
                    appointment_date__lte=month_end
                ).count()
                
                completed_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date__gte=month_date,
                    appointment_date__lte=month_end,
                    status='completed'
                ).count()
                
                cancelled_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date__gte=month_date,
                    appointment_date__lte=month_end,
                    status='cancelled'
                ).count()
                
                # Performans kaydını güncelle
                performance.total_appointments = total_appointments
                performance.completed_appointments = completed_appointments
                performance.cancelled_appointments = cancelled_appointments
                performance.save()

def prepare_performance_chart_data(performances):
    """Performans grafiği için veri hazırlar"""
    chart_data = {
        'labels': [],
        'datasets': [
            {
                'label': 'Tamamlanan Randevular',
                'data': [],
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1
            },
            {
                'label': 'İptal Edilen Randevular',
                'data': [],
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Toplam Randevular',
                'data': [],
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderColor': 'rgba(75, 192, 192, 1)',
                'borderWidth': 1
            }
        ]
    }
    
    # Performans kayıtlarını ay bazında grupla
    months = {}
    for performance in performances:
        month_str = performance.month.strftime('%Y-%m')
        if month_str not in months:
            months[month_str] = {
                'label': performance.month.strftime('%b %Y'),
                'completed': 0,
                'cancelled': 0,
                'total': 0
            }
        
        # Her doktorun verilerini topla
        months[month_str]['completed'] += performance.completed_appointments
        months[month_str]['cancelled'] += performance.cancelled_appointments
        months[month_str]['total'] += performance.total_appointments
    
    # Ayları tarih sırasına göre sırala ve grafik verilerine ekle
    for month in sorted(months.keys()):
        chart_data['labels'].append(months[month]['label'])
        chart_data['datasets'][0]['data'].append(months[month]['completed'])
        chart_data['datasets'][1]['data'].append(months[month]['cancelled'])
        chart_data['datasets'][2]['data'].append(months[month]['total'])
    
    return chart_data

def check_affected_appointments(leave):
    """Doktor izni sırasındaki randevuları kontrol eder ve bildirim gönderir"""
    affected_appointments = Appointment.objects.filter(
        doctor=leave.doctor,
        appointment_date__gte=leave.start_date,
        appointment_date__lte=leave.end_date,
        status__in=['pending', 'confirmed']
    )
    
    # İzinden etkilenen randevular için bildirim ekle
    for appointment in affected_appointments:
        # Burada e-posta/SMS gönderimi yapılabilir
        pass

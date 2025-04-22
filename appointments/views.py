from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from accounts.models import PatientProfile, UserProfile, DoctorProfile
from .models import Appointment, Schedule, Notification
from .forms import AppointmentForm, AppointmentSlotForm, ScheduleForm, AppointmentSearchForm, NotificationForm
from django.utils import timezone
from datetime import datetime, timedelta
import json

def user_is_doctor_or_admin(user):
    """Kullanıcının doktor veya admin olup olmadığını kontrol eder"""
    try:
        return user.profile.user_type in ['doctor', 'admin']
    except:
        return False

@login_required
def appointment_list(request):
    """Randevu listesini görüntüler"""
    user_profile = request.user.profile
    
    # Kullanıcı tipine göre randevu listeleme
    if user_profile.user_type == 'admin':
        appointments = Appointment.objects.all()
    elif user_profile.user_type == 'doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
            appointments = Appointment.objects.filter(doctor=doctor_profile)
        except DoctorProfile.DoesNotExist:
            # Doktor profili yoksa önce onu oluşturma sayfasına yönlendir
            messages.warning(request, "Doktor profiliniz henüz oluşturulmamış. Lütfen doktor bilgilerinizi ekleyin.")
            return redirect('create_doctor_profile')
    elif user_profile.user_type == 'patient':
        try:
            patient_profile = PatientProfile.objects.get(user_profile=user_profile)
            appointments = Appointment.objects.filter(patient=patient_profile)
        except PatientProfile.DoesNotExist:
            messages.error(request, "Hasta profiliniz bulunamadı. Lütfen yönetici ile iletişime geçiniz.")
            return redirect('dashboard')
    else:
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    # Filtrele
    search_form = AppointmentSearchForm(request.GET)
    if search_form.is_valid():
        filters = {}
        
        # Doktor filtresi
        if search_form.cleaned_data['doctor']:
            filters['doctor'] = search_form.cleaned_data['doctor']
        
        # Hasta adı/TC filtresi
        if search_form.cleaned_data['patient'] and (user_profile.user_type == 'admin' or user_profile.user_type == 'doctor'):
            patient_query = search_form.cleaned_data['patient']
            appointments = appointments.filter(
                Q(patient__user_profile__user__first_name__icontains=patient_query) |
                Q(patient__user_profile__user__last_name__icontains=patient_query) |
                Q(patient__tc_number__icontains=patient_query)
            )
        
        # Tarih aralığı
        if search_form.cleaned_data['date_from']:
            filters['appointment_date__gte'] = search_form.cleaned_data['date_from']
        
        if search_form.cleaned_data['date_to']:
            filters['appointment_date__lte'] = search_form.cleaned_data['date_to']
        
        # Durum filtresi
        if search_form.cleaned_data['status']:
            filters['status'] = search_form.cleaned_data['status']
        
        # Filtreleri uygula
        if filters:
            appointments = appointments.filter(**filters)
    
    # Sırala: Önce yaklaşan randevular
    appointments = appointments.order_by('appointment_date', 'start_time')
    
    context = {
        'appointments': appointments,
        'search_form': search_form,
    }
    
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def add_appointment(request):
    """Yeni randevu ekleme"""
    # İlk form: Doktor ve tarih seçimi
    if request.method == 'POST':
        if 'doctor' in request.POST and 'date' in request.POST:
            form = AppointmentForm(request.POST, user=request.user)
            if form.is_valid():
                # Doktor ve tarih bilgilerini al
                doctor = form.cleaned_data['doctor']
                date = form.cleaned_data['date']
                
                # Uygun zaman dilimlerini bul
                available_slots = get_available_slots(doctor, date)
                
                if not available_slots:
                    messages.error(request, "Seçilen tarihte uygun randevu saati bulunmamaktadır.")
                    return render(request, 'appointments/appointment_form.html', {'form': form})
                
                # Zaman dilimi seçim formunu oluştur
                slot_form = AppointmentSlotForm(available_slots=available_slots)
                
                # İlk form bilgilerini session'da sakla
                request.session['appointment_step1'] = {
                    'doctor_id': doctor.id,
                    'date': date.strftime('%Y-%m-%d'),
                    'reason': form.cleaned_data['reason'],
                    'notes': form.cleaned_data['notes'] if form.cleaned_data['notes'] else '',
                }
                
                return render(request, 'appointments/appointment_slot_form.html', {
                    'doctor': doctor,
                    'date': date,
                    'slot_form': slot_form
                })
        
        # İkinci form: Zaman dilimi seçimi
        elif 'slot' in request.POST and 'appointment_step1' in request.session:
            slot_form = AppointmentSlotForm(request.POST)
            step1_data = request.session['appointment_step1']
            
            if slot_form.is_valid():
                # Zaman dilimini al ve randevu oluştur
                slot = slot_form.cleaned_data['slot']
                start_time_str, end_time_str = slot.split('|')
                
                doctor = get_object_or_404(DoctorProfile, id=step1_data['doctor_id'])
                date = datetime.strptime(step1_data['date'], '%Y-%m-%d').date()
                
                # Kullanıcı tipine göre hasta belirleme
                if request.user.profile.user_type == 'patient':
                    patient = PatientProfile.objects.get(user_profile=request.user.profile)
                elif 'patient_id' in request.POST:
                    # Doktor/admin hasta seçebilir
                    patient = get_object_or_404(PatientProfile, id=request.POST['patient_id'])
                else:
                    messages.error(request, "Hasta bilgisi eksik.")
                    return redirect('add_appointment')
                
                # Programı bul
                try:
                    schedule = Schedule.objects.get(
                        doctor=doctor,
                        date=date,
                        start_time__lte=datetime.strptime(start_time_str, '%H:%M').time(),
                        end_time__gte=datetime.strptime(end_time_str, '%H:%M').time()
                    )
                except Schedule.DoesNotExist:
                    messages.error(request, "Seçilen zaman dilimi artık uygun değil.")
                    return redirect('add_appointment')
                
                # Randevu oluştur
                appointment = Appointment(
                    patient=patient,
                    doctor=doctor,
                    schedule=schedule,
                    appointment_date=date,
                    start_time=datetime.strptime(start_time_str, '%H:%M').time(),
                    end_time=datetime.strptime(end_time_str, '%H:%M').time(),
                    reason=step1_data['reason'],
                    notes=step1_data['notes'],
                    status='confirmed' if request.user.profile.user_type in ['doctor', 'admin'] else 'pending'
                )
                
                try:
                    appointment.save()
                    # Oturumdan geçici verileri temizle
                    if 'appointment_step1' in request.session:
                        del request.session['appointment_step1']
                    
                    # Otomatik bildirim oluşturma
                    notification = Notification(
                        appointment=appointment,
                        notification_type='email',
                        is_sent=False
                    )
                    notification.save()
                    
                    messages.success(request, "Randevu başarıyla oluşturuldu.")
                    return redirect('appointment_detail', appointment_id=appointment.id)
                except Exception as e:
                    messages.error(request, f"Randevu oluşturulamadı: {str(e)}")
                    return redirect('add_appointment')
    
    # İlk form: Doktor ve tarih seçimi
    form = AppointmentForm(user=request.user)
    
    # Doktor/admin için hasta seçme imkanı
    patients = None
    if request.user.profile.user_type in ['doctor', 'admin']:
        patients = PatientProfile.objects.all()
    
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'patients': patients,
    })

@login_required
def appointment_detail(request, appointment_id):
    """Randevu detay görüntüleme"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    user_profile = request.user.profile
    
    # Yetki kontrolü
    if user_profile.user_type == 'admin':
        pass  # Admin her randevuyu görebilir
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        if appointment.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu randevuyu görüntüleme yetkiniz bulunmamaktadır.")
    elif user_profile.user_type == 'patient':
        patient_profile = PatientProfile.objects.get(user_profile=user_profile)
        if appointment.patient.id != patient_profile.id:
            return HttpResponseForbidden("Bu randevuyu görüntüleme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    return render(request, 'appointments/appointment_detail.html', {
        'appointment': appointment
    })

@login_required
def edit_appointment(request, appointment_id):
    """Randevu düzenleme"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    user_profile = request.user.profile
    
    # Yetki kontrolü
    if user_profile.user_type == 'admin':
        pass  # Admin her randevuyu düzenleyebilir
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        if appointment.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu randevuyu düzenleme yetkiniz bulunmamaktadır.")
    elif user_profile.user_type == 'patient':
        patient_profile = PatientProfile.objects.get(user_profile=user_profile)
        if appointment.patient.id != patient_profile.id:
            return HttpResponseForbidden("Bu randevuyu düzenleme yetkiniz bulunmamaktadır.")
        
        # Hasta onaylanmış veya tamamlanmış randevuları düzenleyemez
        if appointment.status in ['confirmed', 'completed']:
            return HttpResponseForbidden("Bu randevu durumunda düzenleme yapamazsınız.")
    else:
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            updated_appointment = form.save(commit=False)
            
            # Sadece belirli alanları güncelleyebiliriz, çünkü tarih ve doktor özel işleme tabidir
            appointment.reason = updated_appointment.reason
            appointment.notes = updated_appointment.notes
            
            # Doktor veya admin tüm bilgileri güncelleyebilir
            if user_profile.user_type in ['doctor', 'admin']:
                if 'status' in request.POST:
                    appointment.status = request.POST['status']
            
            appointment.save()
            messages.success(request, "Randevu başarıyla güncellendi.")
            return redirect('appointment_detail', appointment_id=appointment.id)
    else:
        form = AppointmentForm(instance=appointment, user=request.user)
    
    return render(request, 'appointments/appointment_edit.html', {
        'form': form,
        'appointment': appointment
    })

@login_required
def cancel_appointment(request, appointment_id):
    """Randevu iptali"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    user_profile = request.user.profile
    
    # Yetki kontrolü
    if user_profile.user_type == 'admin':
        pass  # Admin her randevuyu iptal edebilir
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        if appointment.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu randevuyu iptal etme yetkiniz bulunmamaktadır.")
    elif user_profile.user_type == 'patient':
        patient_profile = PatientProfile.objects.get(user_profile=user_profile)
        if appointment.patient.id != patient_profile.id:
            return HttpResponseForbidden("Bu randevuyu iptal etme yetkiniz bulunmamaktadır.")
        
        # Hasta tamamlanmış randevuları iptal edemez
        if appointment.status == 'completed':
            return HttpResponseForbidden("Tamamlanmış randevular iptal edilemez.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, "Randevu başarıyla iptal edildi.")
        return redirect('appointment_list')
    
    return render(request, 'appointments/appointment_cancel.html', {
        'appointment': appointment
    })

@login_required
def confirm_appointment(request, appointment_id):
    """Randevu onaylama"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Yetki kontrolü - sadece doktor veya admin onaylayabilir
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if appointment.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu randevuyu onaylama yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, "Randevu başarıyla onaylandı.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'appointments/appointment_confirm.html', {
        'appointment': appointment
    })

@login_required
def complete_appointment(request, appointment_id):
    """Randevu tamamlama"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Yetki kontrolü - sadece doktor veya admin tamamlayabilir
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if appointment.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu randevuyu tamamlama yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        appointment.status = 'completed'
        appointment.save()
        messages.success(request, "Randevu başarıyla tamamlandı.")
        return redirect('appointment_detail', appointment_id=appointment.id)
    
    return render(request, 'appointments/appointment_complete.html', {
        'appointment': appointment
    })

@login_required
def schedule_list(request):
    """Doktor programlarını listeler"""
    user_profile = request.user.profile
    
    if user_profile.user_type == 'admin':
        schedules = Schedule.objects.all().order_by('date', 'start_time')
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        schedules = Schedule.objects.filter(doctor=doctor_profile).order_by('date', 'start_time')
    else:
        # Hastalar sadece doktorun müsait zamanlarını görebilir, ayrı bir sayfada
        return redirect('doctor_available_slots')
    
    return render(request, 'appointments/schedule_list.html', {
        'schedules': schedules
    })

@login_required
def add_schedule(request):
    """Yeni program ekleme"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Program başarıyla eklendi.")
            return redirect('schedule_list')
    else:
        form = ScheduleForm(user=request.user)
    
    return render(request, 'appointments/schedule_form.html', {
        'form': form,
        'title': 'Yeni Program Ekle'
    })

@login_required
def edit_schedule(request, schedule_id):
    """Program düzenleme"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her programı düzenleyebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if schedule.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu programı düzenleme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Program başarıyla güncellendi.")
            return redirect('schedule_list')
    else:
        form = ScheduleForm(instance=schedule, user=request.user)
    
    return render(request, 'appointments/schedule_form.html', {
        'form': form,
        'schedule': schedule,
        'title': 'Programı Düzenle'
    })

@login_required
def delete_schedule(request, schedule_id):
    """Program silme"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Yetki kontrolü
    if request.user.profile.user_type == 'admin':
        pass  # Admin her programı silebilir
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if schedule.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu programı silme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    # Programın randevusu var mı kontrol et
    has_appointments = Appointment.objects.filter(
        schedule=schedule,
        status__in=['pending', 'confirmed']
    ).exists()
    
    if has_appointments and request.method != 'POST':
        return render(request, 'appointments/schedule_delete_warning.html', {
            'schedule': schedule
        })
    
    if request.method == 'POST':
        # Eğer randevular varsa ve force=true ise, randevuları iptal et
        if has_appointments and request.POST.get('force') == 'true':
            Appointment.objects.filter(schedule=schedule).update(status='cancelled')
        
        schedule.delete()
        messages.success(request, "Program başarıyla silindi.")
        return redirect('schedule_list')
    
    return render(request, 'appointments/schedule_confirm_delete.html', {
        'schedule': schedule
    })

@login_required
def doctor_available_slots(request, doctor_id=None):
    """Doktorun müsait zamanlarını görüntüler"""
    doctors = DoctorProfile.objects.all()
    selected_doctor = None
    available_dates = []
    
    if doctor_id:
        selected_doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        
        # Gelecek 30 gün için programları bul
        today = timezone.now().date()
        future_date = today + timedelta(days=30)
        
        schedules = Schedule.objects.filter(
            doctor=selected_doctor,
            date__gte=today,
            date__lte=future_date
        ).order_by('date')
        
        # Her bir programı kontrol et ve müsait günleri bul
        dates_set = set()
        for schedule in schedules:
            # O gün için randevuları kontrol et
            slots = get_available_slots(selected_doctor, schedule.date)
            if slots:  # Eğer müsait zaman dilimi varsa, bu günü ekle
                dates_set.add(schedule.date)
        
        available_dates = sorted(list(dates_set))
    
    return render(request, 'appointments/doctor_available_slots.html', {
        'doctors': doctors,
        'selected_doctor': selected_doctor,
        'available_dates': available_dates
    })

@login_required
def search_appointments(request):
    """Randevu arama"""
    return appointment_list(request)

@login_required
def patient_appointments(request):
    """Hasta için randevu görüntüleme"""
    if request.user.profile.user_type != 'patient':
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    patient_profile = PatientProfile.objects.get(user_profile=request.user.profile)
    
    # Aktif (gelecek) randevular
    today = timezone.now().date()
    active_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__gte=today,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'start_time')
    
    # Geçmiş randevular
    past_appointments = Appointment.objects.filter(
        patient=patient_profile
    ).filter(
        Q(appointment_date__lt=today) |
        Q(status__in=['completed', 'cancelled'])
    ).order_by('-appointment_date', '-start_time')
    
    return render(request, 'appointments/patient_appointments.html', {
        'active_appointments': active_appointments,
        'past_appointments': past_appointments
    })

@login_required
def appointment_calendar(request):
    """Takvim görünümü"""
    user_profile = request.user.profile
    
    if user_profile.user_type == 'admin':
        appointments = Appointment.objects.all()
    elif user_profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=user_profile)
        appointments = Appointment.objects.filter(doctor=doctor_profile)
    elif user_profile.user_type == 'patient':
        patient_profile = PatientProfile.objects.get(user_profile=user_profile)
        appointments = Appointment.objects.filter(patient=patient_profile)
    else:
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    # Takvim verilerini oluştur
    calendar_events = []
    for appointment in appointments:
        # İptal edilen randevular için farklı renk
        color = '#ef4444' if appointment.status == 'cancelled' else (
            '#4f46e5' if appointment.status == 'confirmed' else (
                '#10b981' if appointment.status == 'completed' else '#f59e0b'
            )
        )
        
        start_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
        end_datetime = datetime.combine(appointment.appointment_date, appointment.end_time)
        
        calendar_events.append({
            'id': appointment.id,
            'title': f"{appointment.patient.user_profile.user.get_full_name()} - Dr. {appointment.doctor.user_profile.user.get_full_name()}",
            'start': start_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
            'url': f'/randevular/{appointment.id}/',
            'backgroundColor': color,
            'borderColor': color,
        })
    
    return render(request, 'appointments/appointment_calendar.html', {
        'calendar_events': json.dumps(calendar_events)
    })

def get_available_slots(doctor, date):
    """Doktorun belirli bir gün için uygun zaman dilimlerini hesaplar"""
    # Doktorun program bilgilerini al
    schedules = Schedule.objects.filter(doctor=doctor, date=date)
    
    if not schedules:
        return []
    
    # Mevcut randevuları al
    existing_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date,
        status__in=['pending', 'confirmed']
    )
    
    available_slots = []
    
    # Her bir program için uygun zaman dilimlerini hesapla
    for schedule in schedules:
        start_time = schedule.start_time
        end_time = schedule.end_time
        
        # 30 dakikalık dilimler oluştur
        slot_duration = timedelta(minutes=30)
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        while current_time + slot_duration <= end_datetime:
            slot_start = current_time.time()
            slot_end = (current_time + slot_duration).time()
            
            # Bu zaman dilimi müsait mi kontrol et
            is_available = True
            for appointment in existing_appointments:
                if (slot_start < appointment.end_time and slot_end > appointment.start_time):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start': slot_start.strftime('%H:%M'),
                    'end': slot_end.strftime('%H:%M')
                })
            
            current_time += slot_duration
    
    return available_slots

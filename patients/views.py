from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from accounts.models import PatientProfile, UserProfile, DoctorProfile
from .models import MedicalRecord, Prescription, Medication, PatientNote
from .forms import PatientProfileForm, MedicalRecordForm, PrescriptionForm, MedicationForm, PatientNoteForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def user_is_doctor_or_admin(user):
    """Kullanıcının doktor veya admin olup olmadığını kontrol eder"""
    try:
        return user.profile.user_type in ['doctor', 'admin']
    except:
        return False

def user_is_patients_doctor(user, patient):
    """Kullanıcının hastanın doktoru olup olmadığını kontrol eder"""
    if user.profile.user_type == 'admin':
        return True
    
    if user.profile.user_type == 'doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_profile=user.profile)
            has_appointment = patient.appointments.filter(doctor=doctor_profile).exists()
            has_record = MedicalRecord.objects.filter(patient=patient, doctor=doctor_profile).exists()
            return has_appointment or has_record
        except:
            return False
    
    return False

@login_required
def patient_list(request):
    """Hasta listesini görüntüler"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    query = request.GET.get('q', '')
    patients = PatientProfile.objects.all()
    
    # Arama sorgusu varsa filtreleme yap
    if query:
        patients = patients.filter(
            Q(user_profile__user__first_name__icontains=query) |
            Q(user_profile__user__last_name__icontains=query) |
            Q(tc_number__icontains=query)
        )
    
    # Doktor ise sadece kendi hastalarını göster
    if request.user.profile.user_type == 'doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
            # Doktor profili yoksa ve doktor ise, önce doktor profili oluşturma sayfasına yönlendir
        except DoctorProfile.DoesNotExist:
            messages.warning(request, "Doktor profiliniz henüz oluşturulmamış. Lütfen doktor bilgilerinizi ekleyin.")
            return redirect('create_doctor_profile')
            
        # Doktorun hasta listesini filtrele
        appointments = doctor_profile.appointments.all()
        patient_ids = set(appointment.patient_id for appointment in appointments)
        
        # Tıbbi kayıtlardan da ekle
        medical_records = MedicalRecord.objects.filter(doctor=doctor_profile)
        for record in medical_records:
            patient_ids.add(record.patient_id)
            
        patients = patients.filter(id__in=patient_ids)
    
    # Sayfalama
    paginator = Paginator(patients, 10)
    page = request.GET.get('page')
    
    try:
        patients = paginator.page(page)
    except PageNotAnInteger:
        patients = paginator.page(1)
    except EmptyPage:
        patients = paginator.page(paginator.num_pages)
    
    return render(request, 'patients/patient_list.html', {'patients': patients, 'query': query})

@login_required
def patient_detail(request, patient_id):
    """Hasta detay sayfasını görüntüler"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Hasta kendisi veya doktor/admin ise erişim izni var
    if request.user.profile.user_type == 'patient':
        if not hasattr(request.user.profile, 'patient_profile') or request.user.profile.patient_profile.id != patient_id:
            return HttpResponseForbidden("Bu hastanın bilgilerini görüntüleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    # Hasta notları
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        notes = PatientNote.objects.filter(patient=patient, doctor=doctor_profile)
    else:
        notes = PatientNote.objects.filter(patient=patient)
    
    # Tıbbi kayıtlar
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date')
    
    # Reçeteler
    prescriptions = Prescription.objects.filter(medical_record__patient=patient).order_by('-date_prescribed')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'prescriptions': prescriptions,
        'notes': notes,
    }
    
    return render(request, 'patients/patient_detail.html', context)

@login_required
def add_patient(request):
    """Yeni hasta ekleme"""
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"{patient.user_profile.user.get_full_name()} başarıyla kaydedildi.")
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientProfileForm()
    
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Yeni Hasta Ekle'})

@login_required
def edit_patient(request, patient_id):
    """Hasta bilgilerini düzenleme"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Hasta kendisi veya admin ise düzenleyebilir
    if request.user.profile.user_type == 'patient':
        if not hasattr(request.user.profile, 'patient_profile') or request.user.profile.patient_profile.id != patient_id:
            return HttpResponseForbidden("Bu hastanın bilgilerini düzenleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Hasta bilgileri başarıyla güncellendi.")
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientProfileForm(instance=patient)
    
    return render(request, 'patients/patient_form.html', {'form': form, 'patient': patient, 'title': 'Hasta Bilgilerini Düzenle'})

@login_required
def add_medical_record(request, patient_id):
    """Hasta için yeni tıbbi kayıt ekleme"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Sadece doktorlar ve admin tıbbi kayıt ekleyebilir
    if not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            medical_record = form.save(commit=False)
            medical_record.patient = patient
            
            # Doktor ise kendi profilini kullan
            if request.user.profile.user_type == 'doctor':
                medical_record.doctor = DoctorProfile.objects.get(user_profile=request.user.profile)
            
            medical_record.save()
            messages.success(request, "Tıbbi kayıt başarıyla eklendi.")
            return redirect('medical_record_detail', record_id=medical_record.id)
    else:
        form = MedicalRecordForm()
    
    return render(request, 'patients/medical_record_form.html', {'form': form, 'patient': patient, 'title': 'Yeni Tıbbi Kayıt Ekle'})

@login_required
def medical_record_detail(request, record_id):
    """Tıbbi kayıt detayını görüntüleme"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Hasta kendisi, ilgili doktor veya admin ise erişim izni var
    if request.user.profile.user_type == 'patient':
        if not hasattr(request.user.profile, 'patient_profile') or request.user.profile.patient_profile.id != record.patient.id:
            return HttpResponseForbidden("Bu tıbbi kaydı görüntüleme yetkiniz bulunmamaktadır.")
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if record.doctor.id != doctor_profile.id and not user_is_patients_doctor(request.user, record.patient):
            return HttpResponseForbidden("Bu tıbbi kaydı görüntüleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    # Reçeteler
    prescriptions = Prescription.objects.filter(medical_record=record)
    
    return render(request, 'patients/medical_record_detail.html', {
        'record': record,
        'prescriptions': prescriptions,
    })

@login_required
def edit_medical_record(request, record_id):
    """Tıbbi kayıt düzenleme"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Sadece kayıt sahibi doktor veya admin düzenleyebilir
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if record.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu tıbbi kaydı düzenleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Tıbbi kayıt başarıyla güncellendi.")
            return redirect('medical_record_detail', record_id=record.id)
    else:
        form = MedicalRecordForm(instance=record)
    
    return render(request, 'patients/medical_record_form.html', {
        'form': form,
        'record': record,
        'patient': record.patient,
        'title': 'Tıbbi Kayıt Düzenle'
    })

@login_required
def add_prescription(request, record_id):
    """Tıbbi kayıt için reçete ekleme"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Sadece kayıt sahibi doktor veya admin reçete ekleyebilir
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if record.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu tıbbi kayda reçete ekleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.medical_record = record
            prescription.save()
            messages.success(request, "Reçete başarıyla eklendi.")
            return redirect('prescription_detail', prescription_id=prescription.id)
    else:
        form = PrescriptionForm()
    
    return render(request, 'patients/prescription_form.html', {
        'form': form,
        'record': record,
        'title': 'Yeni Reçete Ekle'
    })

@login_required
def prescription_detail(request, prescription_id):
    """Reçete detayını görüntüleme"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    record = prescription.medical_record
    
    # Hasta kendisi, ilgili doktor veya admin ise erişim izni var
    if request.user.profile.user_type == 'patient':
        if not hasattr(request.user.profile, 'patient_profile') or request.user.profile.patient_profile.id != record.patient.id:
            return HttpResponseForbidden("Bu reçeteyi görüntüleme yetkiniz bulunmamaktadır.")
    elif request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if record.doctor.id != doctor_profile.id and not user_is_patients_doctor(request.user, record.patient):
            return HttpResponseForbidden("Bu reçeteyi görüntüleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu sayfayı görüntüleme yetkiniz bulunmamaktadır.")
    
    # İlaçlar
    medications = Medication.objects.filter(prescription=prescription)
    
    if request.method == 'POST' and 'add_medication' in request.POST:
        medication_form = MedicationForm(request.POST)
        if medication_form.is_valid():
            medication = medication_form.save(commit=False)
            medication.prescription = prescription
            medication.save()
            messages.success(request, "İlaç başarıyla eklendi.")
            return redirect('prescription_detail', prescription_id=prescription.id)
    else:
        medication_form = MedicationForm()
    
    return render(request, 'patients/prescription_detail.html', {
        'prescription': prescription,
        'record': record,
        'medications': medications,
        'medication_form': medication_form,
    })

@login_required
def add_medication(request, prescription_id):
    """Reçeteye ilaç ekleme"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    record = prescription.medical_record
    
    # Sadece kayıt sahibi doktor veya admin ilaç ekleyebilir
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if record.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu reçeteye ilaç ekleme yetkiniz bulunmamaktadır.")
    elif not user_is_doctor_or_admin(request.user):
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            medication = form.save(commit=False)
            medication.prescription = prescription
            medication.save()
            messages.success(request, "İlaç başarıyla eklendi.")
            return redirect('prescription_detail', prescription_id=prescription.id)
    else:
        form = MedicationForm()
    
    return render(request, 'patients/medication_form.html', {
        'form': form,
        'prescription': prescription,
        'title': 'Reçeteye İlaç Ekle'
    })

@login_required
def add_patient_note(request, patient_id):
    """Hasta için not ekleme"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Sadece doktorlar not ekleyebilir
    if request.user.profile.user_type != 'doctor':
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
    
    if request.method == 'POST':
        form = PatientNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.patient = patient
            note.doctor = doctor_profile
            note.save()
            messages.success(request, "Not başarıyla eklendi.")
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientNoteForm()
    
    return render(request, 'patients/patient_note_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Yeni Not Ekle'
    })

@login_required
def edit_patient_note(request, note_id):
    """Hasta notunu düzenleme"""
    note = get_object_or_404(PatientNote, id=note_id)
    
    # Sadece notu yazan doktor düzenleyebilir
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if note.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu notu düzenleme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        form = PatientNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Not başarıyla güncellendi.")
            return redirect('patient_detail', patient_id=note.patient.id)
    else:
        form = PatientNoteForm(instance=note)
    
    return render(request, 'patients/patient_note_form.html', {
        'form': form,
        'note': note,
        'patient': note.patient,
        'title': 'Not Düzenle'
    })

@login_required
def delete_patient_note(request, note_id):
    """Hasta notunu silme"""
    note = get_object_or_404(PatientNote, id=note_id)
    patient_id = note.patient.id
    
    # Sadece notu yazan doktor silebilir
    if request.user.profile.user_type == 'doctor':
        doctor_profile = DoctorProfile.objects.get(user_profile=request.user.profile)
        if note.doctor.id != doctor_profile.id:
            return HttpResponseForbidden("Bu notu silme yetkiniz bulunmamaktadır.")
    else:
        return HttpResponseForbidden("Bu işlemi yapma yetkiniz bulunmamaktadır.")
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, "Not başarıyla silindi.")
        return redirect('patient_detail', patient_id=patient_id)
    
    return render(request, 'patients/patient_note_confirm_delete.html', {
        'note': note,
        'patient': note.patient
    })

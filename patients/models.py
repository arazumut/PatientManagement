from django.db import models
from accounts.models import PatientProfile, DoctorProfile
from django.utils import timezone

class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='medical_records')
    diagnosis = models.CharField(max_length=255)
    diagnosis_details = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.patient} - {self.diagnosis} ({self.date.strftime('%d.%m.%Y')})"

class Prescription(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    prescription_number = models.CharField(max_length=20, unique=True)
    date_prescribed = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Reçete #{self.prescription_number} - {self.medical_record.patient}"

class Medication(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.dosage}"

class PatientNote(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='notes')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='patient_notes')
    note = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Not: {self.patient} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"

from django.db import models
from accounts.models import PatientProfile, DoctorProfile
from django.utils import timezone

class Schedule(models.Model):
    """Doktorların müsait olduğu zaman dilimlerini tanımlar"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']
    
    def __str__(self):
        return f"Dr. {self.doctor.user_profile.user.get_full_name()} - {self.date.strftime('%d.%m.%Y')} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class Appointment(models.Model):
    """Hasta randevularını tanımlar"""
    STATUS_CHOICES = (
        ('pending', 'Beklemede'),
        ('confirmed', 'Onaylandı'),
        ('cancelled', 'İptal Edildi'),
        ('completed', 'Tamamlandı'),
    )
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment_date', 'start_time']
        unique_together = ['doctor', 'appointment_date', 'start_time']
    
    def __str__(self):
        return f"{self.patient.user_profile.user.get_full_name()} - Dr. {self.doctor.user_profile.user.get_full_name()} ({self.appointment_date.strftime('%d.%m.%Y')} {self.start_time.strftime('%H:%M')})"
    
    def is_past_appointment(self):
        appointment_datetime = timezone.datetime.combine(
            self.appointment_date, 
            self.end_time
        )
        return timezone.now() > timezone.make_aware(appointment_datetime)

class Notification(models.Model):
    """Randevu hatırlatmaları için bildirim modeli"""
    TYPE_CHOICES = (
        ('email', 'E-posta'),
        ('sms', 'SMS'),
    )
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Hatırlatma: {self.appointment} - {self.get_notification_type_display()}"

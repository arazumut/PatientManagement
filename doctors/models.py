from django.db import models
from accounts.models import DoctorProfile
from django.utils import timezone

class DoctorAvailability(models.Model):
    """Doktorun düzenli olarak uygun olduğu günler ve saat aralıkları"""
    DAYS_OF_WEEK = (
        (0, 'Pazartesi'),
        (1, 'Salı'),
        (2, 'Çarşamba'),
        (3, 'Perşembe'),
        (4, 'Cuma'),
        (5, 'Cumartesi'),
        (6, 'Pazar'),
    )
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"Dr. {self.doctor.user_profile.user.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

class DoctorLeave(models.Model):
    """Doktorun izinli/uygun olmadığı günler"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Dr. {self.doctor.user_profile.user.get_full_name()} - İzin: {self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}"

class DoctorPerformance(models.Model):
    """Doktor performans metrikleri"""
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='performance')
    month = models.DateField()  # Sadece ay ve yıl bilgisi kullanılacak
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['doctor', 'month']
    
    def __str__(self):
        return f"Dr. {self.doctor.user_profile.user.get_full_name()} - {self.month.strftime('%m.%Y')}"
    
    def completion_rate(self):
        """Tamamlanan randevu oranını hesaplar"""
        if self.total_appointments > 0:
            return (self.completed_appointments / self.total_appointments) * 100
        return 0

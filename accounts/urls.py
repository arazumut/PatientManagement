from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Ana Sayfa
    path('', views.home, name='home'),
    
    # Giriş ve Kayıt URL'leri
    path('dashboard/', views.dashboard, name='dashboard'),
    path('giris/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('cikis/', views.logout_view, name='logout'),
    path('kayit/', views.register, name='register'),
    
    # Profil Yönetimi
    path('profil/', views.profile, name='profile'),
    path('profil/duzenle/', views.edit_profile, name='edit_profile'),
    path('profil/doktor-olustur/', views.create_doctor_profile, name='create_doctor_profile'),
    
    # Parola İşlemleri
    path('parola/degistir/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), 
         name='password_change'),
    path('parola/degistir/basarili/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), 
         name='password_change_done'),
    path('parola/sifirla/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), 
         name='password_reset'),
    path('parola/sifirla/basarili/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),
    path('parola/sifirla/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('parola/sifirla/tamamlandi/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),
] 
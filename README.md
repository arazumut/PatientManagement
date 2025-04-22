# Hasta Yönetim Sistemi

Bu proje, klinik ve hastaneler için hasta randevu ve yönetim sistemidir.

## Özellikler

- Hasta kayıt ve profil yönetimi
- Doktor profil yönetimi 
- Randevu oluşturma ve takibi
- Tıbbi kayıt yönetimi
- Kullanıcı rollerine göre özelleştirilmiş paneller

## Kurulum

### 1. Projeyi İndirin
```bash
git clone <repo_url>
cd PatientManagement
```

### 2. Sanal Ortam Oluşturun ve Aktif Edin
```bash
python -m venv venv
```

#### Windows için:
```bash
venv\Scripts\activate
```

#### Mac/Linux için:
```bash
source venv/bin/activate
```

### 3. Gerekli Paketleri Kurun
```bash
pip install -r requirements.txt
```

### 4. Veritabanı Migrate İşlemlerini Gerçekleştirin
```bash
python manage.py migrate
```

### 5. Süper Kullanıcı Oluşturun
```bash
python manage.py createsuperuser
```

## Projeyi Çalıştırma

Projeyi geliştirme sunucusu üzerinde çalıştırmak için:

```bash
python manage.py runserver
```

Uygulama şu adreste çalışacaktır: http://127.0.0.1:8000/

## Kullanıcı Tipleri

Sistem üç farklı kullanıcı tipini destekler:

1. **Admin** - Sistem yöneticisi (Django admin ve özel admin paneli)
2. **Doktor** - Randevuları ve hastaları yönetir
3. **Hasta** - Randevuları ve tıbbi kayıtlarını görüntüler

## Temel URL'ler

- Ana Sayfa ve Dashboard: `/`
- Giriş: `/giris/`
- Kayıt: `/kayit/`
- Hasta İşlemleri: `/hastalar/`
- Randevu İşlemleri: `/randevular/`
- Doktor İşlemleri: `/doktorlar/`
- Admin Panel: `/admin/` 
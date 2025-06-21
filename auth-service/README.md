# Auth Service Mikroservisi

Bu mikroservis, kullanıcı kayıt ve giriş işlemleri ile JWT token doğrulama işlemlerini sağlar.

## Endpoints

- `POST /register`: Yeni bir kullanıcı kaydı yapar.
- `POST /login`: Mevcut kullanıcı girişi yapar.

## Kullanım

1. Docker imajını oluşturun:
   ```bash
   docker build -t auth-service .

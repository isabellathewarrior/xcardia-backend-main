# HSM Service

## Amaç
Bu servis, kullanıcı kimliğinin (user_id) gizliliğini korumak amacıyla, OpenAI gibi üçüncü parti servislere gerçek kullanıcı kimliği gönderilmeden önce şifreleme ve deşifreleme işlemlerini gerçekleştirir. Kullanıcı kimliği AES-GCM algoritması ile şifrelenerek sahte bir kimlik (pseudo_user_id) üretilir. Böylece, hassas veriler dış servislere aktarılmadan korunmuş olur.

## Kullanılan Kütüphaneler ve Modüller
- **FastAPI**: REST API oluşturmak için kullanılır.
- **cryptography**: AES-GCM algoritması ile şifreleme ve deşifreleme işlemleri için kullanılır.
  - **hazmat (Hazardous Materials)**: `cryptography` kütüphanesinin düşük seviyeli, doğrudan kriptografik işlemler için kullanılan modülüdür. Güvenli ve modern şifreleme algoritmalarını (ör. AES-GCM) doğrudan ve esnek şekilde kullanmaya olanak tanır. Bu modül, kriptografik işlemlerin güvenliğini ve doğruluğunu sağlamak için tercih edilir.
- **pydantic**: API veri modelleri için kullanılır.
- **uvicorn**: FastAPI uygulamasını çalıştırmak için kullanılır.

## Algoritma ve İşleyiş
- **AES-GCM**: Simetrik anahtarlı, modern ve güvenli bir şifreleme algoritmasıdır. Rastgele üretilen 12 baytlık bir nonce ile birlikte user_id şifrelenir ve base64 ile kodlanarak pseudo_user_id elde edilir.
- **Şifreleme**: `/api/encrypt` endpointine gelen user_id, AES-GCM ile şifrelenir ve pseudo_user_id olarak döner.
- **Deşifreleme**: `/api/decrypt` endpointine gelen pseudo_user_id, AES-GCM ile çözülerek orijinal user_id elde edilir.

## API Uçları
- `POST /api/encrypt`  
  - **Request:** `{ "user_id": "gercek_kullanici_id" }`
  - **Response:** `{ "pseudo_user_id": "sifrelenmis_id" }`
- `POST /api/decrypt`  
  - **Request:** `{ "pseudo_user_id": "sifrelenmis_id" }`
  - **Response:** `{ "user_id": "gercek_kullanici_id" }`

## Diğer Servislerle Entegrasyon
- **auth-service**: Kullanıcı sisteme kayıt olur ve kimlik doğrulama işlemleri burada yapılır.
- **doctor-service, pdf2jpg-service**: Normalde user_id ile çalışır. Ancak **OpenAI gibi dış servislere veri gönderileceği zaman** gerçek user_id, HSM Service ile şifrelenerek pseudo_user_id'ye dönüştürülür ve sadece bu sahte kimlik dış servislere gönderilir.
- **OpenAI gibi dış servisler**: Gerçek user_id hiçbir zaman dış servislere gönderilmez, sadece pseudo_user_id ile işlem yapılır.
- **Akış:**
  1. Kullanıcı sisteme kayıt olur, JWT token alır.
  2. Backend, OpenAI'ye veri göndermeden önce user_id'yi HSM Service'e gönderir ve şifrelenmiş pseudo_user_id alır.
  3. OpenAI'den dönen yanıtta pseudo_user_id varsa, backend tekrar HSM Service'e gönderip deşifre eder ve gerçek user_id'ye ulaşır.

## Servisin Çalıştırılması

### Docker ile
1. Ana dizinde (xcardia-backend-1-main) terminal açın.
2. Tüm servisleri başlatmak için:
   ```sh
   docker compose up --build
   ```
3. HSM Service'e Swagger arayüzünden ulaşmak için tarayıcıda:
   [http://localhost:8002/docs](http://localhost:8002/docs)

### Manuel (Geliştirici Modu)
1. Gerekli kütüphaneleri yükleyin:
   ```sh
   pip install -r requirements.txt
   ```
2. Servisi başlatın:
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Notlar
- AES anahtarı örnek olarak kodda sabit tutulmuştur. Gerçek ortamda güvenli bir şekilde saklanmalı ve yönetilmelidir (örn. environment variable veya secrets manager).
- Servis, sadece şifreleme ve deşifreleme işlemlerini yapar, kullanıcı yönetimi veya kimlik doğrulama işlemleri içermez. 
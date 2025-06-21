import requests
import json
import os
from datetime import datetime

# Servis URL'leri
AUTH_URL = "http://localhost:8000"
PDF2JPG_URL = "http://localhost:8001"
HSM_URL = "http://localhost:8002"
AI_URL = "http://localhost:8003"

def test_complete_flow():
    print("🚀 Xcardia Mikroservis Akış Testi Başlıyor...")
    print("=" * 50)
    
    # 1. Kullanıcı Kaydı
    print("1️⃣ Kullanıcı kaydı yapılıyor...")
    register_data = {
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com",
        "password": "test123456",
        "confirm_password": "test123456",
        "full_name": "Test User"
    }
    
    try:
        register_response = requests.post(f"{AUTH_URL}/register", json=register_data)
        if register_response.status_code == 200:
            print("✅ Kullanıcı kaydı başarılı")
        else:
            print(f"❌ Kullanıcı kaydı başarısız: {register_response.text}")
            return
    except Exception as e:
        print(f"❌ Kullanıcı kaydı hatası: {e}")
        return
    
    # 2. Kullanıcı Girişi
    print("2️⃣ Kullanıcı girişi yapılıyor...")
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }
    
    try:
        login_response = requests.post(f"{AUTH_URL}/login", data=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print("✅ Kullanıcı girişi başarılı")
            print(f"🔑 Token: {token[:20]}...")
        else:
            print(f"❌ Kullanıcı girişi başarısız: {login_response.text}")
            return
    except Exception as e:
        print(f"❌ Kullanıcı girişi hatası: {e}")
        return
    
    # 3. HSM Servisi Test
    print("3️⃣ HSM servisi test ediliyor...")
    headers = {"Authorization": f"Bearer {token}"}
    hsm_test_data = {"user_id": "12345"}
    
    try:
        hsm_response = requests.post(f"{HSM_URL}/encrypt", json=hsm_test_data, headers=headers)
        if hsm_response.status_code == 200:
            pseudo_id = hsm_response.json()["pseudo_user_id"]
            print(f"✅ HSM şifreleme başarılı: {pseudo_id}")
        else:
            print(f"❌ HSM şifreleme başarısız: {hsm_response.text}")
            return
    except Exception as e:
        print(f"❌ HSM servisi hatası: {e}")
        return
    
    # 4. PDF Yükleme ve Dönüştürme
    print("4️⃣ PDF yükleniyor ve dönüştürülüyor...")
    
    # Test PDF dosyası oluştur (eğer yoksa)
    test_pdf_path = "test_document.pdf"
    if not os.path.exists(test_pdf_path):
        print("📄 Test PDF dosyası oluşturuluyor...")
        # Basit bir PDF oluştur (gerçek projede bu dosya olacak)
        with open(test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF\n")
    
    try:
        with open(test_pdf_path, "rb") as pdf_file:
            files = {"file": ("test_document.pdf", pdf_file, "application/pdf")}
            headers = {"Authorization": f"Bearer {token}"}
            
            convert_response = requests.post(f"{PDF2JPG_URL}/convert/", files=files, headers=headers)
            
            if convert_response.status_code == 200:
                result = convert_response.json()
                print("✅ PDF dönüştürme başarılı")
                print(f"📸 Oluşturulan resimler: {len(result.get('images', []))}")
                if result.get('ai_evaluation'):
                    print("🤖 AI değerlendirmesi tamamlandı")
                else:
                    print("⚠️ AI değerlendirmesi yapılamadı")
            else:
                print(f"❌ PDF dönüştürme başarısız: {convert_response.status_code}")
                print(f"📄 Hata detayı: {convert_response.text}")
                return
    except Exception as e:
        print(f"❌ PDF dönüştürme hatası: {e}")
        return
    
    # 5. Logları Kontrol Et
    print("5️⃣ Dönüştürme logları kontrol ediliyor...")
    try:
        logs_response = requests.get(f"{PDF2JPG_URL}/logs/", headers=headers)
        if logs_response.status_code == 200:
            logs = logs_response.json()
            print(f"✅ {len(logs)} log kaydı bulundu")
            if logs:
                latest_log = logs[0]
                print(f"📝 Son dönüştürme: {latest_log.get('filename')} - {latest_log.get('converted_at')}")
        else:
            print(f"❌ Loglar alınamadı: {logs_response.text}")
    except Exception as e:
        print(f"❌ Log kontrolü hatası: {e}")
    
    print("=" * 50)
    print("🎉 Test tamamlandı!")
    print("\n📋 Test Sonuçları:")
    print(f"🔗 Auth Service: {AUTH_URL}/docs")
    print(f"🔗 PDF2JPG Service: {PDF2JPG_URL}/docs")
    print(f"🔗 HSM Service: {HSM_URL}/docs")
    print(f"🔗 AI Service: {AI_URL}/docs")

def test_pdf_upload():
    url = "http://localhost:8001/convert/"
    
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnaXplbUBleGFtcGxlLmNvbSIsInVzZXJfaWQiOjEwLCJleHAiOjE3NTA1MjY2ODR9.sYVxK-DxOz6knA1hXs2616Jk4ymcSFiMVz2ASwKyeDE'
    }
    
    files = {
        'file': ('IMG-20250514-WA0026.pdf', open('pdf2jpg-service/uploads/IMG-20250514-WA0026.pdf', 'rb'), 'application/pdf')
    }
    
    try:
        response = requests.post(url, headers=headers, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ PDF yükleme başarılı!")
        else:
            print("❌ PDF yükleme başarısız!")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    test_pdf_upload() 
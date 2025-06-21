import requests
import json

def test_auth_register():
    """Kullanıcı kaydı yap"""
    url = "http://localhost:8000/register"
    data = {
        "name": "Test",
        "surname": "User", 
        "email": "test@example.com",
        "phone_number": "1234567890",
        "password": "testpass123",
        "confirm_password": "testpass123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Register Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Kullanıcı kaydı başarılı")
            return response.json()["access_token"]
        else:
            print(f"❌ Kayıt hatası: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")
        return None

def test_auth_login():
    """Kullanıcı girişi yap"""
    url = "http://localhost:8000/login"
    data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Login başarılı")
            return response.json()["access_token"]
        else:
            print(f"❌ Login hatası: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login hatası: {e}")
        return None

def test_hsm_encrypt(token, user_id):
    """HSM servisi ile user_id şifrele"""
    url = "http://localhost:8002/encrypt"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"user_id": user_id}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"HSM Encrypt Status: {response.status_code}")
        print(f"HSM Encrypt Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Encrypted user_id: {result['pseudo_user_id']}")
            return result['pseudo_user_id']
        else:
            print(f"❌ HSM Encrypt Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ HSM Encrypt Exception: {e}")
        return None

def test_hsm_decrypt(token, pseudo_user_id):
    """HSM servisi ile pseudo_user_id çöz"""
    url = "http://localhost:8002/decrypt"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"pseudo_user_id": pseudo_user_id}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"HSM Decrypt Status: {response.status_code}")
        print(f"HSM Decrypt Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Decrypted user_id: {result['user_id']}")
            return result['user_id']
        else:
            print(f"❌ HSM Decrypt Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ HSM Decrypt Exception: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Mikroservis Entegrasyon Testi Başlıyor...")
    print("=" * 60)
    
    # 1. Kullanıcı kaydı veya girişi
    print("1️⃣ Kullanıcı girişi yapılıyor...")
    token = test_auth_login()
    if not token:
        print("Login başarısız, kayıt deneniyor...")
        token = test_auth_register()
    
    if not token:
        print("❌ Authentication başarısız!")
        exit(1)
    
    print(f"✅ Token alındı: {token[:50]}...")
    
    # 2. HSM Encrypt testi
    print("\n2️⃣ HSM Encrypt testi...")
    test_user_id = "123"
    encrypted = test_hsm_encrypt(token, test_user_id)
    
    if encrypted:
        print("\n3️⃣ HSM Decrypt testi...")
        decrypted = test_hsm_decrypt(token, encrypted)
        
        if decrypted == test_user_id:
            print("✅ HSM Service mükemmel çalışıyor!")
        else:
            print("❌ HSM Service decrypt hatası!")
    else:
        print("❌ HSM Service encrypt hatası!")
    
    print("\n" + "=" * 60)
    print("�� Test tamamlandı!") 
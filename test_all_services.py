import requests

services = {
    "Nginx Gateway": "http://localhost/gateway-status",
    "Face Service": "http://localhost/health/face",
    "Auth Service": "http://localhost/health/auth",
    "Attendance Service": "http://localhost/health/attendance",
    "Report Service": "http://localhost/health/report",
    "WhatsApp Service": "http://localhost/health/whatsapp"
}

print("\n" + "="*60)
print("🔍 EDUVISION SYSTEM HEALTH CHECK")
print("="*60)

for name, url in services.items():
    try:
        r = requests.get(url, timeout=5)
        status = "✅" if r.status_code == 200 else "❌"
        print(f"{status} {name:20} | {r.status_code}")
    except:
        print(f"❌ {name:20} | DOWN")

print("="*60)
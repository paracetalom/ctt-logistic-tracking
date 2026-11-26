import random
import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8080"
API_URL = f"{BASE_URL}/api/shipments"

# เข้าสู่ระบบในฐานะ shipping เพื่อรับ Bearer Token สำหรับสร้างพัสดุ
login_payload = json.dumps({"username": "shipping01", "password": "123456"}).encode("utf-8")
login_req = urllib.request.Request(
    f"{BASE_URL}/api/login",
    data=login_payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(login_req) as resp:
        token = json.loads(resp.read().decode("utf-8"))["token"]
        auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
except Exception as e:
    print(f"❌ Login ไม่สำเร็จ: {e}")
    auth_headers = {"Content-Type": "application/json"}

# ดึงรายการรถขนส่งเพื่อนำ id มาผูกกับพัสดุ
vehicles = []
try:
    with urllib.request.urlopen(f"{BASE_URL}/api/vehicles") as resp:
        vehicles = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"⚠️ ไม่สามารถดึงรายการรถได้: {e}")

senders = ["คลังสินค้าบางนา", "สาขาอ้อมน้อย", "ศูนย์กระจายสินค้ารังสิต", "บจก. สยามเทค", "ร้านค้าออนไลน์ A", "สาขาพระราม 2"]
receivers = ["คุณสมชาย ใจดี", "คุณสมหญิง รักเรียน", "คุณวิชัย มั่นคง", "คุณนภา สดใส", "คุณธนากร เจริญรุ่ง", "คุณกมลวรรณ สุขใจ", "คุณประเสริฐ ศรีสุข", "คุณอรุณี ทองดี"]
destinations = ["กรุงเทพฯ", "นครปฐม", "ชลบุรี", "เชียงใหม่", "ขอนแก่น", "ภูเก็ต", "นครราชสีมา", "สงขลา"]
statuses = ["รับเข้าระบบ", "กำลังจัดส่ง", "จัดส่งสำเร็จ"]

count = 30  # จำนวนรายการที่ต้องการสร้าง

for i in range(1, count + 1):
    tracking_no = f"CTT2026{random.randint(100, 999)}{i:02d}"
    chosen_vehicle = random.choice(vehicles)["id"] if vehicles else 1
    payload = {
        "tracking_no": tracking_no,
        "sender": random.choice(senders),
        "receiver": random.choice(receivers),
        "destination": random.choice(destinations),
        "vehicle_id": chosen_vehicle,
        "weight_kg": round(random.uniform(1.0, 15.0), 1),
        "receiver_phone": f"08{random.randint(10000000, 99999999)}"
    }
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            if res.status in (200, 201):
                # สุ่มอัปเดตสถานะให้หลากหลาย
                chosen_status = random.choice(statuses)
                if chosen_status != "รับเข้าระบบ":
                    put_payload = {
                        "status": chosen_status,
                        "location": f"จุดตรวจเช็ก {payload['destination']}",
                        "remark": f"อัปเดตสถานะ {chosen_status}"
                    }
                    put_req = urllib.request.Request(
                        f"{API_URL}/{tracking_no}",
                        data=json.dumps(put_payload).encode("utf-8"),
                        headers=auth_headers,
                        method="PUT"
                    )
                    urllib.request.urlopen(put_req)
                print(f"✅ สร้าง {tracking_no} -> {payload['destination']} ({chosen_status})")
    except Exception as e:
        print(f"❌ ข้าม {tracking_no}: {e}")

print("\n🎉 สร้างข้อมูลตัวอย่างเสร็จสมบูรณ์!")

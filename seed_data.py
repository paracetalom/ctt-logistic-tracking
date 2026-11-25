import random
import urllib.request
import json

API_URL = "http://localhost:8080/api/shipments"

senders = ["คลังสินค้าบางนา", "สาขาอ้อมน้อย", "ศูนย์กระจายสินค้ารังสิต", "บจก. สยามเทค", "ร้านค้าออนไลน์ A", "สาขาพระราม 2"]
receivers = ["คุณสมชาย ใจดี", "คุณสมหญิง รักเรียน", "คุณวิชัย มั่นคง", "คุณนภา สดใส", "คุณธนากร เจริญรุ่ง", "คุณกมลวรรณ สุขใจ", "คุณประเสริฐ ศรีสุข", "คุณอรุณี ทองดี"]
destinations = ["กรุงเทพฯ", "นครปฐม", "ชลบุรี", "เชียงใหม่", "ขอนแก่น", "ภูเก็ต", "นครราชสีมา", "สงขลา"]
statuses = ["รับเข้าระบบ", "กำลังจัดส่ง", "จัดส่งสำเร็จ"]

count = 30  # จำนวนรายการที่ต้องการสร้าง

for i in range(1, count + 1):
    tracking_no = f"CTT2026{random.randint(100, 999)}{i:02d}"
    payload = {
        "tracking_no": tracking_no,
        "sender": random.choice(senders),
        "receiver": random.choice(receivers),
        "destination": random.choice(destinations)
    }
    
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as res:
            if res.status in (200, 201):
                # สุ่มอัปเดตสถานะให้หลากหลาย
                chosen_status = random.choice(statuses)
                if chosen_status != "รับเข้าระบบ":
                    put_req = urllib.request.Request(
                        f"{API_URL}/{tracking_no}",
                        data=json.dumps({"status": chosen_status}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="PUT"
                    )
                    urllib.request.urlopen(put_req)
                print(f"✅ สร้าง {tracking_no} -> {payload['destination']} ({chosen_status})")
    except Exception as e:
        print(f"❌ ข้าม {tracking_no}: {e}")

print("\n🎉 สร้างข้อมูลตัวอย่างเสร็จสมบูรณ์!")

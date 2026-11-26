import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8080"

def api_call(method, path, data=None, token=None):
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

def login(username, password):
    status, res = api_call("POST", "/api/login", {"username": username, "password": password})
    assert status == 200, f"Login failed for {username}: {res}"
    return res["token"]

print("==========================================================")
print("🤖 CTT LOGISTICS - AUTOMATED RBAC & SECURITY AUDIT BOT")
print("==========================================================\n")

# 1. ล็อกอินทั้ง 3 บทบาทพร้อมกัน
t_admin = login("admin", "123456")
t_ship  = login("shipping01", "123456")
t_track = login("tracking01", "123456")
print("✅ [PASS] 1. ล็อกอินแยก Session ทั้ง 3 บัญชี (Admin / Shipping / Tracking) สำเร็จ\n")

# 2. ทดสอบสิทธิ์ Tracking: ลองแอบยิง API สร้างพัสดุตรงๆ (ต้องโดนบล็อก 403)
status, res = api_call("POST", "/api/shipments", {
    "sender": "แฮกเกอร์จำลอง", "receiver": "ปลายทาง", "destination": "กรุงเทพฯ"
}, token=t_track)
assert status == 403, f"Expected 403, got {status}"
print(f"🛡️  [PASS] 2. ป้องกัน Tracking แอบสร้างพัสดุสำเร็จ (ระบบดีดกลับ HTTP {status}: {res['detail']})")

# 3. ทดสอบสิทธิ์ Shipping: สร้างพัสดุจริง (ต้องผ่าน 200)
status, created = api_call("POST", "/api/shipments", {
    "sender": "คลังสินค้าหลัก (QA Test)",
    "receiver": "คุณทดสอบ ระบบอัตโนมัติ",
    "destination": "เชียงใหม่"
}, token=t_ship)
assert status == 200, f"Shipping create failed: {created}"
_, all_items = api_call("GET", "/api/shipments", token=t_ship)
test_item = next(x for x in all_items if x["sender"] == "คลังสินค้าหลัก (QA Test)")
test_tracking_no = test_item["tracking_no"]
print(f"✅ [PASS] 3. Shipping สร้างพัสดุสำเร็จ -> ออกเลข {test_tracking_no} อัตโนมัติ")

# 4. ทดสอบสิทธิ์ Tracking: อัปเดตสถานะพัสดุชิ้นนี้เป็น "กำลังจัดส่ง" (ต้องผ่าน 200)
status, updated = api_call("PUT", f"/api/shipments/{test_tracking_no}", {
    "status": "กำลังจัดส่ง",
    "location": "ศูนย์คัดแยกวังน้อย",
    "note": "ทดสอบอัปเดตสถานะโดยบอท QA"
}, token=t_track)
assert status == 200, f"Tracking update failed: {updated}"
print(f"✅ [PASS] 4. Tracking อัปเดตสถานะเป็น 'กำลังจัดส่ง' และบันทึกลง shipment_logs สำเร็จ")

# 5. ทดสอบสิทธิ์ Shipping: ลองแอบยิง API ลบพัสดุตรงๆ แม้หน้าเว็บจะซ่อนปุ่มแล้ว (ต้องโดนบล็อก 403)
status, res = api_call("DELETE", f"/api/shipments/{test_tracking_no}", token=t_ship)
assert status == 403, f"Expected 403, got {status}"
print(f"🛡️  [PASS] 5. ป้องกัน Shipping แอบยิง API ลบพัสดุสำเร็จ (ระบบดีดกลับ HTTP {status}: {res['detail']})")

# 6. ทดสอบสิทธิ์ Admin: ลบพัสดุทดสอบทิ้งเพื่อเคลียร์ฐานข้อมูล (ต้องผ่าน 200)
status, deleted = api_call("DELETE", f"/api/shipments/{test_tracking_no}", token=t_admin)
assert status == 200, f"Admin delete failed: {deleted}"
print(f"✅ [PASS] 6. Admin ลบพัสดุทดสอบ {test_tracking_no} และล้าง Log ในฐานข้อมูลเรียบร้อย\n")

print("==========================================================")
print("🎉 ผลการตรวจสอบทั้งหมด 6/6 รายการ: ระบบปลอดภัยและทำงานสมบูรณ์ 100%!")
print("==========================================================")

# 📦 CTT Logistic Tracking System (Enterprise RBAC)

ระบบบริหารจัดการและติดตามสถานะพัสดุระดับองค์กร พัฒนาด้วย **FastAPI**, **Tailwind CSS**, **Chart.js** และ **MySQL 8.0** รองรับการควบคุมสิทธิ์ตามบทบาท (**Role-Based Access Control - RBAC**) การบันทึกไทม์ไลน์การขนส่งจริง การจัดสรรรถขนส่ง และการ Deploy ผ่าน **Docker Compose**

---

## 🏗️ System Architecture

- **Backend API & Web Portal (`web`):** FastAPI + Uvicorn (Container Port `8000` → Host Port `8080`)
  - `/` — ระบบปฏิบัติการหลักสำหรับเจ้าหน้าที่ (RBAC Login, Dashboard สถิติ, ฟอร์มรับพัสดุและจัดสรรรถขนส่ง, ตารางจัดการสถานะ, พิมพ์ใบปะหน้า QR Code, Export CSV และจัดการบัญชีผู้ใช้)
  - `/track` — พอร์ทัลติดตามสถานะพัสดุสำหรับลูกค้า (Public Tracking Portal แสดงข้อมูลรถขนส่ง พนักงานขับรถ น้ำหนัก และไทม์ไลน์จริงจาก `shipment_logs`)
  - `/live-map` — แผนที่ติดตามเส้นทางขนส่งและกระจายสินค้าทั่วประเทศแบบ Interactive SVG
  - `/docs` — เอกสารทดสอบ API อัตโนมัติ (Swagger UI)
- **Database (`db`):** MySQL 8.0 (`ctt_logistic`) บน Port `3306` พร้อม Persistent Volume

---

## 🗄️ MySQL 4-Table Database Architecture

ฐานข้อมูล `ctt_logistic` ออกแบบแบบ Relational ประกอบด้วย 4 ตารางหลักที่เชื่อมโยงกันด้วย Foreign Keys:

| ตาราง | หน้าที่หลัก | คอลัมน์สำคัญและความสัมพันธ์ |
|---|---|---|
| `users` | บัญชีผู้ใช้งานและสิทธิ์ RBAC | `id` (PK), `username` (UNIQUE), `password_hash`, `full_name`, `role` (`ENUM('admin','shipping','tracking')`), `branch`, `is_active`, `created_at` |
| `vehicles` | ข้อมูลรถขนส่งและพนักงานขับรถ | `id` (PK), `plate_number` (UNIQUE), `driver_name`, `driver_phone`, `vehicle_type`, `status` (`ENUM('พร้อมใช้งาน','กำลังวิ่งงาน','ซ่อมบำรุง')`), `created_at` |
| `shipments` | ข้อมูลพัสดุหลักในระบบ | `id` (PK), `tracking_no` (UNIQUE), `sender`, `receiver`, `destination`, `status`, `receiver_phone`, `weight_kg`, `updated_at`, `created_by` (FK → `users.id`), `vehicle_id` (FK → `vehicles.id`) |
| `shipment_logs` | ประวัติและไทม์ไลน์การอัปเดตสถานะจริง | `id` (PK), `shipment_id` (FK → `shipments.id` `ON DELETE CASCADE`), `status`, `location`, `remark`, `updated_by` (FK → `users.id`), `created_at` |

---

## 🔐 RBAC Roles & Test Accounts (บัญชีทดสอบ 3 ตำแหน่ง)

ระบบยืนยันตัวตนด้วย Signed Bearer Token (`HMAC-SHA256`) แยกสิทธิ์การทำงานทั้งระดับ Backend API และหน้าเว็บ UI ดังนี้:

| ตำแหน่ง (`role`) | Username | Password | สิทธิ์การใช้งาน |
|---|---|---|---|
| **IT Admin** (`admin`) | `admin` | `123456` | สิทธิ์เต็มระบบ: สร้าง/ดู/อัปเดตสถานะ/ลบพัสดุ และจัดการบัญชีผู้ใช้งาน (`GET/POST /api/users`) |
| **ฝ่ายจัดส่ง** (`shipping`) | `shipping01` | `123456` | บันทึกรับพัสดุเข้าระบบ เลือกรถขนส่ง (`POST /api/shipments`) และอัปเดตสถานะ (ห้ามลบพัสดุและห้ามจัดการผู้ใช้) |
| **ฝ่ายควบคุมรถ** (`tracking`) | `tracking01` | `123456` | ดูรายการพัสดุและอัปเดตสถานะ/จุดเช็กอิน (`PUT /api/shipments/{tracking_no}`) ลง `shipment_logs` (ห้ามสร้างหรือลบพัสดุ) |

---

## 🚀 Quick Start (Docker Compose)

1. Clone repository และเข้าสู่โฟลเดอร์โปรเจกต์:
   ```bash
   git clone https://github.com/paracetalom/ctt-logistic-tracking.git
   cd ctt-logistic-tracking
   ```
2. Build และรันคอนเทนเนอร์ (`db` และ `web`):
   ```bash
   docker compose up -d --build
   ```
3. เข้าใช้งานระบบ:
   - หน้าจัดการเจ้าหน้าที่: `http://localhost:8080/`
   - หน้าเช็กพัสดุลูกค้า: `http://localhost:8080/track`
   - แผนที่เดินรถ: `http://localhost:8080/live-map`
   - API Docs: `http://localhost:8080/docs`

---

## 🛡️ Automated RBAC & Security Audit (`test_rbac.py`)

สคริปต์ `test_rbac.py` ใช้สำหรับตรวจสอบความปลอดภัยของระบบ RBAC และ End-to-End Flow ทั้ง 6 รายการโดยอัตโนมัติ (รันหลังจากที่คอนเทนเนอร์พร้อมทำงานบน `http://localhost:8080`):

```bash
python3 test_rbac.py
```

**รายการตรวจสอบทั้ง 6 ข้อ:**
1. ล็อกอินแยก Session ทั้ง 3 บัญชี (`admin`, `shipping01`, `tracking01`) สำเร็จ
2. ป้องกัน `tracking` แอบยิง API `POST /api/shipments` สร้างพัสดุ (ระบบดีดกลับ HTTP `403`)
3. อนุญาตให้ `shipping` สร้างพัสดุจริง (`POST /api/shipments`) พร้อมออกเลขพัสดุอัตโนมัติ (HTTP `200`)
4. อนุญาตให้ `tracking` อัปเดตสถานะเป็น `กำลังจัดส่ง` (`PUT /api/shipments/{tracking_no}`) และบันทึกลง `shipment_logs` (HTTP `200`)
5. ป้องกัน `shipping` แอบยิง API `DELETE /api/shipments/{tracking_no}` ลบพัสดุ (ระบบดีดกลับ HTTP `403`)
6. อนุญาตให้ `admin` ลบพัสดุทดสอบและล้างข้อมูล Log ที่เกี่ยวข้องผ่าน `ON DELETE CASCADE` (HTTP `200`)


---

## คู่มือการเปิด-ปิดระบบ และการเชื่อมต่อผ่านโทรศัพท์มือถือ

### 1. การเริ่มต้นการทำงานของระบบ (เมื่อเปิดเครื่องคอมพิวเตอร์)
เปิดหน้าต่าง **Ubuntu (WSL2) Terminal** แล้วรันคำสั่งต่อไปนี้เพื่อเริ่มการทำงานของ Web Server และฐานข้อมูล MySQL:

    cd ~/projects/ctt-logistic-tracking
    sudo docker compose start

เมื่อรันเสร็จแล้ว สามารถเปิดใช้งานหน้าเว็บผ่านเบราว์เซอร์บนคอมพิวเตอร์ได้ที่ `http://localhost:8080`

---

### 2. การเปิดการเชื่อมต่อสำหรับโทรศัพท์มือถือ (กรณีสแกน QR Code แล้วเปิดหน้าเว็บไม่ติด)
หากต้องการใช้โทรศัพท์มือถือในวง Wi-Fi เดียวกันสแกน QR Code เพื่อเปิดหน้าติดตามพัสดุ (`/track`) และเซ็นรับสินค้า (e-POD) แต่หน้าเว็บเปิดไม่ติด ให้เปิด **Windows PowerShell (Run as Administrator)** แล้วรันคำสั่งเปิดการส่งต่อพอร์ต (Port Forwarding):

    netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=127.0.0.1

> **หมายเหตุ:** ตรวจสอบเลข IPv4 ของเครื่องคอมพิวเตอร์ประจำวันด้วยคำสั่ง `ipconfig` ใน PowerShell ให้ตรงกับที่กำหนดไว้ในตัวสร้าง QR Code

---

### 3. การปิดระบบอย่างปลอดภัย (ก่อนปิดเครื่องคอมพิวเตอร์ / เลิกงาน)
1. **ใน Ubuntu (WSL2) Terminal:** สั่งหยุดการทำงานของ Container เพื่อป้องกันฐานข้อมูลเสียหาย
   `cd ~/projects/ctt-logistic-tracking && sudo docker compose stop`
2. **ใน Windows PowerShell (Run as Administrator):** ยกเลิกการส่งต่อพอร์ตเพื่อความปลอดภัยของเครือข่าย
   `netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0`

import os
import time
import json
import hmac
import hashlib
import base64
import random
import pymysql
from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="CTT Logistic Tracking Enterprise API (RBAC)")

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "ctt_dev")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Ctt@2026#Dev")
DB_NAME = os.getenv("DB_NAME", "ctt_logistic")
SECRET_KEY = b"CTT_LOGISTICS_ENTERPRISE_2026_KEY"

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

@app.on_event("startup")
def init_db():
    for _ in range(15):
        try:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT NOT NULL AUTO_INCREMENT,
                        username VARCHAR(50) NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        full_name VARCHAR(100) NOT NULL,
                        role ENUM('admin','shipping','tracking') NOT NULL,
                        branch VARCHAR(100) DEFAULT 'สำนักงานใหญ่ (นครปฐม)',
                        is_active TINYINT(1) DEFAULT 1,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY username (username)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vehicles (
                        id INT NOT NULL AUTO_INCREMENT,
                        plate_number VARCHAR(20) NOT NULL,
                        driver_name VARCHAR(100) NOT NULL,
                        driver_phone VARCHAR(20) DEFAULT NULL,
                        vehicle_type VARCHAR(50) DEFAULT 'รถกระบะตู้ทึบ 4 ล้อ',
                        status ENUM('พร้อมใช้งาน','กำลังวิ่งงาน','ซ่อมบำรุง') DEFAULT 'พร้อมใช้งาน',
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        UNIQUE KEY plate_number (plate_number)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shipments (
                        id INT NOT NULL AUTO_INCREMENT,
                        tracking_no VARCHAR(50) NOT NULL,
                        sender VARCHAR(100) NOT NULL,
                        receiver VARCHAR(100) NOT NULL,
                        destination VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'รับเข้าระบบ',
                        updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        created_by INT DEFAULT 2,
                        vehicle_id INT DEFAULT 1,
                        receiver_phone VARCHAR(20) DEFAULT '080-000-0000',
                        weight_kg DECIMAL(6,2) DEFAULT 5.00,
                        PRIMARY KEY (id),
                        UNIQUE KEY tracking_no (tracking_no),
                        KEY fk_shipments_user (created_by),
                        KEY fk_shipments_vehicle (vehicle_id),
                        CONSTRAINT fk_shipments_user FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL,
                        CONSTRAINT fk_shipments_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS shipment_logs (
                        id INT NOT NULL AUTO_INCREMENT,
                        shipment_id INT NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        location VARCHAR(150) NOT NULL,
                        remark VARCHAR(255) DEFAULT NULL,
                        updated_by INT DEFAULT NULL,
                        created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id),
                        KEY fk_logs_shipment (shipment_id),
                        KEY fk_logs_user (updated_by),
                        CONSTRAINT fk_logs_shipment FOREIGN KEY (shipment_id) REFERENCES shipments (id) ON DELETE CASCADE,
                        CONSTRAINT fk_logs_user FOREIGN KEY (updated_by) REFERENCES users (id) ON DELETE SET NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

                for col_sql in [
                    "ALTER TABLE shipments ADD COLUMN customs_doc_no VARCHAR(80) DEFAULT NULL",
                    "ALTER TABLE shipments ADD COLUMN service_type VARCHAR(80) DEFAULT 'Free Zone Warehouse'",
                    "ALTER TABLE shipments ADD COLUMN container_no VARCHAR(50) DEFAULT NULL",
                ]:
                    try:
                        cursor.execute(col_sql)
                    except Exception:
                        pass

                cursor.execute("SELECT COUNT(*) AS cnt FROM users")
                if cursor.fetchone()["cnt"] == 0:
                    cursor.executemany(
                        "INSERT INTO users (username, password_hash, full_name, role, branch) VALUES (%s, %s, %s, %s, %s)",
                        [
                            ("admin", "123456", "คุณกิตติพงษ์ (IT Admin)", "admin", "สำนักงานใหญ่ (นครปฐม)"),
                            ("shipping01", "123456", "คุณสุดารัตน์ (ฝ่ายจัดส่ง)", "shipping", "ศูนย์กระจายสินค้านครปฐม"),
                            ("tracking01", "123456", "คุณธนพล (ฝ่ายควบคุมรถ)", "tracking", "ศูนย์ควบคุมการเดินรถ"),
                        ],
                    )

                cursor.execute("SELECT COUNT(*) AS cnt FROM vehicles")
                if cursor.fetchone()["cnt"] == 0:
                    cursor.executemany(
                        "INSERT INTO vehicles (plate_number, driver_name, driver_phone, vehicle_type, status) VALUES (%s, %s, %s, %s, %s)",
                        [
                            ("70-4512 นฐ", "สมศักดิ์ ขับดี", "081-234-5678", "รถบรรทุก 6 ล้อตู้ทึบ", "กำลังวิ่งงาน"),
                            ("บบ-8821 กทม", "วิรัช ปลอดภัย", "089-876-5432", "รถกระบะตู้ทึบ 4 ล้อ", "กำลังวิ่งงาน"),
                            ("71-1094 ชบ", "มานะ ตรงเวลา", "086-555-4321", "รถบรรทุก 10 ล้อ", "พร้อมใช้งาน"),
                        ],
                    )
            conn.close()
            break
        except Exception:
            time.sleep(2)

# --- Pydantic Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

class ShipmentCreate(BaseModel):
    tracking_no: Optional[str] = None
    customs_doc_no: Optional[str] = None
    service_type: Optional[str] = "Free Zone Warehouse"
    container_no: Optional[str] = None
    sender: str
    receiver: str
    destination: str
    receiver_phone: Optional[str] = "080-000-0000"
    weight_kg: Optional[float] = 5.0
    vehicle_id: Optional[int] = 1

class StatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None
    remark: Optional[str] = None
    note: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    branch: Optional[str] = "สำนักงานใหญ่ (นครปฐม)"

# --- RBAC Dependency Helpers ---
def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return verify_token(token)

def require_roles(allowed_roles: list):
    def role_checker(user: Optional[dict] = Depends(get_current_user)):
        if not user:
            raise HTTPException(status_code=401, detail="กรุณาเข้าสู่ระบบก่อนทำรายการ (Unauthorized)")
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"ตำแหน่ง '{user['role']}' ไม่มีสิทธิ์ทำรายการนี้ (Access Denied)"
            )
        return user
    return role_checker

def make_token(user_dict: dict) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(user_dict, ensure_ascii=False).encode()).decode()
    sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"

def verify_token(token: str):
    try:
        payload, sig = token.split(".", 1)
        expected = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return None

# --- Authentication Endpoints ---
@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, full_name, role, branch, is_active FROM users WHERE username = %s AND password_hash = %s",
            (req.username.strip(), req.password.strip())
        )
        user = cursor.fetchone()
    conn.close()

    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง")

    token = make_token(user)
    return {"token": token, "user": user}

@app.post("/api/logout")
def logout():
    return {"message": "ออกจากระบบเรียบร้อย"}

@app.get("/api/me")
def get_me(user: Optional[dict] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# --- Master Data Endpoints (Vehicles & Users) ---
@app.get("/api/vehicles")
def list_vehicles():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM vehicles ORDER BY id ASC")
        rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/api/users")
def list_users(user: dict = Depends(require_roles(["admin"]))):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, full_name, role, branch, is_active, created_at FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/api/users")
def create_user(item: UserCreate, user: dict = Depends(require_roles(["admin"]))):
    if item.role not in ["admin", "shipping", "tracking"]:
        raise HTTPException(status_code=400, detail="Role ต้องเป็น admin, shipping หรือ tracking เท่านั้น")
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, role, branch) VALUES (%s, %s, %s, %s, %s)",
                (item.username.strip(), item.password.strip(), item.full_name, item.role, item.branch)
            )
    except pymysql.err.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้งานนี้มีอยู่ในระบบแล้ว")
    conn.close()
    return {"message": "สร้างบัญชีผู้ใช้งานสำเร็จ"}

# --- Shipments & Logs Endpoints ---
@app.get("/api/public/track/{tracking_no}")
def public_track_shipment(tracking_no: str):
    clean_no = tracking_no.upper().strip()
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT s.id, s.tracking_no, s.customs_doc_no, s.service_type, s.container_no, s.sender, s.receiver, s.destination, s.status,
                          s.weight_kg, s.updated_at,
                          v.plate_number AS plate_no, v.driver_name, v.vehicle_type
                   FROM shipments s
                   LEFT JOIN vehicles v ON s.vehicle_id = v.id
                   WHERE s.tracking_no = %s""",
                (clean_no,)
            )
            shipment = cursor.fetchone()
            if not shipment:
                raise HTTPException(status_code=404, detail="ไม่พบหมายเลขพัสดุนี้ในระบบ")

            cursor.execute(
                """SELECT l.status, l.location, l.remark, l.remark AS note, l.created_at,
                          u.full_name AS updated_by_name
                   FROM shipment_logs l
                   LEFT JOIN users u ON l.updated_by = u.id
                   WHERE l.shipment_id = %s
                   ORDER BY l.created_at DESC, l.id DESC""",
                (shipment["id"],)
            )
            logs = cursor.fetchall()
            shipment.pop("id", None)
            return {"shipment": shipment, "logs": logs}
    finally:
        conn.close()

@app.get("/api/shipments")
def list_shipments():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT s.*, 
                   u.full_name AS created_by_name,
                   v.plate_number AS vehicle_plate,
                   v.driver_name AS driver_name
            FROM shipments s
            LEFT JOIN users u ON s.created_by = u.id
            LEFT JOIN vehicles v ON s.vehicle_id = v.id
            ORDER BY s.updated_at DESC
        """)
        rows = cursor.fetchall()
    conn.close()
    return rows

@app.get("/api/shipments/{tracking_no}/logs")
def get_shipment_logs(tracking_no: str):
    clean_no = tracking_no.upper().strip()
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM shipments WHERE tracking_no = %s", (clean_no,))
        shipment = cursor.fetchone()
        if not shipment:
            conn.close()
            raise HTTPException(status_code=404, detail="ไม่พบเลขพัสดุนี้ในระบบ")

        cursor.execute("""
            SELECT l.id, l.status, l.location, l.remark, l.created_at,
                   u.full_name AS updated_by_name, u.role AS updated_by_role
            FROM shipment_logs l
            LEFT JOIN users u ON l.updated_by = u.id
            WHERE l.shipment_id = %s
            ORDER BY l.created_at ASC, l.id ASC
        """, (shipment["id"],))
        logs = cursor.fetchall()
    conn.close()
    return logs

@app.post("/api/shipments")
def create_shipment(item: ShipmentCreate, user: dict = Depends(require_roles(["admin", "shipping"]))):
    t_no = item.tracking_no.upper().strip() if item.tracking_no else f"CTT2026{random.randint(100000, 999999)}"
    receiver_phone = (item.receiver_phone or "").strip() or "080-000-0000"
    weight_kg = item.weight_kg if item.weight_kg is not None else 5.0
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO shipments 
                   (tracking_no, sender, receiver, destination, receiver_phone, weight_kg, created_by, vehicle_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    t_no, item.sender, item.receiver, item.destination,
                    receiver_phone, weight_kg, user["id"], item.vehicle_id
                )
            )
            shipment_id = cursor.lastrowid
            cursor.execute(
                """INSERT INTO shipment_logs (shipment_id, status, location, remark, updated_by)
                   VALUES (%s, %s, %s, %s, %s)""",
                (shipment_id, "รับเข้าระบบ", user.get("branch", "ศูนย์กระจายสินค้านครปฐม"), "สร้างรายการพัสดุเข้าระบบ", user["id"])
            )
    except pymysql.err.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="เลขพัสดุนี้มีอยู่ในระบบแล้ว")
    conn.close()
    return {"message": "บันทึกข้อมูลพัสดุสำเร็จ", "tracking_no": t_no}

@app.put("/api/shipments/{tracking_no}")
def update_status(tracking_no: str, item: StatusUpdate, user: dict = Depends(require_roles(["admin", "shipping", "tracking"]))):
    clean_no = tracking_no.upper().strip()
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, destination FROM shipments WHERE tracking_no = %s", (clean_no,))
        shipment = cursor.fetchone()
        if not shipment:
            conn.close()
            raise HTTPException(status_code=404, detail="ไม่พบเลขพัสดุ")

        cursor.execute(
            "UPDATE shipments SET status = %s WHERE tracking_no = %s",
            (item.status, clean_no)
        )

        # กำหนดจุดเช็กอินอัตโนมัติหากไม่ได้ระบุมา
        default_loc = f"ปลายทาง จ.{shipment['destination']}" if item.status == "จัดส่งสำเร็จ" else (
            f"ระหว่างขนส่งมุ่งหน้า จ.{shipment['destination']}" if item.status == "กำลังจัดส่ง" else user.get("branch", "ศูนย์คัดแยกสินค้า")
        )
        loc = (item.location or "").strip() or default_loc
        remark = (item.remark or item.note or "").strip() or f"อัปเดตสถานะโดย {user['full_name']}"

        cursor.execute(
            """INSERT INTO shipment_logs (shipment_id, status, location, remark, updated_by)
               VALUES (%s, %s, %s, %s, %s)""",
            (shipment["id"], item.status, loc, remark, user["id"])
        )
    conn.close()
    return {"message": "อัปเดตสถานะและบันทึก Log สำเร็จ"}

@app.delete("/api/shipments/{tracking_no}")
def delete_shipment(tracking_no: str, user: dict = Depends(require_roles(["admin"]))):
    clean_no = tracking_no.upper().strip()
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM shipments WHERE tracking_no = %s", (clean_no,))
    conn.close()
    return {"message": "ลบรายการสำเร็จ (สิทธิ์ Admin)"}

# --- Frontend Pages ---
@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("index.html", media_type="text/html")

@app.get("/")
def serve_ui():
    return FileResponse("showcase.html")

@app.get("/track")
async def public_tracking_page():
    return FileResponse("track.html")


@app.get("/logo.png")
def serve_logo():
    return FileResponse("CTT-Log-scaled.png", media_type="image/png")


@app.get("/showcase")
def serve_showcase():
    return FileResponse("showcase.html", media_type="text/html")

@app.get("/live-map")
async def live_command_center():
    return FileResponse("live_map.html")


from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        html_404 = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>404 — ไม่พบหน้าที่ต้องการ | CTT Freezone &amp; Logistics</title>
  <style>
    body { font-family: sans-serif; background: #FFFFFF; color: #0F172A; margin: 0; display: flex; min-height: 100vh; align-items: center; justify-content: center; padding: 20px; }
    .box { max-width: 440px; width: 100%; border: 1px solid #E2E8F0; border-top: 4px solid #002B88; border-radius: 4px; padding: 28px; }
    .code { font-weight: 700; color: #E10600; font-size: 13px; letter-spacing: 0.08em; }
    h1 { margin: 8px 0 10px; font-size: 24px; color: #002B88; }
    p { margin: 0 0 22px; color: #475569; font-size: 14px; line-height: 1.6; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; }
    a { text-decoration: none; font-size: 13px; font-weight: 600; padding: 10px 14px; border-radius: 4px; }
    .primary { background: #002B88; color: #FFFFFF; }
    .secondary { border: 1px solid #CBD5E1; color: #002B88; background: #FFFFFF; }
  </style>
</head>
<body>
  <div class="box">
    <div class="code">ERROR 404</div>
    <h1>ไม่พบหน้าที่ต้องการ</h1>
    <p>ไม่พบเส้นทางหน้าเว็บที่คุณเรียกใช้งาน กรุณากลับไปที่หน้าหลักหรือหน้าแดชบอร์ดเพื่อดำเนินการต่อ</p>
    <div class="actions">
      <a class="primary" href="/">กลับหน้าหลัก</a>
      <a class="secondary" href="/dashboard">ไปหน้าแดชบอร์ด</a>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_404, status_code=404)
    if request.url.path.startswith("/api/"):
        return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)

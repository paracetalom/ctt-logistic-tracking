import os
import time
import secrets
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

# เก็บ Active Session Token ชั่วคราวใน Memory (map token -> user dict)
ACTIVE_SESSIONS = {}

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
                cursor.execute("SELECT 1")
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

import hmac, hashlib, base64, json
SECRET_KEY = b"CTT_LOGISTICS_ENTERPRISE_2026_KEY"

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
def logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        ACTIVE_SESSIONS.pop(token, None)
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
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id FROM shipments WHERE tracking_no = %s", (tracking_no.upper(),))
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
    import random
    t_no = item.tracking_no.upper().strip() if item.tracking_no else f"CTT2026{random.randint(100000, 999999)}"
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO shipments 
                   (tracking_no, sender, receiver, destination, receiver_phone, weight_kg, created_by, vehicle_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    t_no, item.sender, item.receiver, item.destination,
                    item.receiver_phone, item.weight_kg, user["id"], item.vehicle_id
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
    return {"message": "บันทึกข้อมูลพัสดุสำเร็จ"}

@app.put("/api/shipments/{tracking_no}")
def update_status(tracking_no: str, item: StatusUpdate, user: dict = Depends(require_roles(["admin", "shipping", "tracking"]))):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, destination FROM shipments WHERE tracking_no = %s", (tracking_no.upper(),))
        shipment = cursor.fetchone()
        if not shipment:
            conn.close()
            raise HTTPException(status_code=404, detail="ไม่พบเลขพัสดุ")

        cursor.execute(
            "UPDATE shipments SET status = %s WHERE tracking_no = %s",
            (item.status, tracking_no.upper())
        )

        # กำหนดจุดเช็กอินอัตโนมัติหากไม่ได้ระบุมา
        default_loc = f"ปลายทาง จ.{shipment['destination']}" if item.status == "จัดส่งสำเร็จ" else (
            f"ระหว่างขนส่งมุ่งหน้า จ.{shipment['destination']}" if item.status == "กำลังจัดส่ง" else user.get("branch", "ศูนย์คัดแยกสินค้า")
        )
        loc = item.location if item.location else default_loc
        remark = item.remark if item.remark else f"อัปเดตสถานะโดย {user['full_name']}"

        cursor.execute(
            """INSERT INTO shipment_logs (shipment_id, status, location, remark, updated_by)
               VALUES (%s, %s, %s, %s, %s)""",
            (shipment["id"], item.status, loc, remark, user["id"])
        )
    conn.close()
    return {"message": "อัปเดตสถานะและบันทึก Log สำเร็จ"}

@app.delete("/api/shipments/{tracking_no}")
def delete_shipment(tracking_no: str, user: dict = Depends(require_roles(["admin"]))):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM shipments WHERE tracking_no = %s", (tracking_no.upper(),))
    conn.close()
    return {"message": "ลบรายการสำเร็จ (สิทธิ์ Admin)"}

# --- Frontend Pages ---
@app.get("/")
def serve_ui():
    return FileResponse("index.html")

@app.get("/track")
async def public_tracking_page():
    return FileResponse("track.html")

@app.get("/live-map")
async def live_command_center():
    return FileResponse("live_map.html")

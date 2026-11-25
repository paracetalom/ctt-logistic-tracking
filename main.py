import os
import time
import pymysql
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="CTT Logistic Tracking API")

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "ctt_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ctt_pass123")
DB_NAME = os.getenv("DB_NAME", "ctt_logistic")

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
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
                    CREATE TABLE IF NOT EXISTS shipments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        tracking_no VARCHAR(50) UNIQUE NOT NULL,
                        sender VARCHAR(100) NOT NULL,
                        receiver VARCHAR(100) NOT NULL,
                        destination VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'รับเข้าระบบ',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
            conn.close()
            break
        except Exception:
            time.sleep(2)

class ShipmentCreate(BaseModel):
    tracking_no: str
    sender: str
    receiver: str
    destination: str

class StatusUpdate(BaseModel):
    status: str

@app.get("/")
def serve_ui():
    return FileResponse("index.html")

@app.get("/api/shipments")
def list_shipments():
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM shipments ORDER BY updated_at DESC")
        rows = cursor.fetchall()
    conn.close()
    return rows

@app.post("/api/shipments")
def create_shipment(item: ShipmentCreate):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO shipments (tracking_no, sender, receiver, destination) VALUES (%s, %s, %s, %s)",
                (item.tracking_no.upper(), item.sender, item.receiver, item.destination)
            )
    except pymysql.err.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="เลขพัสดุนี้มีอยู่ในระบบแล้ว")
    conn.close()
    return {"message": "บันทึกสำเร็จ"}

@app.put("/api/shipments/{tracking_no}")
def update_status(tracking_no: str, item: StatusUpdate):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE shipments SET status = %s WHERE tracking_no = %s",
            (item.status, tracking_no.upper())
        )
    conn.close()
    return {"message": "อัปเดตสถานะสำเร็จ"}

@app.delete("/api/shipments/{tracking_no}")
def delete_shipment(tracking_no: str):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM shipments WHERE tracking_no = %s", (tracking_no.upper(),))
    conn.close()
    return {"message": "ลบรายการสำเร็จ"}

from fastapi.responses import FileResponse

@app.get("/track")
async def public_tracking_page():
    return FileResponse("track.html")

@app.get("/live-map")
async def live_command_center():
    return FileResponse("live_map.html")

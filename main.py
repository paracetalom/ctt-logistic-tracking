import os
import sqlite3
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="CTT Logistic Tracking API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("DB_PATH", "ctt_logistic.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_no TEXT UNIQUE NOT NULL,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                destination TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'รับเข้าระบบ',
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


class ShipmentCreate(BaseModel):
    tracking_no: str
    sender: str
    receiver: str
    destination: str
    status: Optional[str] = "รับเข้าระบบ"


class StatusUpdate(BaseModel):
    status: str


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


@app.get("/api/shipments")
def list_shipments(q: Optional[str] = None):
    with get_db() as conn:
        if q:
            keyword = f"%{q}%"
            rows = conn.execute(
                """SELECT * FROM shipments 
                   WHERE tracking_no LIKE ? OR receiver LIKE ? OR destination LIKE ?
                   ORDER BY id DESC""",
                (keyword, keyword, keyword),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM shipments ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.post("/api/shipments")
def create_shipment(item: ShipmentCreate):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO shipments (tracking_no, sender, receiver, destination, status, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (item.tracking_no.strip().upper(), item.sender, item.receiver, item.destination, item.status, now),
            )
            conn.commit()
        return {"message": "บันทึกข้อมูลพัสดุสำเร็จ", "tracking_no": item.tracking_no.upper()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="เลขพัสดุนี้มีอยู่ในระบบแล้ว")


@app.put("/api/shipments/{tracking_no}")
def update_status(tracking_no: str, data: StatusUpdate):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE shipments SET status = ?, updated_at = ? WHERE tracking_no = ?",
            (data.status, now, tracking_no.upper()),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบเลขพัสดุในระบบ")
    return {"message": "อัปเดตสถานะเรียบร้อย"}


@app.delete("/api/shipments/{tracking_no}")
def delete_shipment(tracking_no: str):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM shipments WHERE tracking_no = ?", (tracking_no.upper(),))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบเลขพัสดุในระบบ")
    return {"message": "ลบรายการเรียบร้อย"}
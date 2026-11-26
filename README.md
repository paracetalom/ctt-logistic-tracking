# 📦 CTT Logistic Tracking System

ระบบบริหารจัดการและติดตามสถานะพัสดุภายในองค์กร พัฒนาด้วย **FastAPI**, **Tailwind CSS** และ **MySQL 8.0** พร้อมโครงสร้างการ Deploy ผ่าน **Docker Compose** และ **IIS Reverse Proxy**

## 🏗️ System Architecture
- **Frontend & API:** FastAPI + Tailwind CSS (Docker Port 8080)
- **Database:** MySQL 8.0 พร้อม Docker Volume เก็บข้อมูลถาวร (Port 3306)
- **Web Server / Proxy:** IIS Reverse Proxy รับหน้าด่านที่ Port 80

## ✨ Key Features
- **Dashboard & Real-time Tracking:** สรุปยอดพัสดุทั้งหมด กำลังจัดส่ง และจัดส่งสำเร็จ พร้อมระบบค้นหาทันที
- **Full CRUD Operations:** บันทึกรับพัสดุ อัปเดตสถานะการจัดส่ง และลบรายการ
- **Shipping Label Print & CSV Export:** สั่งพิมพ์ใบปะหน้าพัสดุและดาวน์โหลดรายงานข้อมูลเป็นไฟล์ CSV (รองรับภาษาไทยใน Excel)
- **Auto API Documentation:** เข้าถึงหน้าทดสอบ API อัตโนมัติได้ที่ `/docs`

## 🚀 Quick Start (Docker Compose)
1. Clone repository: `git clone [https://github.com/paracetalom/ctt-logistic-tracking.git](https://github.com/paracetalom/ctt-logistic-tracking.git)`
2. เข้าโฟลเดอร์: `cd ctt-logistic-tracking`
3. รันระบบ: `docker compose up -d --build`

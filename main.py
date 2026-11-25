import os
import time
import pymysql
from fastapi import FastAPI, HTTPException

from fastapi.responses import FileResponse

@app.get("/track")
async def public_tracking_page():
    return FileResponse("track.html")

@app.get("/live-map")
async def live_command_center():
    return FileResponse("live_map.html")

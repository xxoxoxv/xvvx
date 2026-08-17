"""
Main FastAPI Application for AMOS Web Interface
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Optional
import os


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="AMOS Federal State",
        description="Administrative Dashboard and Citizen Portal",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import routes
    from .routes import router
    app.include_router(router, prefix="/api")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "amos-web-interface",
            "version": "1.0.0"
        }
    
    # Root endpoint - serve admin dashboard
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return get_admin_dashboard_html()
    
    # Citizen portal
    @app.get("/citizen", response_class=HTMLResponse)
    async def citizen_portal():
        return get_citizen_portal_html()
    
    # Task management
    @app.get("/tasks", response_class=HTMLResponse)
    async def task_manager():
        return get_task_manager_html()
    
    # System monitoring
    @app.get("/monitor", response_class=HTMLResponse)
    async def system_monitor():
        return get_system_monitor_html()
    
    return app


def get_admin_dashboard_html() -> str:
    """Return admin dashboard HTML"""
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMOS - لوحة التحكم الإدارية</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: white; border-radius: 10px; padding: 30px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header h1 { color: #667eea; margin-bottom: 10px; }
        .header p { color: #666; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 10px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 10px; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #667eea; }
        .stat-card .change { color: #48bb78; font-size: 14px; margin-top: 5px; }
        .section { background: white; border-radius: 10px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .section h2 { color: #333; margin-bottom: 20px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: right; border-bottom: 1px solid #eee; }
        th { background: #f7fafc; color: #666; font-weight: 600; }
        tr:hover { background: #f7fafc; }
        .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .badge-success { background: #c6f6d5; color: #22543d; }
        .badge-warning { background: #feebc8; color: #744210; }
        .badge-info { background: #bee3f8; color: #2c5282; }
        .btn { padding: 8px 16px; border: none; border-radius: 5px; cursor: pointer; font-weight: 600; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ الدولة الفدرالية AMOS</h1>
            <p>لوحة التحكم الإدارية - السيادي: zoorooz (KING-001)</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>المواطنين المسجلين</h3>
                <div class="value">1</div>
                <div class="change">+1 هذا الأسبوع</div>
            </div>
            <div class="stat-card">
                <h3>المؤسسات النشطة</h3>
                <div class="value">12</div>
                <div class="change">+3 هذا الشهر</div>
            </div>
            <div class="stat-card">
                <h3>المهام المنفذة</h3>
                <div class="value">24</div>
                <div class="change">95% نجاح</div>
            </div>
            <div class="stat-card">
                <h3>الوكلاء النشطين</h3>
                <div class="value">8</div>
                <div class="change">جميعهم نشطين</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 آخر المهام</h2>
            <table>
                <thead>
                    <tr>
                        <th>المعرف</th>
                        <th>النوع</th>
                        <th>الحالة</th>
                        <th>الوكيل</th>
                        <th>التاريخ</th>
                        <th>الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>TASK-001</td>
                        <td>تشريعي</td>
                        <td><span class="badge badge-success">مكتمل</span></td>
                        <td>Coordinator-National</td>
                        <td>2024-01-15</td>
                        <td><button class="btn btn-primary">عرض</button></td>
                    </tr>
                    <tr>
                        <td>TASK-002</td>
                        <td>تنفيذي</td>
                        <td><span class="badge badge-warning">قيد التنفيذ</span></td>
                        <td>Worker-Legislative</td>
                        <td>2024-01-15</td>
                        <td><button class="btn btn-primary">عرض</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🏢 المؤسسات الفدرالية</h2>
            <table>
                <thead>
                    <tr>
                        <th>المؤسسة</th>
                        <th>النوع</th>
                        <th>الرئيس</th>
                        <th>الحالة</th>
                        <th>الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>البرلمان الفدرالي</td>
                        <td>تشريعي</td>
                        <td>zoorooz</td>
                        <td><span class="badge badge-success">نشط</span></td>
                        <td><button class="btn btn-primary">إدارة</button></td>
                    </tr>
                    <tr>
                        <td>المحكمة العليا</td>
                        <td>قضائي</td>
                        <td>zoorooz</td>
                        <td><span class="badge badge-success">نشط</span></td>
                        <td><button class="btn btn-primary">إدارة</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
    """


def get_citizen_portal_html() -> str:
    """Return citizen portal HTML"""
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMOS - بوابة المواطنين</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f7fafc; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; padding: 40px; margin-bottom: 30px; text-align: center; }
        .card { background: white; border-radius: 10px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ بوابة المواطنين الفدرالية</h1>
            <p>مرحباً بك في النظام الفدرالي AMOS</p>
        </div>
        <div class="card">
            <h2>خدمات المواطنين</h2>
            <p>سجل طلباتك وتابع معاملاتك الحكومية</p>
        </div>
    </div>
</body>
</html>
    """


def get_task_manager_html() -> str:
    """Return task manager HTML"""
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>AMOS - إدارة المهام</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f7fafc; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 نظام إدارة المهام</h1>
        <p>متابعة وتنفيذ المهام الفدرالية</p>
    </div>
</body>
</html>
    """


def get_system_monitor_html() -> str:
    """Return system monitor HTML"""
    return """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>AMOS - مراقبة النظام</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f7fafc; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 مراقبة النظام</h1>
        <p>صحة وأداء مكونات النظام الفدرالي</p>
    </div>
</body>
</html>
    """

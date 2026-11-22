# 🚦 Smart Traffic Incident & Road Safety Management System (TrafficSafe)

[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Leaflet](https://img.shields.io/badge/Leaflet-GIS_Mapping-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-1.5_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An enterprise-grade, human-crafted **Municipal Traffic Command & Road Incident Surveillance Platform** built with Django, Leaflet GIS spatial mapping, Chart.js telemetry dashboards, and Google Gemini AI forensics assistant. 

Designed for traffic enforcement authorities, emergency response teams, urban planners, and citizen reporters to log accidents, track congestion corridors, broadcast advisories, and analyze accident hotspots in real time.

---

## 🌟 Key Features

### 1. 🗺️ Interactive City GIS Surveillance Map
- **Dual-Layer Basemap Support**: Seamlessly toggle between **ArcGIS World Street Map** and **ArcGIS World Imagery (Satellite)**.
- **Dynamic Pin Classification**: Junction markers color-coded by real-time safety status (High Risk, Heavy Jam, Moderate Flow, Normal).
- **Interactive Spatial Popups**: View casualties, average speeds, active advisories, and jump straight to location incident logs with one click.

### 2. 🚨 Road Incident Registry & Citizen Reporting
- **Multi-Level Classification**: Report incidents categorized by severity (Minor, Major, Fatal) and lifecycle status (Reported, Under Review, Resolved).
- **Field Telemetry Logging**: Capture involved vehicles, casualties, timestamp (IST), and exact coordinates.
- **Smart Filtering & 'My Submissions'**: Instant filter pills for status, severity, zones, and individual user report logs.
- **CSV Data Export**: One-click filtered CSV exports with UTF-8 BOM encoding for seamless Excel compatibility.

### 3. 📊 Analytics Command Dashboard
- **Dynamic Time Horizons**: Switch between 7 Days, 14 Days, and 30 Days with reactive Chart.js visual updates.
- **Rich Metric Visualizations**:
  - Daily accident trajectories and trends.
  - Severity distribution breakdown (Minor vs Major vs Fatal).
  - 24-hour diurnal congestion curves (Peak morning/evening analysis).
  - Real-time corridor speed tracking.
- **Automated Hotspot Risk Matrix**: Weighted scoring model based on collision severity, frequency, and sustained bottleneck levels.

### 4. 🤖 AI Assistant Copilot (Google Gemini 1.5 Flash)
- **Accident Forensic Audit**: One-click causal diagnosis and civil intervention roadmap for every reported incident.
- **Interactive Traffic Intelligence Modal**: Ask natural language strategic questions (e.g., *"How to mitigate evening peak congestion at Mall Road?"*).
- **Zero Heavy Dependencies**: Built using a lightweight, native REST client with secure environment key fallback.

### 5. 👥 Role-Based Authentication & Civic Directory
- **Custom Citizen Registration & Login**: Streamlined registration with instant session creation and password strength validation.
- **Emergency Helpline Directory Modal**: Instant directory modal for Traffic Police (103), Emergency (112), Ambulance (108), and Highway Helpline (1033).
- **Live Advisory Broadcasts**: Staff-curated public emergency alerts with unread badge indicators in the top navigation bar.

---

## 🏗️ Architecture & Tech Stack

`	ext
├── traffic_system/             # Django core configuration & routing
│   ├── settings.py             # Settings, apps, and Gemini configuration
│   ├── urls.py                 # Global routing
│   └── wsgi.py                 # WSGI web server gateway
├── management_app/             # Core Civic Application
│   ├── models.py               # Location, Accident, CongestionReport, Alert, Profile
│   ├── views.py                # Business logic, query filters, API endpoints
│   ├── forms.py                # Authentication, Registration & Incident forms
│   ├── analytics.py            # Summary statistics & Hotspot ranking engine
│   ├── gemini_service.py       # REST integration for Google Gemini AI
│   ├── templates/              # Semantic, responsive HTML5 templates
│   └── management/commands/    # Automated demo data seeder
└── static/                     # Design system assets (CSS, JS, Leaflet)
`

- **Backend**: Python 3.10+, Django 4.2+ (tested up to Django 6.1)
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Frontend**: HTML5, Modern CSS Design System, Bootstrap 5.3, Vanilla JavaScript
- **Mapping**: Leaflet.js with ArcGIS World Street & Satellite tile servers
- **Visualizations**: Chart.js 4.4
- **AI Engine**: Google Gemini 1.5 Flash (REST API)

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
`ash
git clone https://github.com/MarutiNandan2796/smart-traffic-incident-management.git
cd smart-traffic-incident-management
`

### 2. Create and Activate Virtual Environment
`ash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
`

### 3. Install Dependencies
`ash
pip install -r requirements.txt
`

### 4. Configure Environment Variables (Optional)
Copy .env.example to .env and add your Google Gemini API key:
`ash
cp .env.example .env
`
*(You can obtain a free API key at [Google AI Studio](https://aistudio.google.com/app/apikey))*.

### 5. Run Migrations & Seed Sample Data
`ash
python manage.py migrate
python manage.py seed_data
`
The seeder automatically initializes 10 city junctions, historical accidents, congestion telemetry, emergency alerts, and pre-configured accounts.

### 6. Start the Development Server
`ash
python manage.py runserver
`
Visit **http://127.0.0.1:8000/** in your browser.

---

## 🔑 Default Credentials

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Command Officer** | dmin | dmin123 | Full Administrative & Broadcast Access |
| **Citizen Reporter** | demo | demo12345 | Standard Incident Reporting & Telemetry |

*You can also register your own personal account directly via /register/.*

---

## 🧪 Testing & Quality Assurance

Run the comprehensive 16-test automated suite:
`ash
python manage.py test
`
All tests verify authentication, user registration, report persistence, RBAC permissions, and spatial telemetry endpoints.

---

## 📄 License
This project is open-source and licensed under the [MIT License](LICENSE).

# 🎉 Event Space Management System - Backend

[![Built with Django](https://img.shields.io/badge/Django-4.2+-green?logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/licenses/MIT)

A robust and scalable Django REST API for managing **event spaces**, handling **booking workflows**, and enabling **admin approvals** with real-time availability tracking.

Developed by a team of attachees 💼 to enhance efficiency, transparency, and control in venue reservations.

## 🚀 Features

- 🔐 JWT Authentication (Login, Register, Profile)
- 🏢 Space Management (CRUD, Features, Equipment)
- 📅 Booking System (Requests, Conflicts, Status)
- ✅ Admin Approval Workflow
- 📆 Calendar View Integration
- ✉️ Notifications (Email Ready)
- 📊 Dashboard APIs (Stats, Recent Bookings)
- ⚙️ Role-Based Access (Admin, Staff, External)

---

## 🏗️ Tech Stack

| Layer        | Technology       |
|--------------|------------------|
| Backend      | Django, Django REST Framework |
| Database     | PostgreSQL       |
| Auth         | JWT (SimpleJWT)  |
| Dev Tools    | Railway  |
| Calendar     | FullCalendar.js *(Frontend)* |
| Frontend     | React (Separate Repo)        |

---

## 📁 Project Structure

```bash
eventspace-api/
├── apps/
│   ├── authentication/
│   ├── bookings/
│   ├── spaces/
│   └── notifications/
├── core/
├── manage.py
├── Procfile
└── requirements.txt
```

## 🚂 Railway Deployment

This application is configured for automatic deployment on Railway.app platform.

### Automatic Migrations

When deployed on Railway, the application automatically handles database migrations in a specific order to avoid dependency issues:

1. First, `contenttypes` migrations are applied
2. Then, `authentication` app migrations for the custom user model
3. Finally, all remaining migrations are applied
4. This order ensures that the custom user model is available before other models that depend on it

To deploy to Railway:

1. Connect your repository to Railway
2. Add PostgreSQL plugin
3. Set the following environment variables:
   - `RAILWAY_ENVIRONMENT=production` 
   - `DEBUG=False`
   - `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, and `PGPORT` (set by Railway automatically)
   - Other required environment variables from `.env`
4. The deployment process will:
   - Execute the `railway_entrypoint.sh` script
   - Run migrations in the correct order
   - Start the Gunicorn server
5. No manual shell commands needed - everything is automated!

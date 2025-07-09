# 🎉 Event Space Management System - Backend

[![Built with Django](https://img.shields.io/badge/Django-4.2+-green?logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/licenses/MIT)

A robust and scalable Django REST API for managing **event spaces**, handling **booking workflows**, and enabling **admin approvals** with real-time availability tracking.

Developed by a team of attachees 💼 to enhance efficiency, transparency, and control in venue reservations.

---

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
└── requirements.txt

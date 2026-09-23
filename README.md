# Job Application & Analytics Management System

A web-based application to track job applications, manage application status, and analyze job search progress.

## Features

- User registration and login
- Secure password hashing and session-based authentication
- Add, edit, delete, and view job applications
- Search applications by company or role
- Filter applications by status
- Dashboard with application statistics
- Application analytics using Pandas
- Charts for application status, roles, companies, and monthly applications
- REST API for application CRUD operations
- CSV export of application data
- MySQL database integration

## Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- MySQL
- Pandas
- HTML
- CSS
- JavaScript
- REST API
- JSON
- Git & GitHub

## Project Structure

```text
JOB-APPLICATION-SYSTEM/
├── app.py
├── requirements.txt
├── api_test.http
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── applications.html
│   ├── add_application.html
│   ├── edit_application.html
│   └── dashboard.html
├── static/
├── .gitignore
└── .env
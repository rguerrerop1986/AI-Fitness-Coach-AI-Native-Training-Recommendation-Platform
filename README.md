
# Fitness Coach App

A comprehensive web application for fitness & nutrition coaches to manage clients, assign diet and workout plans, and track progress.

## Features

- **Client Management**: CRUD operations for clients with body measurements tracking
- **Catalogs**: Food and exercise databases with nutritional and workout information
- **Plans & Assignments**: Diet and workout plan creation with client assignment
- **Progress Tracking**: Weekly check-ins with trend analysis and charts
- **Notifications**: Email reminders for check-ins
- **Reports**: Dashboard with client progress and adherence metrics
- **Client Portal**: Secure client access to assigned plans with PDF download capability

## Tech Stack

- **Backend**: Python 3.12, Django 5, Django REST Framework
- **Authentication**: Django auth + JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL
- **Frontend**: React + TypeScript + Vite, TailwindCSS, React Router
- **Packaging**: Docker + docker-compose, Poetry
- **Testing**: Pytest + DRF test client, React Testing Library
- **Documentation**: OpenAPI/Swagger via drf-spectacular

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)

### Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd fitness-coach-app-v1
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the applications:
- Backend API: http://localhost:8000
- Frontend (Coach Portal): http://localhost:5173
- Client Portal: http://localhost:5173/client/login
- API Documentation: http://localhost:8000/api/docs/

### Demo Credentials

- **Coach Login**: 
  - Username: `coach`
  - Password: `demo123`
- **Assistant Login**:
  - Username: `assistant`
  - Password: `demo123`
- **Client Portal**:
  - John Doe: Username `john_doe`, Password `client123`
  - Jane Smith: Username `jane_smith`, Password `client456`

## Environment Variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/fitness_coach

# Email (for notifications)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=False

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1
```

## Local Development

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
poetry install
# or
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Load seed data and setup client portal:
```bash
python manage.py loaddata seed_data
python setup_client_portal.py
```

7. Run the development server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## API Endpoints

- **Authentication**: `/api/auth/jwt/`
- **Clients**: `/api/clients/`
- **Measurements**: `/api/clients/{id}/measurements/`
- **Foods**: `/api/foods/`
- **Exercises**: `/api/exercises/`
- **Diet Plans**: `/api/diet-plans/`
- **Workout Plans**: `/api/workout-plans/`
- **Assignments**: `/api/assignments/`
- **Check-ins**: `/api/checkins/`
- **Reports**: `/api/reports/progress/`
- **Client Portal**: `/api/client/`
  - Authentication: `/api/client/auth/login/`
  - Dashboard: `/api/client/dashboard/`
  - Plans: `/api/client/plans/`

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Coverage Report
```bash
cd backend
pytest --cov=. --cov-report=html
```

## Project Structure

```
fitness-coach-app-v1/
├── backend/                 # Django backend
│   ├── fitness_coach/      # Main Django project
│   ├── apps/              # Django applications
│   ├── requirements.txt    # Python dependencies
│   └── manage.py
├── frontend/               # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml      # Docker orchestration
├── .github/               # CI/CD workflows
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License
=======
# Fitness-coach-app

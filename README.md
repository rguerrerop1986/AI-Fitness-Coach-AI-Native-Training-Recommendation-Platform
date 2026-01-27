
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

After running migrations and creating users:

- **Coach Login** (Coach Portal): 
  - Username: `coach`
  - Password: `demo123`
- **Assistant Login** (Coach Portal):
  - Username: `assistant`
  - Password: `demo123`
- **Client Portal**:
  - Clients log in with their User account credentials (username/password)
  - Use `python manage.py create_client_users` to create client user accounts
  - Credentials will be printed by the command

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

6. Load seed data:
```bash
python manage.py loaddata seed_data
```

7. Create client user accounts (if you have existing clients):
```bash
python manage.py create_client_users
```

**Note**: The old `setup_client_portal.py` script is deprecated. Client authentication now uses standard Django User accounts with the `client` role. Use the `create_client_users` management command instead.

8. Run the development server:
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

## Authentication & Roles

The application uses unified Django authentication with JWT tokens for all users:

- **Coach/Admin**: Users with `role='coach'` who can manage clients, plans, and view all data
- **Assistant**: Users with `role='assistant'` who can help manage clients (same permissions as coach)
- **Client**: Users with `role='client'` who can only view their own assigned plans and measurements

### Creating Client Users

After creating a Client record, you need to create a linked User account for client portal access:

```bash
# Create user accounts for all clients without linked users
python manage.py create_client_users

# Or with a specific password
python manage.py create_client_users --password=SecurePass123

# Dry run to see what would be created
python manage.py create_client_users --dry-run
```

The command will:
- Generate unique usernames from client emails
- Create User accounts with `role='client'`
- Link the User to the Client via the `user` field
- Generate random passwords (or use provided password)
- Print credentials for sharing with clients

**Important**: Clients should change their passwords after first login.

### Login Endpoints

- **Coach/Assistant Login**: `POST /api/auth/login/`
  - Body: `{ "username": "coach", "password": "demo123" }`
  - Returns: `{ "user": {...}, "tokens": { "access": "...", "refresh": "..." } }`

- **Client Login**: `POST /api/client/auth/token/`
  - Body: `{ "username": "john_doe", "password": "client123" }`
  - Returns: `{ "access": "...", "refresh": "...", "client": {...} }`

- **Token Refresh**: `POST /api/auth/token/refresh/` (coach) or `POST /api/client/auth/token/refresh/` (client)
  - Body: `{ "refresh": "..." }`
  - Returns: `{ "access": "...", "refresh": "..." }`

## API Endpoints

- **Authentication**: 
  - Coach/Assistant: `/api/auth/login/`
  - Client: `/api/client/auth/token/`
  - Token Refresh: `/api/auth/token/refresh/` or `/api/client/auth/token/refresh/`
- **Clients**: `/api/clients/` (coach only)
- **Measurements**: `/api/clients/{id}/measurements/` (coach only)
- **Foods**: `/api/foods/` (coach only)
- **Exercises**: `/api/exercises/` (coach only)
- **Diet Plans**: `/api/diet-plans/` (coach only)
- **Workout Plans**: `/api/workout-plans/` (coach only)
- **Assignments**: `/api/assignments/` (coach only)
- **Check-ins**: `/api/checkins/` (coach only)
- **Reports**: `/api/reports/progress/` (coach only)
- **Client Portal**: 
  - Dashboard: `/api/client/dashboard/` (client only, returns own data)
  - Plans: `/api/client/plans/` (client only, returns own assignments)

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

## How to Test Locally

### Setup Steps

1. **Run migrations**:
   ```bash
   cd backend
   python manage.py migrate
   ```

2. **Create a superuser (Sandy - Coach/Admin)**:
   ```bash
   python manage.py createsuperuser
   # Username: sandy (or your choice)
   # Email: sandy@example.com
   # Password: (set a secure password)
   # Role: coach
   ```

3. **Create a client (Raul)**:
   - Use Django admin or API to create a Client record:
     - First name: Raul
     - Last name: (your choice)
     - Email: raul@example.com
     - Other required fields...

4. **Create user account for the client**:
   ```bash
   python manage.py create_client_users
   # This will create a User account with role='client' and link it to the Client
   # Note the username and password printed by the command
   ```

5. **Test client login**:
   - Navigate to http://localhost:5173/client/login
   - Use the credentials from step 4
   - Verify you can see only Raul's data

6. **Test coach login**:
   - Navigate to http://localhost:5173/login
   - Use Sandy's credentials from step 2
   - Verify you can see all clients and manage them

### Verification Checklist

- [ ] Client can authenticate via `/api/client/auth/token/`
- [ ] Client can access ONLY their own plans/measurements/checkins via `/api/client/dashboard/`
- [ ] Client cannot access other clients' data (returns 403/404)
- [ ] Coach can access all clients/plans via `/api/clients/`, `/api/diet-plans/`, etc.
- [ ] Coach cannot access client portal endpoints (returns 403)
- [ ] Token refresh works for both coach and client

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

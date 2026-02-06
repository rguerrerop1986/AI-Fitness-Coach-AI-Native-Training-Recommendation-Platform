
# Fitness Coach App

A comprehensive web application for fitness & nutrition coaches to manage clients, assign diet and workout plans, and track progress.

## Features

- **Client Management**: CRUD operations for clients with body measurements tracking
- **Catalogs**: Food and exercise databases with nutritional and workout information
- **Plans & Assignments**: Diet and workout plan creation with client assignment
- **Progress Tracking**: Weekly check-ins with trend analysis and charts
- **Appointments & Payments**: Schedule consultations with pay-per-consultation monetization
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
- Frontend (Coach Portal): http://localhost:5174
- Client Portal: http://localhost:5174/client/login
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

### Login Endpoints (Unified SimpleJWT)

All authentication uses Django User accounts with SimpleJWT tokens:

- **Standard Login** (Coach/Assistant): `POST /api/auth/token/`
  - Body: `{ "username": "coach", "password": "demo123" }`
  - Returns: `{ "access": "...", "refresh": "..." }`

- **Client Portal Login**: `POST /api/auth/token/client/`
  - Body: `{ "username": "john_doe", "password": "client123" }`
  - Returns: `{ "access": "...", "refresh": "...", "client": {...} }`
  - Validates: user role is 'client' and Client profile is linked

- **Token Refresh** (Unified): `POST /api/auth/token/refresh/`
  - Body: `{ "refresh": "..." }`
  - Returns: `{ "access": "...", "refresh": "..." }`
  - Works for both coach and client tokens

**Note**: The old `/api/client/auth/login/` endpoint has been removed. All authentication now uses unified SimpleJWT endpoints.

## API Endpoints

- **Authentication** (Unified SimpleJWT):
  - All users: `/api/auth/token/` (standard SimpleJWT endpoint)
  - Client portal: `/api/auth/token/client/` (validates client role + linked Client profile)
  - Token Refresh: `/api/auth/token/refresh/` (unified for all users)
  - Legacy: `/api/auth/login/` (coach/assistant, kept for backwards compatibility)
- **Clients**: `/api/clients/` (coach only)
- **Measurements**: `/api/clients/{id}/measurements/` (coach only)
- **Foods**: `/api/foods/` 
  - Read: All authenticated users (coach, assistant, client)
  - Write: Coach and assistant only
  - Filter by: `nutritional_group`, `origin_classification`
  - Search by: `name`, `brand`
- **Exercises**: `/api/exercises/`
  - Read: All authenticated users (coach, assistant, client)
  - Write: Coach and assistant only
  - Filter by: `muscle_group`, `equipment_type`, `difficulty`
  - Search by: `name`, `muscle_group`, `equipment`
- **Training Entries**: `/api/training-entries/`
  - Read: All authenticated users (clients see only their assigned plans)
  - Write: Coach and assistant only
  - Filter by: `workout_plan`, `exercise`, `date`
  - Nested endpoint: `/api/workout-plans/{id}/entries/` (GET, POST)
- **Diet Plans**: `/api/diet-plans/` (coach only)
- **Workout Plans**: `/api/workout-plans/` (coach only)
- **Assignments**: `/api/assignments/` (coach only)
- **Plan Cycles**: `/api/plan-cycles/` (coach only)
  - List/Create: `/api/plan-cycles/`
  - Detail: `/api/plan-cycles/{id}/`
  - Current cycle: `/api/plan-cycles/current/?client={id}` (coach)
- **Check-ins**: `/api/check-ins/` (global list) and `/api/clients/{id}/check-ins/` (nested, coach only)
  - **ESTRUCTURAL**: New check-ins use the structural format (pliegues, diámetros, perímetros, RC). POST accepts a nested payload; GET returns flat fields including `rc_1min` (alias for `rc_1min_bpm`). See [Check-in ESTRUCTURAL API](#check-in-estructural-api) below.
- **Reports**: `/api/reports/progress/` (coach only)
- **Client Portal** (all endpoints require client role):
  - Dashboard: `/api/client/dashboard/` (returns own data, inferred from token)
  - Plans: `/api/client/plans/` (returns own assignments only)
  - Current Cycle: `/api/client/current-cycle/` (returns active cycle)
  - Appointments: `/api/client/me/appointments/` (returns own appointments, separated into upcoming/past)
- **Appointments** (coach only - full CRUD):
  - List/Create: `/api/appointments/`
  - Detail/Update: `/api/appointments/{id}/`
  - Mark Completed: `/api/appointments/{id}/mark_completed/`
  - Mark Paid: `/api/appointments/{id}/mark_paid/` (requires payment_method in body)
  - Cancel: `/api/appointments/{id}/cancel/`
  - Filter by client: `/api/appointments/?client={id}`

### Check-in ESTRUCTURAL API

Seguimientos tipo ESTRUCTURAL (hoja Excel) se crean con `POST /api/clients/{client_id}/check-ins/` enviando un payload anidado. El backend persiste promedios de pliegues y diámetros y valida que todos los campos obligatorios estén presentes.

**Ejemplo de request (POST):**

```json
{
  "client_id": 123,
  "date": "2026-02-04",
  "weight_kg": 106.4,
  "height_m": 1.85,
  "rc_termino": 140,
  "rc_1min": 110,
  "skinfolds": {
    "triceps": { "m1": 10.0, "m2": 10.5, "m3": 10.2, "avg": 10.23 },
    "subscapular": { "m1": 12.0, "m2": 12.1, "m3": 12.2, "avg": 12.10 },
    "suprailiac": { "m1": 14.0, "m2": 14.2, "m3": 14.1, "avg": 14.10 },
    "abdominal": { "m1": 18.0, "m2": 18.5, "m3": 18.2, "avg": 18.23 },
    "ant_thigh": { "m1": 16.0, "m2": 16.3, "m3": 16.1, "avg": 16.13 },
    "calf": { "m1": 9.0, "m2": 9.2, "m3": 9.1, "avg": 9.10 }
  },
  "diameters": {
    "femoral": { "l": 9.0, "r": 9.1, "avg": 9.05 },
    "humeral": { "l": 7.0, "r": 7.2, "avg": 7.10 },
    "styloid": { "l": 5.0, "r": 5.1, "avg": 5.05 }
  },
  "perimeters": {
    "waist": 107, "abdomen": 110, "calf": 35, "hip": 115, "chest": 116,
    "arm": { "relaxed": 36, "flexed": 38 },
    "thigh": { "relaxed": 55, "flexed": 57 }
  },
  "feedback": {
    "rpe": 5, "fatigue": 5, "diet_adherence_pct": 80, "training_adherence_pct": 80,
    "notes": "..."
  }
}
```

**Ejemplo de response (201 Created):** el cuerpo es el check-in serializado en formato plano (todos los campos del modelo, con `rc_1min` en lugar de `rc_1min_bpm`), por ejemplo `id`, `client`, `date`, `weight_kg`, `height_m`, `rc_termino`, `rc_1min`, `skinfold_triceps_1/2/3/avg`, `diameter_femoral_l/r/avg`, `perimeter_waist`, etc., más `rpe`, `fatigue`, `diet_adherence`, `workout_adherence`, `notes`, `created_at`, `updated_at`.

## Exercise Catalog & Training Entries

The app includes a comprehensive exercise catalog that coaches can use to build workout plans with specific training entries.

### Features

- **Exercise Catalog**: Complete exercise database with muscle groups, equipment types, and difficulty levels
- **Training Entries**: Connect exercises to workout plans with sets, reps, weight, rest, and notes
- **Image Support**: Optional image URLs for exercise visualization
- **Instructions**: Text or URL-based exercise instructions

### Exercise Fields

- **Name**: Unique exercise name
- **Muscle Group**: Chest, Back, Shoulders, etc.
- **Equipment Type**: Mancuerna, Barra, Máquina, Peso Corporal, etc.
- **Difficulty**: Beginner, Intermediate, Advanced
- **Instructions**: Exercise instructions (text or URL)
- **Image URL**: Optional image for visualization
- **Video URL**: Optional video demonstration

### Training Entry Fields

- **Date**: Session date for the training entry
- **Series**: Number of sets
- **Repetitions**: Reps (e.g., "8-12" or "10")
- **Weight (kg)**: Optional weight (for bodyweight exercises, leave blank)
- **Rest (seconds)**: Optional rest time between sets
- **Notes**: Additional notes for the exercise

### Coach Workflow

1. **Create Exercises**: Navigate to Exercises → "Add Exercise" to create exercise entries
2. **Build Workout Plans**: Create workout plans and add training entries
3. **Add Training Entries**: Use `/api/workout-plans/{id}/entries/` to add exercises to plans
4. **Assign to Clients**: Assign workout plans to clients via PlanAssignment

### Client Access

- Clients can view exercises in their assigned workout plans
- Training entries are included in the current cycle response
- Read-only access to exercise details and instructions

### API Endpoints

- **List Exercises**: `GET /api/exercises/` (authenticated users)
- **Create Exercise**: `POST /api/exercises/` (coach/assistant only)
- **List Training Entries**: `GET /api/training-entries/` (filtered by assigned plans for clients)
- **Create Training Entry**: `POST /api/training-entries/` or `POST /api/workout-plans/{id}/entries/` (coach/assistant only)
- **Nested Endpoint**: `GET /api/workout-plans/{id}/entries/` (get all entries for a plan)

## Food Catalog & Nutrition Management

The app includes a comprehensive food catalog with complete nutritional information for diet plan generation.

### Features

- **Complete Nutrition Data**: All nutrients stored per 100g for consistency
- **Classification**: Foods are classified by nutritional group and origin (Vegetal/Animal/Mineral)
- **Macronutrients**: Calories, protein, carbs, and fats (required)
- **Optional Nutrition**: Fiber, water, and creatine tracking
- **Notes**: Micronutrients notes and general remarks for sources

### Nutritional Groups

Foods are classified into 6 nutritional groups (in Spanish):
1. Cereales, tubérculos y derivados.
2. Frutas y verduras.
3. Leche y derivados.
4. Carnes, legumbres secas y huevos.
5. Azúcares o mieles.
6. Aceites o grasas.

### Coach Workflow

1. **Create Foods**: Navigate to Foods → "Add Food" to create new food entries
2. **Required Fields**: Name, nutritional group, origin classification, and all macronutrients (per 100g)
3. **Optional Fields**: Fiber, water, creatine, and notes
4. **Filter & Search**: Use filters by nutritional group/origin and search by name
5. **Edit/Delete**: Coaches can update or remove foods

### Data Model

- **Nutrients stored per 100g**: All macronutrients (calories_kcal, protein_g, carbs_g, fats_g) are stored per 100g for consistency
- **Serving size**: Legacy field kept for backward compatibility
- **Validation**: All numeric fields must be non-negative; required fields enforced in serializer

### API Endpoints

- **List Foods**: `GET /api/foods/` (authenticated users)
- **Create Food**: `POST /api/foods/` (coach/assistant only)
- **Update Food**: `PATCH /api/foods/{id}/` (coach/assistant only)
- **Delete Food**: `DELETE /api/foods/{id}/` (coach/assistant only)
- **Filter**: `GET /api/foods/?nutritional_group={group}&origin_classification={origin}`
- **Search**: `GET /api/foods/?search={query}`

## Appointments & Pay-Per-Consultation

The app supports appointment scheduling with pay-per-consultation monetization. This is a simple MVP implementation that tracks payments manually (no payment gateway integration yet).

### Features

- **Coach can**:
  - Create appointments with client, date/time, duration, and price
  - Mark appointments as completed after the consultation
  - Mark appointments as paid (only after completion)
  - Cancel appointments
  - View all appointments with filtering by client

- **Client can**:
  - View their own appointments (read-only)
  - See upcoming and past appointments separately
  - View payment status for each appointment

### Business Rules

1. **Payment Status**:
   - New appointments default to `UNPAID`
   - Only `COMPLETED` appointments can be marked as `PAID`
   - When marking as paid, a payment method must be specified (cash, transfer, card, other)

2. **Appointment Status**:
   - `SCHEDULED`: Initial status for new appointments
   - `COMPLETED`: Consultation has taken place
   - `CANCELLED`: Appointment was cancelled
   - `NO_SHOW`: Client did not attend

3. **Permissions**:
   - Clients can only view their own appointments
   - Clients cannot modify appointments, status, or payment information
   - Coaches have full CRUD access to all appointments

### Usage Example

**Coach creates an appointment**:
```bash
POST /api/appointments/
{
  "client": 1,
  "scheduled_at": "2026-02-15T10:00:00Z",
  "duration_minutes": 60,
  "price": "500.00",
  "currency": "MXN",
  "notes": "Initial consultation"
}
```

**After consultation, coach marks as completed**:
```bash
PATCH /api/appointments/1/mark_completed/
```

**Coach records payment**:
```bash
PATCH /api/appointments/1/mark_paid/
{
  "payment_method": "cash"
}
```

**Client views their appointments**:
```bash
GET /api/client/me/appointments/
# Returns:
{
  "all": [...],
  "upcoming": [...],
  "past": [...]
}
```

### Payment Tracking

Currently, payment tracking is manual:
- Coach marks appointment as `PAID` after receiving payment
- Payment method is recorded (cash, transfer, card, other)
- `paid_at` timestamp is automatically set when marking as paid
- No payment gateway integration (ready for future Stripe integration)

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
   # Basic usage - creates users for all clients without linked accounts
   python manage.py create_client_users
   
   # Dry run to see what would be created
   python manage.py create_client_users --dry-run
   
   # Use a default password for all created users (dev only)
   python manage.py create_client_users --default-password=SecurePass123
   
   # Force recreate users for clients with invalid/missing links
   python manage.py create_client_users --force
   
   # Note the username and password printed by the command
   ```

5. **Test client login**:
   - Navigate to http://localhost:5174/client/login
   - Use the credentials from step 4
   - Verify you can see only Raul's data

6. **Test coach login**:
   - Navigate to http://localhost:5174/login
   - Use Sandy's credentials from step 2
   - Verify you can see all clients and manage them

### Verification Checklist

- [ ] Client can authenticate via `/api/auth/token/client/` (unified SimpleJWT)
- [ ] Client receives standard JWT tokens (access/refresh)
- [ ] Client can access ONLY their own plans/measurements/checkins via `/api/client/dashboard/`
- [ ] Client cannot access other clients' data (returns 403/404)
- [ ] Client cannot access coach endpoints (returns 403)
- [ ] Coach can authenticate via `/api/auth/token/`
- [ ] Coach can access all clients/plans via `/api/clients/`, `/api/diet-plans/`, etc.
- [ ] Coach cannot access client portal endpoints (returns 403)
- [ ] Token refresh works for both coach and client via `/api/auth/token/refresh/`
- [ ] No ClientSubscription model exists (removed, using unified User auth)
- [ ] PlanCycle can be created and linked to assignments
- [ ] CheckIns auto-link to active PlanCycle
- [ ] No overlapping active PlanCycles allowed for same client

## PlanCycle Usage

PlanCycle is a period container for organizing plans and tracking data into time-bound cycles (weekly/biweekly/monthly).

### Creating a PlanCycle (Coach)

1. **Create a PlanCycle**:
   ```bash
   POST /api/plan-cycles/
   {
     "client": 1,
     "start_date": "2025-01-01",
     "end_date": "2025-01-08",
     "cadence": "weekly",
     "goal": "fat_loss",
     "status": "active"
   }
   ```

2. **Link assignments to cycle**:
   When creating a PlanAssignment, optionally link it to a PlanCycle:
   ```bash
   POST /api/assignments/
   {
     "client": 1,
     "plan_type": "diet",
     "diet_plan": 1,
     "start_date": "2025-01-01",
     "plan_cycle": 1  # Link to PlanCycle
   }
   ```

3. **Business Rules**:
   - Only one ACTIVE PlanCycle per client at a time
   - Overlapping active cycles are rejected (use DRAFT status to plan ahead)
   - CheckIns automatically link to the active PlanCycle for the check-in date

### Client View of Current Cycle

Clients can view their current active cycle:
```bash
GET /api/client/current-cycle/
```

Returns:
- Cycle details (dates, cadence, goal)
- Linked diet plan summary
- Linked workout plan summary

### Management Command Options

The `create_client_users` command supports several options:

- `--dry-run`: Preview what would be created without making changes
- `--default-password=<pwd>`: Set a default password for all created users (dev only)
- `--force`: Recreate users for clients with invalid/missing user links
- `--password`: Alias for `--default-password`

**Example**:
```bash
# Preview changes
python manage.py create_client_users --dry-run

# Create users with a default password
python manage.py create_client_users --default-password=TempPass123

# Fix clients with broken user links
python manage.py create_client_users --force
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

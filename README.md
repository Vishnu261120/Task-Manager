# Team Task Manager

A simple full-stack Django project for the assignment. It includes:

- Signup, login, and logout
- Project management with admin/member roles
- Task creation, assignment, status updates, and overdue tracking
- Dashboard analytics
- REST API endpoints
- SQLite locally and PostgreSQL-ready Railway deployment

## Local setup

```bash
python -m venv .venv
# activate venv
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Default flow

1. Sign up as a user.
2. Create a project. You become the project admin automatically.
3. Add members by email.
4. Create and assign tasks.
5. View dashboard stats.

## API endpoints

- `POST /api/auth/signup/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/projects/`
- `POST /api/projects/`
- `GET /api/tasks/`
- `POST /api/tasks/`
- `GET /api/dashboard/`

## Railway deployment

1. Create a new Railway project.
2. Connect this repo.
3. Add environment variables:
   - `DEBUG=0`
   - `SECRET_KEY`
   - `ALLOWED_HOSTS=your-railway-domain`
   - `CSRF_TRUSTED_ORIGINS=https://your-railway-domain`
   - `DATABASE_URL` from Railway Postgres
4. Run migrations on deploy:

```bash
python manage.py migrate
```

5. Start command is handled by `Procfile` / `gunicorn`.

## Notes

The frontend is intentionally simple so the project is easy to explain during evaluation, but it still covers the required features and REST API structure.

# Piki Ora Medical Centre API

Django REST Framework backend for the clinic appointment system.
Patients register and book a doctor. Staff manage doctors, times, bookings and patient accounts from the React site (separate repository). The React app is the staff dashboard. The Django admin page is only a backup view of the tables.

## Logins after seed data

| Who | Username | Password |
| --- | --- | --- |
| Staff | admin | Admin12345 |
| Patient | avery | Patient12345 |

## Run it locally (Windows)

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

API base: http://127.0.0.1:8000

Quick check: http://127.0.0.1:8000/api/health/

## Main endpoints

- POST `/api/register/` and POST `/api/login/` return a token
- POST `/api/logout/` and GET `/api/me/`
- `/api/doctors/` list for logged-in users, create/update/delete for staff
- `/api/slots/?doctor=1&available=true` open times
- POST `/api/appointments/` book a slot
- PATCH `/api/appointments/<id>/` change the reason or move to another slot
- POST `/api/appointments/<id>/cancel/` cancel and free the slot
- `/api/patients/` staff only, turn an account on or off

Send the token as: `Authorization: Token <token>`

The Postman collection is `postman/Piki_Ora_API.postman_collection.json`. Run the Login request first. It saves the token for the other requests.

## Where the booking rule lives

`clinic/models.py` has a database rule so only one booked appointment can point at a slot.
`clinic/views.py` checks the slot is still free, then marks it unavailable.
Cancelling sets the slot back to available.

## Database

The `.env` file has the database credentials.

- `USE_SQLITE=True` uses `db.sqlite3`. This is the simple local setup.
- Set `USE_SQLITE=False` to use `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`.
- If `DATABASE_URL` is set, that Postgres URL is used instead. That is the usual Render setup.

Do not commit your real `.env`. `.env.example` shows the same keys.

## Tests

```powershell
python manage.py test
```

## Deploy on Render

1. Push this repo to a public GitHub repository.
2. In Render, New, Web Service, connect the repo.
3. Build command:

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_data
```

4. Start command:

```text
gunicorn piki_ora.wsgi:application --bind 0.0.0.0:$PORT
```

5. Environment variables:

```text
PYTHON_VERSION=3.11.11
DEBUG=False
USE_SQLITE=True
CORS_ALLOW_ALL=True
ALLOWED_HOSTS=*
SECRET_KEY=any-long-random-string
```

6. Deploy, then open `https://your-service.onrender.com/api/health/`. It should say `{"status":"ok"}`.

SQLite on the free Render plan keeps the seeded admin login. New bookings can disappear if the free service goes to sleep. For a database that keeps bookings, create a Render Postgres database, copy its Internal Database URL into `DATABASE_URL`, and remove `USE_SQLITE` or set it to `False`.

## Project files

- `users/models.py` patient and staff accounts
- `users/views.py` register, login, logout, patient list
- `clinic/models.py` doctors, slots, appointments
- `clinic/serializers.py` JSON in and out
- `clinic/views.py` booking, edit, cancel
- `clinic/management/commands/seed_data.py` demo data

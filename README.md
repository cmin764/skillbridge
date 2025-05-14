# skillbridge

SkillBridge - Bridging the gap between purposeful roles and exceptional candidates

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL

### Database Setup

#### Installing PostgreSQL on Mac

```bash
# Using Homebrew
brew install postgresql@17
brew services start postgresql@17

# OR using Postgres.app
# Download from https://postgresapp.com/
```

#### Creating the Database

```bash
# Create the database
createdb skillbridge

# If you need to specify a user
createdb -U postgres skillbridge
```

Connect first with `psql` if `createdb` isn't available. (check for `-17` suffix)

### Project Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (optional)
python manage.py createsuperuser
```

### Running the Server

```bash
# Using Django's development server
python manage.py runserver

# OR using Uvicorn (ASGI)
uvicorn skillbridge.asgi:application --reload
```

Access the site at http://127.0.0.1:8000/

### Admin Access

To access the Django admin interface:

1. Create a superuser if you haven't already:
```bash
python manage.py createsuperuser
```

2. You'll be prompted to enter:
   - Username (e.g., `cmin764`)
   - Email address (e.g., `your.email@example.com`)
   - Password (twice)
   
   Note: If you get a "password too common" warning, you can bypass validation by entering `y`.

3. Access the admin interface at http://127.0.0.1:8000/admin/

4. Log in with the superuser credentials you created

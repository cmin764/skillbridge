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

Admin interface is available at http://127.0.0.1:8000/admin/ (login with the superuser you created)

## API Documentation

For API request examples using the HTTPie tool, see [API Request Examples](docs/request-examples.md).

## Front-end UI

The SkillBridge UI is a Next.js app located in the `skillbridge-ui` directory.

See [skillbridge-ui/README.md](./skillbridge-ui/README.md) for setup and usage instructions for the front-end.

# SkillBridge API Request Examples

This document provides examples for using the SkillBridge API with HTTPie.

## Authentication

When authentication is enabled, you'll need to authenticate before accessing protected endpoints.

### JWT Authentication (Recommended)

JWT (JSON Web Token) authentication is stateless and recommended for API clients.

#### 1. Obtain a JWT token

```bash
# Get an access token
http POST http://localhost:8000/api/token/ username=your_username password=your_password
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 2. Use the token in subsequent requests

```bash
# Set token as a variable for ease of use
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Use the token in your requests
http GET http://localhost:8000/api/cv-uploads/ "Authorization: Bearer $TOKEN"
```

#### 3. Refresh token when it expires

Access tokens typically expire after 5 minutes. Use the refresh token to get a new access token:

```bash
# Using the refresh token to get a new access token
http POST http://localhost:8000/api/token/refresh/ refresh="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Session Authentication (Browser-based)

For browser-based access or development, you can use session authentication.

```bash
# Login via the browsable API
http --session=./session.json -f POST http://localhost:8000/api-auth/login/ username=your_username password=your_password

# Subsequent requests will use the session cookie
http --session=./session.json GET http://localhost:8000/api/cv-uploads/
```

### Creating a Superuser

Before you can login, create a superuser account if you haven't already:

```bash
python manage.py createsuperuser
```

Follow the prompts to create a username, email, and password.

## API Endpoints

### CV Uploads

```bash
# Upload a CV file
http -f POST http://localhost:8000/api/cv-uploads/ file@/path/to/resume.pdf "Authorization: Bearer $TOKEN"

# List all CVs
http GET http://localhost:8000/api/cv-uploads/ "Authorization: Bearer $TOKEN"

# Parse a CV into a candidate
http POST http://localhost:8000/api/cv-uploads/1/parse/ "Authorization: Bearer $TOKEN"
```

### Jobs

```bash
# Create a job posting
http POST http://localhost:8000/api/jobs/ \
  title="Django Developer" \
  requirements:='["Python", "Django", "REST", "PostgreSQL"]' \
  "Authorization: Bearer $TOKEN"

# List all jobs
http GET http://localhost:8000/api/jobs/ "Authorization: Bearer $TOKEN"

# Search for jobs containing "Python"
http GET "http://localhost:8000/api/jobs/?search=Python" "Authorization: Bearer $TOKEN"
```

### Candidates

```bash
# List all candidates
http GET http://localhost:8000/api/candidates/ "Authorization: Bearer $TOKEN"

# Get a specific candidate
http GET http://localhost:8000/api/candidates/1/ "Authorization: Bearer $TOKEN"
```

### Matches

```bash
# Create a match between a candidate and job
http POST http://localhost:8000/api/matches/create_match/ \
  candidate_id=1 job_id=1 \
  "Authorization: Bearer $TOKEN"

# Run the matching algorithm for all candidates
http POST http://localhost:8000/api/matches/match_candidates/ "Authorization: Bearer $TOKEN"
``` 

# SimpliSmart Task API Documentation

This API provides user authentication and organization management functionality.

## Authentication

All endpoints except `/accounts/signup/` and `/accounts/login/` require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer your_access_token
```

## API Endpoints

### Authentication

#### Sign Up
```http
POST /accounts/signup/
```
Create a new user account.

**Request Body:**
```json
{
    "username": "string",
    "password": "string",
    "invite_code": "string"  // optional
}
```

**Response (201 Created):**
```json
{
    "message": "User created successfully"
}
```

#### Login
```http
POST /accounts/login/
```
Authenticate and get JWT tokens.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response (200 OK):**
```json
{
    "message": "Login successful",
    "user_id": "integer",
    "username": "string",
    "access": "string",  // JWT access token
    "refresh": "string"  // JWT refresh token
}
```

#### Refresh Token
```http
POST /accounts/token/refresh/
```
Get a new access token using refresh token.

**Request Body:**
```json
{
    "refresh": "string"  // refresh token
}
```

**Response (200 OK):**
```json
{
    "access": "string"  // new access token
}
```

### Organizations

#### Create Organization
```http
POST /accounts/organizations/create/
```
Create a new organization. Requires authentication.

**Request Body:**
```json
{
    "name": "string"
}
```

**Response (201 Created):**
```json
{
    "message": "Organization created successfully",
    "organization": {
        "id": "integer",
        "name": "string",
        "invite_code": "string"
    }
}
```

#### Join Organization
```http
POST /accounts/organizations/join/
```
Join an organization using invite code. Requires authentication.

**Request Body:**
```json
{
    "invite_code": "string"
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully joined organization",
    "organization": {
        "id": "integer",
        "name": "string"
    }
}
```

#### View Invite Code
```http
GET /accounts/organizations/{organization_id}/invite-code/
```
View the current invite code for an organization. Requires authentication and organization membership.

**Response (200 OK):**
```json
{
    "organization_id": "integer",
    "organization_name": "string",
    "invite_code": "string"
}
```

#### Regenerate Invite Code
```http
POST /accounts/organizations/{organization_id}/invite-code/
```
Generate a new invite code for an organization. Requires authentication and organization membership.

**Response (200 OK):**
```json
{
    "message": "Invite code regenerated successfully",
    "organization_id": "integer",
    "organization_name": "string",
    "new_invite_code": "string"
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "string"  // Error message
}
```

### 401 Unauthorized
```json
{
    "error": "string"  // Error message
}
```

### 403 Forbidden
```json
{
    "error": "string"  // Error message
}
```

### 404 Not Found
```json
{
    "error": "string"  // Error message
}
```

## Example Usage

1. Sign up a new user:
```bash
curl -X POST http://localhost:8000/accounts/signup/ \
-H "Content-Type: application/json" \
-d '{"username": "testuser", "password": "testpass123"}'
```

2. Login to get JWT tokens:
```bash
curl -X POST http://localhost:8000/accounts/login/ \
-H "Content-Type: application/json" \
-d '{"username": "testuser", "password": "testpass123"}'
```

3. Create an organization:
```bash
curl -X POST http://localhost:8000/accounts/organizations/create/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-d '{"name": "My Organization"}'
```

4. Join an organization:
```bash
curl -X POST http://localhost:8000/accounts/organizations/join/ \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
-d '{"invite_code": "abc123xyz"}'
```

5. View invite code:
```bash
curl -X GET http://localhost:8000/accounts/organizations/1/invite-code/ \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

6. Regenerate invite code:
```bash
curl -X POST http://localhost:8000/accounts/organizations/1/invite-code/ \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
``` 
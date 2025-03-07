# Česká elektronická knihovna (ČEK)

Django app presenting over 70 000 Czech poems from 19th and 20th century.

## Installation

Ensure you have Python 3, `pip`, and `PostgreSQL` installed.

### 1. Clone the Repository
```sh
git clone <repository_url>
cd <repository_name>
```

### 2. Set Up the Database

Create a PostgreSQL database and a user with necessary privileges:

```sql
CREATE DATABASE mydatabase;
CREATE USER myuser WITH PASSWORD 'mypassword';
ALTER ROLE myuser SET client_encoding TO 'utf8';
ALTER ROLE myuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;
```

### 3. Configure the Application

Copy the sample configuration and update it with your credentials:

```sh
cp cek/config.sample.py cek/config.py
```

Edit `cek/config.py` and update:

 * Database credentials (from Step 2)
 * `SECRET_KEY` (generate one using: `python -c 'import secrets; print(secrets.token_hex(32))'`)

### 4. Apply migrations

```sh
python manage.py migrate
```

### 5. Run the Development Server

```sh
python manage.py runserver
```

### 6. Create a Superuser (for Admin Access)

To access the Django admin panel at `/admin/`, create a superuser:

```sh
python manage.py createsuperuser
```

Follow the prompts to set up the admin account.

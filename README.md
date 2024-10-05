# optimo
Python Developer Recruitment Task

This is an application designed to streamline book reservations and manage library resources efficiently. 
This system leverages both Django and Flask frameworks, orchestrated through Docker Compose, to provide a robust and scalable solution for library management.
The aplication features Django Celery Beat and Redis for notification sending via email, and Flask to check external libraries.

### Features
Core features include:
* Book Management: CRUD operations for managing books in the library.
* User Management: User registration and administration with role-based permissions.
* Reservations: Users can reserve books, with availability checks across multiple libraries.
* Health Checks: Monitor the health status of both Django and Flask services.
* Robust Logging: Logs are stored in a MySQL database for easy monitoring and analysis.
* Resilience: Implements retry mechanisms for external API communications to enhance reliability.

### Architecture
The system consists of the following components:
* Django Backend (django_backend): Handles user authentication, book reservations, and administrative tasks.
* Flask API (flask): Provides status checks for book availability across different libraries.
* MySQL Database: Stores application data, including logs.
* Redis: Serves as a message broker for asynchronous tasks handled by Celery.
* Celery Workers: Execute background tasks such as sending notifications.
* Docker Compose: Orchestrates all services, ensuring seamless interaction and deployment.

### Installation
1. Clone the Repository

    ```
    git clone https://github.com/popraf/optimo.git

    cd optimo
    ```

2. Set Up Environment Variables

    Create a `.env` file in the project's root directory based on the provided `.env.example`

3. Configuration

    The application uses Docker Compose to manage multiple services. The primary configuration file is docker-compose.yml. Here's a brief overview of the services:

    * optimo-mysql: MySQL database for storing application data and logs.
    * optimo-redis: Redis server acting as a message broker for Celery.
    * optimo-flask: Flask API service handling book status checks.
    * optimo-django: Django backend managing reservations and user authentication.
    * celery: Celery worker for executing background tasks.
    * celery-beat: Celery Beat scheduler for periodic tasks.
    
    Ensure that all services are correctly defined in the docker-compose.yml file and that environment variables are appropriately set in the .env file.

4. Build and Start Services

    From the project's root directory, run: 
    ```
    docker-compose up --build -d
    ```

    Check the status of all services via: 
    ```
    docker-compose ps
    ```

### API Endpoints

#### Django Backend
The Django backend provides endpoints for managing users, books, and reservations.

* User Registration Endpoint
    * Endpoint: /api/register/
    * Method: POST
    * Description: Register a new user.
    * Payload:
        ```
        {
            "username": "newuser",
            "password": "strongpassword123",
            "email": "newuser@example.com"
        }
        ```

* Book Management
    * List Books
        * Endpoint: /api/books/
        * Method: GET
        * Description: Retrieve a list of all books.
    * Retrieve Book Details
        * Endpoint: /api/books/{id}/
        * Method: GET
        * Description: Retrieve details of a specific book, required JWT auth data in request.
        * Create, Update, Delete Books: Restricted to admin users.

* Reservation Management
    * Reserve a Book
        * Endpoint: /api/reservations/reserve/
        * Method: POST
        * Description: Reserve a book, required JWT auth data in request.
        * Payload:
            ```
            {
                "book_id": 1,
                "reserved_until": "2024-12-31T23:59:59",
                "library": "Main Library"
            }
            ```

    * Return a Book
        * Endpoint: /api/reservations/{id}/return_book/
        * Method: POST
        * Description: Return a reserved book, required JWT auth data in request.

#### Flask API
The Flask API handles status checks for book availability.

* Health Check
    * Endpoint: /health
    * Method: GET
    * Description: Check if the Flask service is running.

* Check Book Availability
    * Endpoint: /status/<book_id>
    * Method: GET
    * Description: Retrieve availability status of a book across different libraries. Currently works only on mock data. book_id is int.
    * Response:
        ```
        {
            "book_id": 1,
            "availability": {
                "library 2": true,
                "library 3": false,
                "library 4": true
            }
        }
        ```

* Reserve a Book via Flask
    * Endpoint: /reserve
    * Method: POST
    * Description: Reserve a book by communicating with the Django backend.
    * Headers:
        * Authorization: Bearer <JWT_TOKEN>
        * Content-Type: application/json
    * Payload:
        ```
        {
            "book_id": 1,
            "reserved_until": '2024-12-31T23:59:59',
            "library": "Main Library"
        }
        ```

### Logging
* Django Logs: Managed by Django's logging framework and stored in the MySQL database.
* Flask Logs: Redirected from log files to the MySQL database using a custom logging handler implemented with SQLAlchemy.
#### Viewing Logs
Access the logs directly from the MySQL database. Use a MySQL client or admin tool to query the logs_db (or your configured database) and inspect the log table for detailed log entries.


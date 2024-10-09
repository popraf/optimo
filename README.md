# optimo
Python Developer Recruitment Task

This is an application designed to streamline book reservations and manage library resources efficiently. 
This system leverages both Django and Flask frameworks, orchestrated through Docker Compose, to provide a robust and scalable solution for library management.
The aplication also features Django Celery Beat and Redis for notification sending via email, and Flask to check external libraries.

### Basic Business Logic
* Users can reserve and return books from the main library. If a book isn't available locally, the system checks external libraries via an external API and handles reservations accordingly.

* Administrators have additional privileges to manage the book inventory through specialized endpoints.

* Checks availability in main library by quering the MySQL db to check if the book is available in primary library (Main Library). If available:
    1. Creates a reservation entry in the database linking the user, book, reservation period, and library.
    2. Logs the reservation event.
    3. Responds with a success message and reservation details.

* Check availability in other libraries via Flask API: If the book is not available in the Main Library, Django sends a GET request to the Flask API endpoint `/books/<isbn>/availability`. Flask API responds with the availability status of the book across other libraries. This logic also implements a retry strategy (3 retries) to handle transient failures when communicating with the Flask API.

* Reservation via Flask API: Users can reserve a book using Flask `/reserve` endpoint. The endpoint reserves a book by calling Django's endpoint, therefore the core reservation logic should be maintained only in Django.

### Features
Core features include:
* Book Management: CRUD operations for managing books in the library.
* User Management: User registration and administration with role-based permissions.
* Reservations: Users can reserve books, with availability checks across multiple libraries.
* Health Checks: Monitor the health status of both Django and Flask services.
* Robust Logging: Logs are stored in a MySQL database for easy monitoring and analysis.
* Resilience: Implements retry mechanisms for external API communications to enhance reliability.
* Caching, such as caching books list view

### Architecture
The system consists of the following components:
* Django Backend (django_backend): Handles user authentication, book reservations, and administrative tasks.
* Flask API (flask): Provides status checks for book availability across different libraries.
* MySQL Database: Stores application data, including logs.
* Redis: Serves as a message broker for asynchronous tasks handled by Celery.
* Celery Workers: Execute background tasks such as sending notifications.
* Docker Compose: Orchestrates all services, ensuring seamless interaction and deployment.
![Optimo Architecture](https://github.com/user-attachments/assets/c6827f01-83f6-4809-92b0-649f8068eb10)

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
    
    * Using Docker Compose:

        From the project's root directory, run: 
        ```
        docker-compose up --build -d
        ```

        Check the status of all services via: 
        ```
        docker-compose ps
        ```
    * Using Docker Dev Container:
        
        Dev containers are prepared for both Django and Flask applications, therefore please adhere to commonly known instructions. Both dev containers are available in `.devcontainer` folder.

### Running Tests

Once containers are built, please use following commands to run respective Flask and Django tests:
    
* Django
    
    ```
    docker exec optimo-django-container python manage.py test -v 3
    ```

* Flask
    
    ```
    docker exec optimo-flask-container pytest -vv
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

* Check Book Availability by Book PK
    * Endpoint: /api/books/< pk:int >/check_availability
    * Method: GET
    * Description: Check availability of a book across internal and external libraries by PK from main system.

* Search Book by ISBN
    * Endpoint: /api/books/search_by_isbn/?isbn=< isbn >
    * Method: GET
    * Description: Check availability of a book in main system using its ISBN.
    * Query Params: isbn

* Book Management
    * List Books
        * Endpoint: /api/books/
        * Method: GET
        * Description: Retrieve a list of all books.
    * Retrieve Book Details
        * Endpoint: /api/books/< pk >/details
        * Method: GET
        * Description: Retrieve details of a specific book, required JWT auth data in request.
        * Create, Update, Delete Books: Restricted to admin users.

* User Login
    * Endpoint: /api/login
    * Method: POST
    * Description: Login to the library system. This will authenticate the user and return a JWT token for further API interactions.

* Reservation Management
    * Reserve a Book
        * Endpoint: /api/reserve/< pk >/
        * Method: POST
        * Description: Reserve a book, required JWT auth data in request.
        * Query Params: book_id

    * Return a Book
        * Endpoint: /api/reservations/< pk >/return_book/
        * Method: POST
        * Description: Return a reserved book, required JWT auth data in request.

#### Flask API
The Flask API handles status checks for book availability.

* Health Check
    * Endpoint: /health
    * Method: GET
    * Description: Check if the Flask service is running.

* Check Book Availability
    * Endpoint: /books/<isbn>/availability
    * Method: GET
    * Description: Retrieve book available across different external libraries. Currently works only on mock data.
    * Response:
        ```
        1: {
            "library": "Library 1",
            "count_in_library": 1
        },
        ```

* Check Book Details
    * Endpoint: /books/<int:pk>/details
    * Method: GET
    * Description: Retrieve details of a book from external library. Currently works only on mock data.
    * Response:
        ```
        1: {
            "title": "Title Book",
            "author": "Test Author",
            "isbn": 123123,
            "library": "Library 1",
            "count_in_library": 1
        },
        ```

* User Login
    * Endpoint: /login
    * Method: POST
    * Description: User login, returns refresh and access tokens provided by Django.

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
        }
        ```

* Reserve a Book via Flask
    * Endpoint: /book_reserved_external/<int:pk>
    * Method: POST
    * Description: Reserve a book in external library.
    * Headers:
        * Authorization: Bearer <JWT_TOKEN>
        * Content-Type: application/json
    * Payload:
        ```
        {
            "book_id": 1,
        }
        ```

### Logging
* Django Logs: Managed by Django's logging framework and stored in the MySQL database.
* Flask Logs: Redirected from log files to the MySQL database using a custom logging handler implemented with SQLAlchemy.
#### Viewing Logs
Access the logs directly from the MySQL database. Use a MySQL client or admin tool to query the logs_db (or your configured database) and inspect the log table for detailed log entries.

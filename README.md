(API Service for Retail Network Ordering)
Development by Obrant Aleksandr.
Description:
The application is designed to automate purchasing in a retail network. Service users are the buyer (a retail manager who purchases products for sale in a store) and the supplier of goods.

Client (Buyer):
The purchasing manager makes daily purchases through the API from a catalog that contains products from multiple suppliers.
In one order, the buyer can specify products from different suppliers, which will affect the delivery cost.
The user can log in, register and restore their password through the API.

Supplier:
Notifies the service of price updates via the API.
Can enable or disable order acceptance.
Can receive a list of completed orders (with products from their price list).

Technologies used in the project:
Python 3
Django
Django Rest Framework
Celery
Redis server

Installation:

Clone the repository with git
https://github.com/aobrant/shop-service.git

Get folder:
cd shop_service

Create and activate a Python virtual environment.
Install dependencies from requirements.txt file:

pip install -r requirements.txt

Go to folder with manage.py:

cd orders

Run the following commands:

To create database application migrations

python manage.py makemigrations
python manage.py migrate

Create a superuser

python manage.py createsuperuser

Run bases
docker-compose up

Run Celery
celery -A orders worker -l info


Command to run the application

python manage.py runserver

The application will be available at: http://127.0.0.1:8000/`
At api/schema/, a JSON schema of API will be generated, 
from which Swagger-UI documentation will be built at api/docs/.

http://127.0.0.1:8000/api/docs/ you will see a list of endpoints


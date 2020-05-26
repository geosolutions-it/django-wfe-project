# django-wfe-project

Reference Django project for the integration of django-wfe module.

**Please note this is only preliminary version of the reference implementation! A lot of things may yet change.**

## Requirements
##### Requirements:
* Python 3.7.5+
* PostgreSQL 11.7+
* RabbitMQ 3+

You can quickly setup RabbitMQ with docker, e.g.:
`docker run -d -p 15672:15672 -p 5672:5672 -p 5671:5671 --hostname my-rabbitmq rabbitmq:3-management`

## Quick Setup

1. Create a python virtualenv, activate it and install requirments:
        
    ``` bash
    python3.7 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
        
2. Create environment variables configuring the `PostgreSQL` database backend:
        
    ``` bash
    export DB_PASSWORD=<your_password>  (required)
    export DB_NAME=<database_name>      (default: postgres)
    export DB_USER=<database_user>      (default: postgres)
    export DB_HOST=localhost            (default: localhost)
    export DB_PORT=5432                 (default: 5243)
    ```
        
3. In case you are not using default config of RabbitMQ, you need to configure `django_dramatiq` broker in `django_wfe_project/settings.py` file
For details see: [django_dramatiq][django_dramatiq] and [dramatiq][dramatiq].

4. Run migration command to create the django-wfe models:

        python manage.py migrate

5. Run django-wfe `Watchdog` process to update your workflows during the runtime - this process will occupy the terminal

        python manage.py wfe_watchdog
        
6. In another terminal run django server - remember to export the needed envvars before execution! 

        python manage.py runserver

7. In yet another terminal run dramatiq - also here remember to export the needed envvars before execution! 

        python manage.py rundramatiq

## Usage

This project currently impements a simple workflow validating an uploaded file and processing it with your `fancy logic`.
To start your adventure go to the main page and upload a file using the form there (you may want to choose a small file - it will be uploaded to your temporary directory, but currently no mechanism deleting this file is implemented in the scope of django-wfe-project). On successful file upload you will be redirected to the status page of your upload - to update the status you need to refresh the page.

You can follow the impolemented logic in `django_wfe_integration.views.upload_file()` function. It's there where pretty much everything happens. Interesting for you may also be: `django_wfe_integration.workflows` and `django_wfe_integration.example_workflow_steps` files.

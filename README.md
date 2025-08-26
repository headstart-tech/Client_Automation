# GTCRM - BackEnd Server Module

<p align="center">
    <a href='https://fastapi.tiangolo.com/"'>
        <img src="https://img.shields.io/badge/Build%20With-FastAPI-brightgreen?style=flat-square">
    </a>
    <img src="https://teamcity.shiftboolean.com/app/rest/builds/buildType:id:Gtcrm_IntergerationBuild_TestSuiteBackend/statusIcon.svg" alt="TeamCity build status">
    <a href="">
        <img src="https://img.shields.io/static/v1?message=Python|3.11&logo=python&labelColor=5c5c5c&color=3776AB&logoColor=green&label=%20&&style=flat-square">
    </a>
	<a href="">
		<img src="https://img.shields.io/static/v1?message=Protected&logo=snyk&labelColor=white&color=green&logoColor=4C4A73&label=%20SNYK&style=flat-square">
	</a>
    <a href="">
		<img src="https://img.shields.io/static/v1?message=2.0.9&labelColor=white&color=green&logoColor=4C4A73&label=%20release&style=flat-square">
	</a>
    <a href="">
		<img src="https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white&style=flat-square">
	</a>
    
</p>

# Setup Instructions
## Prerequisites
Before you continue, ensure you have met the following requirements:

* You have installed the Python version 3.9<+. `Recommended 3.11`
* You are using a Linux or macOS machine.
* Windows with Python installed
* Recommended approach to use `virtualenv` or `Pipenv`
* Recommended IDE `Pycharm` or `Vscode`

* Virtual env setup on 🖥️ Linux or Macos

  _🔶 Virtual Env Setup_ 

  * 🚀 Create a `virtual environment` for this project
```shell
# creating virtual environment for python 3.9
$ python3.9 -m venv ~/.venvs/my-venv-name

# activating the virtual environment
$ source ~/.venvs/my-venv-name/bin/activate

# Check the Python version inside the venv:
(my-venv-name) $ python -V

# install all dependencies 
$ pip install -r requirements.txt
```
* Virtual env setup on 🖥️ Windows

  _ Virtual Env Setup_ 

  * 🚀 Create a `virtual environment` for this project
```shell
# creating virtual environment for python 3.11
$ python3 -m venv .venv

# activating the virtual environment
$ .\.venv\Scripts\activate

# Check the Python version inside the venv:
(venv) $ python -V

# install all dependencies 
$ pip install -r requirements.txt
```



* Create **PIPEnv Virtual Env**
  * 🚀 Create a `virtual environment` for this project

_🔶 Sample pipenv_ 
```shell
# creating pipenv environment for python 3
$ pipenv --three

# activating the pipenv environment
$ pipenv shell

# if you have multiple python 3 versions installed then
$ pipenv install -d --python 3.11

# install all dependencies (include -d for installing dev dependencies)
$ pipenv install -d
```

## Deployments Environments

### 🚀 Dev Environments

🚧 Dev environments contains all developments deployment helps to test development area . 

🔨 API -- https://dev.shiftboolean.com/docs

🔨 Student Dashboard -- https://dev1.shiftboolean.com/docs

🔨 Admin Dashboard  -- https://dev2.shiftboolean.com/docs

### 🚀 Staging Environments

🚧 Staging environments contains all pre-release deployment . 
Before release test can be made here
Database is same as dev environment to maintain stability 

⚡ API -- https://stage.shiftboolean.com/docs

⚡ Student Dashboard -- https://stage1.shiftboolean.com/docs

⚡ Admin Dashboard  -- https://stage2.shiftboolean.com/docs



## Project Structure

If you are building an application or a web API, it's rarely the case that you can put everything on a single file.

FastAPI provides a convenience tool to structure your application while keeping all the flexibility.

> _If you come from Flask, this would be the equivalent of Flask's Blueprints._

```shell
.
├── app                                             # "app" is a Python package
│   ├── __init__.py                                 # this file makes "app" a "Python package"
│   ├── main.py                                     # "main" module, e.g. import app.main
│   ├── background_task                             # modules of all the background task
│   │   ├── amazon_ses                              # amazon server related settings
│   │   │   └── configuration.py                    # configurations of amazon
│   │   ├── __init__.py
│   │   ├── admin_user.py                           # admin user related background task module
│   │   ├── college.py                              # college related background task module
│   │   ├── counselor_task.py                       # counsellor background task
│   │   └── doc_text_extraction.py                  # uploaded document text extraction for validation
│   ├── celery_tasks                                # celery task modules
│   │   │── __init__.py
│   │   ├── celery_add_user_timeline.py             # add user timeline automatic task module
│   │   ├── celery_email_activity.py                # automatic email task module
│   │   └── celery_send_mail.py                     # mail sending with celery module
│   ├── core                                        # common useable functions and task
│   │   ├── settings                                # core settings of project
│   │   ├── log_config.py                           # log creation configuration
│   │   ├── utils.py                                # data validation related functions
│   │   ├── zoom_api_config.py                      # zoom module configuration settings
│   │   └── celery_app.py                           # celery core configuration
│   ├── database                                    # database configuration related functions and modules
│   │   ├── __init__.py 
│   │   ├── configuration.py                        # connection of database with projects
│   │   ├── database_sync.py                        # synchronus connection with database
│   │   └── master_db_connection.py                 # connection with db for common database connectivity
│   ├── dependencies                                # "dependencies" module, e.g. import app.dependencies
│   │   ├── __init__.py
│   │   ├── celery_worker_status.py                 # celery related core funcitons
│   │   ├── college.py                              # college related core functions
│   │   ├── cryptography.py                         
│   │   ├── hashing.py
│   │   ├── jwttoken.py                             # jwt token creation related functions
│   │   ├── oauth.py                                # oauth configuration
│   │   └── security_auth.py
│   ├── helper                                      # Crud function for different modules API's
│   │   ├── qa_manager_helper                       # QA manager module related required crud functions
│   │   │   ├── __init__.py
│   │   │   ├── call_list.py
│   │   │   └── counsellor_reviews.py
│   │   ├── report
│   │   ├── resource
│   │   ├── student_curd
│   │   ├── tawk_webhook                            # tawk integration for webhook functions
│   │   ├── templates
│   │   ├── whatsapp_sms_activity
│   │   ├── notification                            # notification related funcitons
│   │   └── automation
│   ├── routers                                     # "routers" is a "Python subpackage"
│   │   ├── __init__.py                             # makes "routers" a "Python subpackage"
│   │   └── api_v1                                  # all api first router for request and response
│   │       ├── __init__.py
│   │       ├── app.py                              # first routing files for all API's
│   │       └── routes                              # collection of all modules in project
│   │           ├── __init__.py
│   │           ├── application_routes.py           # application related all modules api
│   │           ├── authentication_routes.py
│   │           ├── call_activity_routes.py
│   │           ├── colleges_routes.py              # college related all modules api
│   │           ├── courses_routes.py
│   │           ├── tawk_routes.py
│   │           ├── qa_manager_routes.py
│   │           └── admin_routes.py
│   ├── models                                      # "models" is a "Python subpackage"
│   │   ├── __init__.py                             # makes "models" a "Python subpackage"
│   │   └── applications.py                         # "applications" submodule, e.g. import app.models.applications
│   ├── tests                                       # test cases for entire apis

```

```shell

░▒▓   ✔  ▓▒░
.
├── app                        # "app" is a core directory containing all project files
│   ├── __init__.py            # this file makes "app" a "Python package"
│   ├── __pycache__             
│   ├── background_task        # Background task related package
│   ├── core                   # "core" Application core and utilities
│   ├── database               # "database" modules help for database connection and jobs
│   ├── dependencies           # "dependencies" module,Authentication related package
│   ├── helpers                # Helper files  
│   ├── main.py                # "main" module, e.g. import app.main
│   ├── models                 # starlet models for database
│   ├── routers                # Contains all routers
│   ├── s3_events              # S3 Related Codes
│   ├── secret.key             # Key is useful and generated . It should be same in order to compare password with database
│   ├── templates              # HTML templates used when sending email
│   └── tests                  # Stores all the tests
├── pytest.ini                 # This files setup test cases to execute only in asyncio mode only 
├── README.md                  # Project setup documentations
├── requirements.txt           # required python liberaries list for project
├── test_main.http
├── config.toml                # stores all the secret keys and credintials used in our project for connectivity or requests.

```
> There are several `__init__.py` files: one in each directory or subdirectory.
> 
>This is what allows importing code from one file into another.
> 
>For example, in `app/main.py` you could have a line like:
> 
>`from app.routers import StudentRouter`

* The app directory contains everything. And it has an empty file `app/__init__.py`, so it is a "Python package" (a collection of "Python modules"): `app`.
* It contains an `app/main.py` file. As it is inside a Python package (a directory with a file `__init__.py`), it is a "module" of that package: `app.main`.
* There's also an `app/dependencies.py` file, just like `app/main.py`, it is a "module": `app.dependencies`.
* There's a subdirectory `app/routers/` with another file `__init__.py`, so it's a "Python subpackage": `app.routers`.
* The file `app/routers/users.py` is inside a package, app/routers/, so, it's a submodule: `app.routers.users`.
* The same with any .py file `app/routers/<any>.py`, it's another submodule: `app.routers.<any>`.





## Environment Variables
> :warning: **Locate secert crenditals from team**: Be very careful here!**** These are secret credentials 

To run this project, you will need to add the following environment variables to your `config.toml` file within `root` directory

```yml
[general]
first_superuser = "**"
first_superuser_password = "********"
environment = "**********"
log_level = "****"

[master_db]
db_username = "****"
db_password = "************"
db_url = "************"
db_name = "**********"

[base_path]
base_path_api = "http://127.0.0.1:8000/"
base_path = "dev1.shiftboolean.com"
base_admin_path = "http://127.0.0.1:8000/"

[random]
password_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz"
random_otp = "1234567890987654321"
random_name = "1234567890abcdefghijklmnopqrstuvwxyz"

[authentication]
secret_key_auth = "******************"
algorithm = "HS256"

[testing]
test = false

[Google_recaptcha]
captcha_site_key = "********************************"
captcha_secret_key = "******************&&************"

[redis_server]
redis_server_url = "************************************"

[teamcity_credential]
teamcity_base_path = "https://teamcity.shiftboolean.com"
teamcity_build_type = "**************************"
teamcity_token = "************************************************************************************************************"

[env]
aws_env = "dev"
```
>> [Environment File](https://shiftboolean.slack.com/archives/C02UC932MGC/p1660895636797369)

## Development

To deploy this project run or execute main.py file

🚥 Execution with single runner on Windows 
```shell
 $ python3 .\app\main.py
```

🚥 Execution with multiple runner will only work on Linux or MacOS
```shell
 $ python3 .\app\main.py
```
> Multiple workers are not supported on Windows 

✅ Output like this should be expected
```shell
INFO:app.core.utils:Attempting to establish a connection to Redis...
INFO   2024-01-11 12:39:33,625 - app.core.utils - MainThread - Attempting to establish a connection to Redis... (celery_app.py:34)
INFO:app.core.utils:Connected to Redis successfully!
INFO   2024-01-11 12:39:34,271 - app.core.utils - MainThread - Connected to Redis successfully! (celery_app.py:37)
INFO:app.core.utils:Attempting to establish a connection to Redis...
INFO   2024-01-11 12:39:39,920 - app.core.utils - MainThread - Attempting to establish a connection to Redis... (celery_app.py:34)
INFO:app.core.utils:Connected to Redis successfully!
INFO   2024-01-11 12:39:40,389 - app.core.utils - MainThread - Connected to Redis successfully! (celery_app.py:37)
INFO:app.core.utils:Attempting to establish a connection to Redis...
INFO   2024-01-11 12:39:41,908 - app.core.utils - MainThread - Attempting to establish a connection to Redis... (celery_app.py:34)
INFO:app.core.utils:Connected to Redis successfully!
INFO   2024-01-11 12:39:42,465 - app.core.utils - MainThread - Connected to Redis successfully! (celery_app.py:37)
INFO:     Started server process [15548]
INFO:     Waiting for application startup.
INFO:app.core.utils:Attempting to establish a connection to Redis...
INFO   2024-01-11 12:39:56,292 - app.core.utils - MainThread - Attempting to establish a connection to Redis... (celery_app.py:34)
INFO:app.core.utils:Connected to Redis successfully!
INFO   2024-01-11 12:39:56,971 - app.core.utils - MainThread - Connected to Redis successfully! (celery_app.py:37)
INFO:app.routers.api_v1.app:Connected to Redis successfully!
INFO   2024-01-11 12:39:57,414 - app.routers.api_v1.app - MainThread - Connected to Redis successfully! (app.py:409)
INFO:app.routers.api_v1.app:Operating system = win32 and workers disabled
INFO   2024-01-11 12:39:57,418 - app.routers.api_v1.app - MainThread - Operating system = win32 and workers disabled (app.py:430)
INFO:app.routers.api_v1.app:Connected to Database.
INFO   2024-01-11 12:39:57,423 - app.routers.api_v1.app - MainThread - Connected to Database. (app.py:431)
WARNING:app.helpers.notification.real_time_configuration:User not found, skipping sending notifications.
WARNING 2024-01-11 12:39:57,427 - app.helpers.notification.real_time_configuration - MainThread - User not found, skipping sending notifications. (real_time_configuration.py:31)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

```

## Testing 
**Is Testing important ? Answer is Yes**
Developer don't know which part of our codebase may break! 
We use unit tests mostly for a single purpose. 
It works as documentation, By designing a unit test We help fellow developers, 
how exactly this new feature should work.
For more info read [here](https://sbwiki.atlassian.net/wiki/spaces/GTCRM/pages/2898722817/Properly+setup+of+Test+Enviroment)

To run test 

```bash
  pytest -v app/tests
```

## Creating PR for Release

_Update Release version in query parameters_

[Use Query Parameters to fetch Release Pull request Section
](https://github.com/shiftboolean/GTCRM-backend/compare/master...release/1.1.0?template=release_template.md
)
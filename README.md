# MHcut Browser

A web application for viewing, filtering, and searching CRISPR annotation TSV
data.



## Authors

* David Lougheed ([david.lougheed@mail.mcgill.ca](mailto:david.lougheed@mail.mcgill.ca))
    * Wrote the original web application.



## Overview

TODO



## Requirements

### Python 3

Python 3.5 or later is needed to run the application server and database-
generating script. See the `requirements.txt` file for required packages.


### NPM

NPM version 6 or later is required to install front-end dependencies for the
web application.



## Usage

### Step 0: Initial Setup

All the sub-steps outlined here are contained in a single script, `setup.bash`,
which can be run with the following command in the root of the project
directory:

```bash
bash ./setup.bash
```

This script will prompt the user for a choice of web server software to be
installed; either Apache 2 or NGINX can be chosen.

If some of the dependencies are already installed on the host machine, or if
different install paths or installation methods are required, it is suggested
that the installation steps are completed manually (see directly below).

#### Install Various Dependencies

##### Python

Make sure the `python3`, `python3-dev`, and `python3-pip` packages are
installed on the host system. They can be installed on a Debian-based system
with the following commands:

```bash
sudo apt update
sudo apt install python3 python3-dev python3-pip
```

##### Web Server

A web server software is used to serve the application's static files and as a
proxy for the web application itself. This project supports both the NGINX
and Apache 2 server software, although it may be possible for others to work as
well.

To install **NGINX** on a Debian-based system:
```bash
sudo apt install nginx
```

To install **Apache 2** on a Debian-based system, and enable the required
modules:
```bash
sudo apt install apache2 libapache2-mod-wsgi-py3
sudo a2enmod wsgi
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod rewrite
sudo systemctl restart apache2
```

##### Postgres

MHcut Browser uses Postgres as a database in order to efficiently perform
complex queries on the data.

To install Postgres, use the following command:

```bash
sudo apt install postgresql postgresql-contrib
```

##### NPM

Install NPM via your method of choice (caution; the version in Aptitude
repositories is often out of date) and make sure it is updated to at least
version 6.

Using external NodeJS Aptitude repositories, this can be done with the
following commands:

```bash
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt install nodejs
sudo npm install -g npm  # Update NPM to the latest version
npm -v  # The version should be at least 6.x.x
```

#### Set Up Python Virtual Environment

Create a Python 3 virtual environment in the main project directory with the
following commands, ran from the root project directory:

```bash
sudo -H pip3 install virtualenv  # If not done so already, install Python virtualenv
virtualenv -p python3 ./env
source env/bin/activate
pip install -r requirements.txt
```

#### Install Web Dependencies

Install all dependencies required for the web application with the following
commands, starting from the root project directory:

```bash
cd web
npm install
cd ..
```


### Step 1: Create the Database and Postgres User

First, create a Postgres user for the application to use in order to access the
data by opening a new `psql` session and issuing a `CREATE ROLE` command,
specifying the database role's password:

```bash
sudo -u postgres psql
```

```postgresql
CREATE ROLE mhcut LOGIN PASSWORD 'some_password';
```

This will prompt the user for a username (for example, one could enter `mhcut`)
and whether the new user should be a super user (it should **not**).

Then, create a database in the `psql` session and enable the trigram extension
on the database for indexing purposes:

```postgresql
CREATE DATABASE mhcut_db WITH OWNER mhcut;
\c mhcut_db
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Finally, edit the `pg_hba.conf` file (usually found in the
`/etc/postgresql/10/main/` directory), adding the following line, and
restart the database:

Before:
```
local   all             postgres                                peer

# TYPE  DATABASE        USER            ADDRESS                 METHOD
```

After:
```
local   all             postgres                                peer

# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             mhcut                                   md5
```

Restart:
```bash
sudo systemctl restart postgresql
```


### Step 2: Build the Database

To build the database, run the `tsv_to_postgres.py` script as follows to
generate the `db.sqlite` relational database file, passing in the desired TSV
files to convert as arguments, as well as the name of the created database and
database user:

```bash
python ./tsv_to_postgres.py variants.tsv guides.tsv cartoons.tsv mhcut_db mhcut
```

This will prompt the user for the database user's password before building the
MHcut Browser database.

**Warning:** The database construction process will take quite a while
(~30 minutes). The resulting database is typically around **20-60 gigabytes**.


### Step 3: Running the Web Application

#### In Development

TODO: FIGURE OUT DEPLOYMENT UNDER NGINX!!!!!

##### A. Activate the Virtual Environment

If not already in the virtual environment, activate it by running the following
command from within the root project directory:

```bash
source env/bin/activate
```

##### B. *Option 1:* Configure NGINX

Either alter the default configuration file (for `localhost`) or create a new
virtual host specifically for the application and register a local domain name
in the `/etc/hosts` file on the development machine.

Example configuration file, located in `/etc/nginx/sites-available/`:
```nginx
server {
	listen 80;

	root /path/to/mhcut/browser/web;
	index index.html index.htm;

	server_name your-domain-name.local;

	location /api/ {
		proxy_pass http://localhost:5000/;
	}

	location / {
		try_files $uri $uri/ /index.html;
	}
}
```

If a new virtual host configuration file has been created, enable the virtual
host by running the following commands, replacing `conf-name` with the name of
the newly-created configuration file, and restarting NGINX:

```bash
ln -s /etc/nginx/sites-available/conf-name /etc/nginx/sites-enabled/conf-name
nginx -t  # Optional, tests the configuration and informs the user if it's OK
sudo systemctl restart nginx
```

##### B. *Option 2:* Configure Apache

Either alter the default configuration file (for `localhost`) or create a new
virtual host specifically for the application and register a local domain name
in the `/etc/hosts` file on the development machine.

Example configuration file, located in `/etc/apache2/sites-available/`:
```
<VirtualHost *:80>
    ServerName your-domain-name.local

    ServerAdmin webmaster@localhost
    DocumentRoot /path/to/mhcut/browser/web

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory /path/to/mhcut/browser/web>
        Require all granted

        RewriteEngine on
        # Don't rewrite files or directories
        RewriteCond %{REQUEST_FILENAME} -f [OR]
        RewriteCond %{REQUEST_FILENAME} -d
        RewriteRule ^ - [L]
        # Rewrite everything else to index.html to allow html5 state links
        RewriteRule ^ index.html [L]
    </Directory>

    ProxyPass /api/ http://127.0.0.1:5000/
    ProxyPassReverse /api/ http://127.0.0.1:5000/
</VirtualHost>
```

If a new virtual host configuration file (for example `mcgill-network.conf`)
has been created, enable the virtual host by running the following commands,
replacing `mcgill-network` with the name of the newly-created configuration
file, and restarting Apache:

```bash
sudo a2ensite mcgill-network
sudo systemctl restart apache2
```


##### C. Build the JavaScript Bundle

In this case, the development-environment bundle is built, to aid in debugging.
This should be ran from the main project directory.

```bash
cd web
npm run build-dev
cd ..
```

If continuous development is being done on the JavaScript parts of the web
application, the webpack watcher (which continuously compiles the code as it is
changed) can be started with the following command, within the `web`
directory:

```bash
npm run watch
```

This will run continuously, waiting for changes in the `web/src` directory,
until it is killed with `Ctrl-c` or similar.

##### D. Run the Development API Server

Run the following commands from the root project directory to start the
development server:

```bash
export FLASK_APP=application.py
export FLASK_ENV=development

DB_NAME=mhcut_db DB_USER=mhcut DB_PASSWORD=your_db_password flask run
```

To check if the server is running, visit
[localhost:5000](http://localhost:5000/). The URL should give a JSON response
with some of the entries from the database.

If it is not running, check the terminal in which the server is running for
any possible error messages.

#### In Production

TODO: FIGURE OUT DEPLOYMENT UNDER NGINX AND ADD INSTRUCTIONS FOR EDITING
`wsgi.py`!!!!!

In production, the McGill Network web application is designed to be deployed
with uWSGI and NGINX as a systemd service.

##### A. Perform Initial Setup and Configuration

See Step 0 for details.

##### B. *Option 1:* Configure NGINX

In production, it is recommended to create a new virtual host specifically for
the application.

Example configuration, located in `/etc/nginx/sites-available/`:
```nginx
server {
	listen 80;

	root /path/to/mhcut/browser/web;
	index index.html index.htm;

	server_name your-domain-name.com;

	location /api/ {
		include uwsgi_params;
		uwsgi_pass unix:/path/to/mhcut/browser/mcb.sock;
		uwsgi_param SCRIPT_NAME /api/;
	}

	location / {
		try_files $uri $uri/ /index.html;
	}
}
```

If a new virtual host configuration file has been created, enable the virtual
host by running the following command, replacing `conf-name` with the name of
the newly-created configuration file, and restarting NGINX:

```bash
ln -s /etc/nginx/sites-available/conf-name /etc/nginx/sites-enabled/conf-name
nginx -t # Optional, tests the configuration and informs the user if it's OK
sudo systemctl restart nginx
```

##### B. *Option 2:* Configure Apache

In production, it is recommended to create a new virtual host specifically for
the application.

Example configuration, located in `/etc/apache2/sites-available/`:
```
<VirtualHost *:80>
    ServerName your-domain-name.com

    ServerAdmin webmaster@localhost
    DocumentRoot /path/to/mhcut/browser/web

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory /path/to/mhcut/browser/web>
        Require all granted

        RewriteEngine on
        # Don't rewrite files or directories
        RewriteCond %{REQUEST_FILENAME} -f [OR]
        RewriteCond %{REQUEST_FILENAME} -d
        RewriteRule ^ - [L]
        # Rewrite everything else to index.html to allow html5 state links
        RewriteRule ^ index.html [L]
    </Directory>

    <Directory /path/to/mhcut/browser>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess mcb python-home=/path/to/mhcut/browser/env python-path=/path/to/mhcut/browser
    WSGIProcessGroup mcb
    WSGIScriptAlias /api /path/to/mhcut/browser/wsgi.py
</VirtualHost>
```

If a new virtual host configuration file (for example `mcgill-network.conf`)
has been created, enable the virtual host by running the following commands,
replacing `mcgill-network` with the name of the newly-created configuration
file, and restarting Apache:

```bash
sudo a2ensite mcgill-network
sudo systemctl restart apache2
```

###### Setting Up Database Credentials

In order to run the server in an Apache 2 production environment, the `wsgi.py`
file must be edited to contain the production database name and credentials.
Change the following variables to contain the production values, within the
quotes:

```python
os.environ["DB_NAME"] = "your_production_db_name"
os.environ["DB_USER"] = "your_production_db_user"
os.environ["DB_PASSWORD"] = "your_production_db_password"
```

Then, restart Apache with the following command:

```bash
sudo systemctl restart apache2
```

##### C. Build the JavaScript Bundle

In this case, the production-environment bundle is built. This must be run from
the product directory.

```bash
cd static
npm install
npm run build
cd ..
```

##### D. *(for NGINX only)* Configure Project `systemd` Service

First, edit the example `mcb.example.service` file to match the paths the
application is being served out of.

Then, copy the example `mcb.example.service` file to the `systemd` services
folder as follows:

```bash
cp ./mcb.example.service /etc/systemd/system/mcb.service
```

Finally, start the service and enable it to start at boot time:

```bash
sudo systemctl start mcb
sudo systemctl enable mcb
```

To check if the software is running, visit
[localhost:5000](http://localhost:5000/). The URL should give a JSON response
with some of the entries from the database.

If it is not running, make sure the service started correctly with the
following command:

```bash
sudo systemctl status mcb
```

If a `502` HTTP error appears, check if the socket path is correct in the NGINX
configuration and the service user is correct in the systemd service file.

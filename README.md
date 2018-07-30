# CRISPR Browser

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

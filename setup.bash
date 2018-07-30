#!/usr/bin/env bash

set -eu

if ! [ -x "$(command -v python3)" ]; then
  echo "Attempting to install Python 3 via apt..."
  sudo apt-get install -y python3 python3-dev
fi

if ! [ -x "$(command -v pip3)" ]; then
    echo "Attempting to install pip3 via apt..."
    sudo apt-get install -y python3-pip
fi

if ! [ -x "$(command -v virtualenv)" ]; then
    echo "Attempting to install virtualenv via pip..."
    sudo -H pip3 install virtualenv
fi

read -p "Server software to install (apache2 or [nginx]): " server

if [ "$server" == "apache2" ]; then
  if ! [ -x "$(command -v apache2)" ]; then
    echo "Attempting to install Apache via apt..."
    sudo apt-get install -y apache2 libapache2-mod-wsgi-py3
    echo "Enabling required Apache modules..."
    sudo a2enmod wsgi proxy proxy_http rewrite
    sudo systemctl restart apache2
  fi
else
    if ! [ -x "$(command -v nginx)" ]; then
      echo "Attempting to install NGINX via apt..."
      sudo apt-get install -y nginx
    fi
fi

if ! [ -x "$(command -v npm)" ]; then
  echo "Attempting to install NPM from nodesource via apt..."
  curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "Updating NPM to the latest version..."
sudo npm install -g npm

echo "Setting up Python 3 virtual environment in project root..."
virtualenv -p python3 ./env
source env/bin/activate
pip install -r requirements.txt

echo "Installing web dependencies via NPM..."
cd web
npm install
echo "Building JavaScript bundle..."
npm run build-dev
cd ..

echo "Setup complete."
echo

echo "Please activate the virtual environment by running the following:"
echo "    source env/bin/activate"
echo

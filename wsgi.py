#!/usr/bin/env python3

import os

from application import app as application

os.environ["DB_USER"] = "your_production_db_user"
os.environ["DB_PASSWORD"] = "your_production_db_password"

if __name__ == "__main__":
    application.run()

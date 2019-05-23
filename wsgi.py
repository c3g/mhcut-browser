#!/usr/bin/env python3

import os

from application import app as application

os.environ["DB_NAME"] = "your_production_db_name"
os.environ["DB_USER"] = "your_production_db_user"
os.environ["DB_PASSWORD"] = "your_production_db_password"

os.environ["SENDGRID_API_KEY"] = "your_production_sendgrid_api_key"
os.environ["BUG_REPORT_EMAIL"] = "your_production_bug_report_email"

if __name__ == "__main__":
    application.run()

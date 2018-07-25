#!/usr/bin/env python3

import re
import sqlite3
from flask import Flask, g, json, request
from typing import Pattern

CHR_DOMAIN = re.compile("^(chr(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|X|Y)|any)$")
POS_INT_DOMAIN = re.compile("^[1-9]\d*")
SORT_ORDER_DOMAIN = re.compile("^(ASC|DESC)$")

app = Flask(__name__)


class DomainError(Exception):
    """
    Error to be thrown if a variable's value falls outside of its domain.
    """
    pass


def verify_domain(value, domain: Pattern):
    if re.match(domain, str(value)):
        return value
    raise DomainError


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("db.sqlite")
        db.row_factory = sqlite3.Row
    return db


@app.route("/", methods=["GET"])
def index():
    page = int(verify_domain(request.args.get("page", "1"), POS_INT_DOMAIN))
    items_per_page = int(verify_domain(request.args.get("items_per_page", "100"), POS_INT_DOMAIN))
    chromosome = verify_domain(request.args.get("chr", "any"), CHR_DOMAIN)
    c = get_db().cursor()
    c.execute("PRAGMA table_info(variants)")
    columns = [dict(i)["name"] for i in c.fetchall()]
    sort_by = verify_domain(request.args.get("sort_by", "id"), re.compile("^({})$".format("|".join(columns))))
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)
    c.execute(
        "SELECT * FROM variants WHERE chr = :chr OR :chr = 'any' ORDER BY {} {} "
        "LIMIT :items_per_page OFFSET :start".format(sort_by, sort_order),
        {
            "start": (page - 1) * items_per_page,
            "chr": chromosome,
            "items_per_page": items_per_page
        }
    )
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/entries", methods=["GET"])
def pages():
    c = get_db().cursor()
    c.execute("SELECT COUNT(*) FROM variants")
    count = c.fetchone()[0]
    return json.jsonify(count)


@app.route("/fields", methods=["GET"])
def fields():
    c = get_db().cursor()
    c.execute("PRAGMA table_info(variants)")
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/metadata", methods=["GET"])
def metadata():
    c = get_db().cursor()
    c.execute("SELECT MIN(start) AS min_pos, MAX(end) AS max_pos FROM variants")
    return json.jsonify(dict(c.fetchone()))


@app.teardown_appcontext
def close_connection(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run()

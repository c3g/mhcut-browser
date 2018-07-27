#!/usr/bin/env python3

import json as pyjson
import re
import sqlite3

from flask import Flask, g, json, request
from typing import Pattern


# Search Operator / Condition Domains
SEARCH_OPERATORS = {
    "equals": ("=", "{}"),

    # TEXT
    "contains": ("LIKE", "%{}%"),
    "starts_with": ("LIKE", "{}%"),
    "ends_with": ("LIKE", "%{}"),

    # INTEGER
    "<": ("<", "{}"),
    "<=": ("<=", "{}"),
    ">": (">", "{}"),
    ">=": (">=", "{}")
}

# Domain lists for metadata endpoint
CHR_VALUES = ("chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9", "chr10",
              "chr11", "chr12", "chr13", "chr14", "chr15", "chr16", "chr17", "chr18", "chr19",
              "chr20", "chr21", "chr22", "chrX", "chrY")

# Domains
CHR_DOMAIN = re.compile("^(chr(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|X|Y)|any)$")
POS_INT_DOMAIN = re.compile("^[1-9]\d*")
SORT_ORDER_DOMAIN = re.compile("^(ASC|DESC)$")

app = Flask(__name__)


class DomainError(Exception):
    """
    Error to be thrown if a variable's value falls outside of its domain.
    """
    pass


def get_columns(c):
    c.execute("PRAGMA table_info(variants)")
    return tuple([dict(i) for i in c.fetchall()])


def verify_domain(value, domain: Pattern):
    if re.match(domain, str(value)):
        return value
    raise DomainError


def search_param(c):
    return "search_cond_{}".format(str(c).strip())


def build_search_query(raw_query, c):
    columns = get_columns(c)
    column_names = [c["name"] for c in columns]
    search_query_fragment = ""
    search_query_data = {}

    try:
        query_obj = json.loads(raw_query)
        for c in query_obj:
            if c["field"] not in column_names:
                continue
            if c["operator"] not in SEARCH_OPERATORS.keys():
                continue
            op_data = SEARCH_OPERATORS[c["operator"]]
            if search_query_fragment != "":
                search_query_fragment += " {} ".format(c["boolean"])
            search_query_fragment += "{} {} :{}".format(c["field"], op_data[0], search_param(c["id"]))
            search_query_data[search_param(c["id"])] = op_data[1].format(c["value"])

    except (pyjson.decoder.JSONDecodeError, AttributeError):
        search_query_fragment = " OR ".join(["CAST({} AS TEXT) LIKE :{}".format(c["name"], search_param(c["name"]))
                                             for c in columns])
        search_query_data = {search_param(c["name"]): "%{}%".format(raw_query.strip()) for c in columns}

    return search_query_fragment, search_query_data


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
    columns = get_columns(c)
    column_names = [i["name"] for i in columns]

    search_query_fragment, search_query_data = build_search_query(request.args.get("search_query", ""), c)

    sort_by = verify_domain(request.args.get("sort_by", "id"), re.compile("^({})$".format("|".join(column_names))))
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    c.execute(
        "SELECT * FROM variants WHERE (chr = :chr OR :chr = 'any') AND ({}) ORDER BY {} {} "
        "LIMIT :items_per_page OFFSET :start".format(search_query_fragment, sort_by, sort_order),
        {
            "start": (page - 1) * items_per_page,
            "chr": chromosome,
            "items_per_page": items_per_page,
            **search_query_data
        }
    )
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/entries", methods=["GET"])
def pages():
    chromosome = verify_domain(request.args.get("chr", "any"), CHR_DOMAIN)

    c = get_db().cursor()
    search_query_fragment, search_query_data = build_search_query(request.args.get("search_query", ""), c)
    c.execute(
        "SELECT COUNT(*) FROM variants WHERE (chr = :chr OR :chr = 'any') AND ({})".format(search_query_fragment),
        {
            "chr": chromosome,
            **search_query_data
        }
    )
    count = c.fetchone()[0]
    return json.jsonify(count)


@app.route("/fields", methods=["GET"])
def fields():
    return json.jsonify(get_columns(get_db().cursor()))


@app.route("/metadata", methods=["GET"])
def metadata():
    c = get_db().cursor()
    c.execute("SELECT MIN(start) AS min_pos, MAX(end) AS max_pos FROM variants")
    return json.jsonify({
        **dict(c.fetchone()),
        "chr": CHR_VALUES
    })


@app.teardown_appcontext
def close_connection(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run()

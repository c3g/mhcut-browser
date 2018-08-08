#!/usr/bin/env python3

import json as pyjson
import os.path
import re
import sqlite3

from flask import Flask, g, json, request, Response
from typing import Pattern


BASE_DIR = os.path.dirname(__file__)

# Version for Metadata Endpoint
__version__ = json.load(open(os.path.join(BASE_DIR, "web/package.json"), "r"))["version"]


# Database Setup
DATABASE_PATH = os.path.join(BASE_DIR, "db.sqlite")


# Search Operator / Condition Domains
SEARCH_OPERATORS = {
    "equals": ("=", "{}"),
    "<": ("<", "{}"),
    "<=": ("<=", "{}"),
    ">": (">", "{}"),
    ">=": (">=", "{}"),

    # TEXT
    "contains": ("LIKE", "%{}%"),
    "starts_with": ("LIKE", "{}%"),
    "ends_with": ("LIKE", "%{}"),

    # NULLABLE
    "is_null": ("IS NULL", "")
}

POSITION_OPERATORS = {
    "overlap": "end >= :start_pos AND start <= :end_pos ",
    "not_overlap": "end < :start_pos OR start > :end_pos",
    "within": "start >= :start_pos AND end <= :end_pos"
}

# Domain lists for metadata endpoint
CHR_VALUES = ("chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9", "chr10",
              "chr11", "chr12", "chr13", "chr14", "chr15", "chr16", "chr17", "chr18", "chr19",
              "chr20", "chr21", "chr22", "chrX", "chrY")
GENELOC_VALUES = ("intronic", "exonic", "intergenic")

# Domains
CHR_DOMAIN = re.compile("^(chr(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|X|Y)|any)$")
POS_INT_DOMAIN = re.compile("^[1-9]\d*$")
NON_NEG_INT_DOMAIN = re.compile("^\d+$")
BOOLEAN_DOMAIN = re.compile("^(true|false)$")
POSITION_OPERATOR_DOMAIN = re.compile("^(overlap|not_overlap|within)$")
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


def search_param(c):
    return "search_cond_{}".format(str(c).strip())


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
    return db


def get_variants_columns(c):
    c.execute("PRAGMA table_info(variants)")
    return tuple([dict(i) for i in c.fetchall()])


def get_guides_columns(c):
    c.execute("PRAGMA table_info(guides)")
    return tuple([dict(i) for i in c.fetchall()])


def build_search_query(raw_query, c):
    columns = get_variants_columns(c)
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

            search_query_fragment += "({}({} {}".format("NOT " if c["negated"] else "", c["field"], op_data[0])

            if op_data[1] != "":
                search_query_fragment += " :{}".format(search_param(c["id"]))
                search_query_data[search_param(c["id"])] = op_data[1].format(c["value"])

            search_query_fragment += "))"

    except (pyjson.decoder.JSONDecodeError, TypeError, AttributeError):
        search_query_fragment = " OR ".join(["(CAST({} AS TEXT) LIKE :{})".format(c["name"], search_param(c["name"]))
                                             for c in columns])
        search_query_data = {search_param(c["name"]): "%{}%".format(raw_query.strip()) for c in columns}

    return search_query_fragment, search_query_data


def get_search_params_from_request(c):
    chromosomes = [ch for ch in request.args.get("chr", "").split(",") if re.match(CHR_DOMAIN, ch)]
    if len(chromosomes) == 0:
        chromosomes = list(CHR_VALUES)
    chr_fragment = "(" + ",".join(["'{}'".format(ch) for ch in chromosomes]) + ")"

    start_pos = int(verify_domain(request.args.get("start", "0"), NON_NEG_INT_DOMAIN))
    end_pos = int(verify_domain(request.args.get("end", "1000000000000"), POS_INT_DOMAIN))
    position_filter_operator = verify_domain(request.args.get("position_filter_operator", "overlap"),
                                             POSITION_OPERATOR_DOMAIN)
    position_filter_fragment = POSITION_OPERATORS[position_filter_operator]

    gene_locations = [l.strip() for l in request.args.get("geneloc", "").split(",") if l.strip() in GENELOC_VALUES]
    if len(gene_locations) == 0:
        gene_locations = list(GENELOC_VALUES)
    geneloc_fragment = "(" + ",".join(["'{}'".format(l) for l in gene_locations]) + ")"

    min_mh_l = int(verify_domain(request.args.get("min_mh_l", "0"), NON_NEG_INT_DOMAIN))

    dbsnp = int(verify_domain(request.args.get("dbsnp", "false"), BOOLEAN_DOMAIN) == "true")
    clinvar = int(verify_domain(request.args.get("clinvar", "false"), BOOLEAN_DOMAIN) == "true")

    search_query_fragment, search_query_data = build_search_query(request.args.get("search_query", ""), c)

    return {
        "chr_fragment": chr_fragment,

        "start_pos": start_pos,
        "end_pos": end_pos,

        "position_filter_fragment": position_filter_fragment,
        "geneloc_fragment": geneloc_fragment,

        "min_mh_l": min_mh_l,

        "dbsnp": dbsnp,
        "clinvar": clinvar,

        "search_query_fragment": search_query_fragment,
        "search_query_data": search_query_data
    }


@app.route("/", methods=["GET"])
def index():
    page = int(verify_domain(request.args.get("page", "1"), POS_INT_DOMAIN))
    items_per_page = int(verify_domain(request.args.get("items_per_page", "100"), POS_INT_DOMAIN))

    c = get_db().cursor()

    search_params = get_search_params_from_request(c)

    sort_by = verify_domain(
        request.args.get("sort_by", "id"),
        re.compile("^({})$".format("|".join([i["name"] for i in get_variants_columns(c)])))
    )
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    c.execute(
        "SELECT * FROM variants WHERE (chr IN {}) AND (geneloc IN {}) AND (mh_l >= :min_mh_l) "
        "AND NOT ((:dbsnp AND rs == '-') OR (:clinvar AND gene_info_clinvar IS NULL)) AND ({}) AND ({}) "
        "ORDER BY {} {} LIMIT :items_per_page OFFSET :start".format(
            search_params["chr_fragment"],
            search_params["geneloc_fragment"],
            search_params["position_filter_fragment"],
            search_params["search_query_fragment"],
            sort_by,
            sort_order
        ),
        {
            "start": (page - 1) * items_per_page,
            "items_per_page": items_per_page,
            "start_pos": search_params["start_pos"],
            "end_pos": search_params["end_pos"],
            "min_mh_l": search_params["min_mh_l"],
            "dbsnp": search_params["dbsnp"],
            "clinvar": search_params["clinvar"],
            **search_params["search_query_data"]
        }
    )
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/tsv", methods=["GET"])
def variants_tsv():
    c = get_db().cursor()

    search_params = get_search_params_from_request(c)

    column_names = [i["name"] for i in get_variants_columns(c)]
    sort_by = verify_domain(
        request.args.get("sort_by", "id"),
        re.compile("^({})$".format("|".join(column_names)))
    )
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    def generate():
        with app.app_context():
            c2 = get_db().cursor()

            c2.execute(
                "SELECT * FROM variants WHERE (chr IN {}) AND (geneloc IN {}) AND (mh_l >= :min_mh_l) "
                "AND NOT ((:dbsnp AND rs == '-') OR (:clinvar AND gene_info_clinvar IS NULL)) AND ({}) AND ({}) "
                "ORDER BY {} {}".format(
                    search_params["chr_fragment"],
                    search_params["geneloc_fragment"],
                    search_params["position_filter_fragment"],
                    search_params["search_query_fragment"],
                    sort_by,
                    sort_order
                ),
                {
                    "start_pos": search_params["start_pos"],
                    "end_pos": search_params["end_pos"],
                    "min_mh_l": search_params["min_mh_l"],
                    "dbsnp": search_params["dbsnp"],
                    "clinvar": search_params["clinvar"],
                    **search_params["search_query_data"]
                }
            )

            yield "\t".join(column_names) + "\n"
            row = c2.fetchone()
            while row is not None:
                yield "\t".join([str(col) if col is not None else "NA" for col in tuple(row)]) + "\n"
                row = c2.fetchone()

    return Response(generate(), mimetype="text/tab-separated-values",
                    headers={"Content-Disposition": "Content-Disposition: attachment; filename=\"export.tsv\""})


@app.route("/variants/<int:variant_id>/guides", methods=["GET"])
def variant_guides(variant_id):
    c = get_db().cursor()
    c.execute("SELECT * FROM guides WHERE variant_id = ?", (variant_id,))
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/guides", methods=["GET"])
def guides():
    page = int(verify_domain(request.args.get("page", "1"), POS_INT_DOMAIN))
    items_per_page = int(verify_domain(request.args.get("items_per_page", "100"), POS_INT_DOMAIN))

    c = get_db().cursor()

    search_params = get_search_params_from_request(c)

    sort_by = verify_domain(
        request.args.get("sort_by", "id"),
        re.compile("^({})$".format("|".join([i["name"] for i in get_variants_columns(c)])))
    )
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    # TODO: SORT GUIDES AS WELL

    c.execute(
        "SELECT * FROM guides WHERE variant_id IN ("
        "  SELECT id FROM variants WHERE (chr IN {}) AND (geneloc IN {}) AND (mh_l >= :min_mh_l) "
        "  AND NOT ((:dbsnp AND rs == '-') OR (:clinvar AND gene_info_clinvar IS NULL)) AND ({}) AND ({}) "
        "  ORDER BY {} {} LIMIT :items_per_page OFFSET :start"
        ")".format(
            search_params["chr_fragment"],
            search_params["geneloc_fragment"],
            search_params["position_filter_fragment"],
            search_params["search_query_fragment"],
            sort_by,
            sort_order
        ),
        {
            "start": (page - 1) * items_per_page,
            "items_per_page": items_per_page,
            "start_pos": search_params["start_pos"],
            "end_pos": search_params["end_pos"],
            "min_mh_l": search_params["min_mh_l"],
            "dbsnp": search_params["dbsnp"],
            "clinvar": search_params["clinvar"],
            **search_params["search_query_data"]
        }
    )
    return json.jsonify([dict(i) for i in c.fetchall()])


@app.route("/entries", methods=["GET"])
def entries():
    c = get_db().cursor()
    search_params = get_search_params_from_request(c)
    c.execute(
        "SELECT COUNT(*) FROM variants WHERE (chr IN {}) AND (geneloc IN {}) AND (mh_l >= :min_mh_l) "
        "AND NOT ((:dbsnp AND rs == '-') OR (:clinvar AND gene_info_clinvar IS NULL)) AND ({}) AND ({})".format(
            search_params["chr_fragment"],
            search_params["geneloc_fragment"],
            search_params["position_filter_fragment"],
            search_params["search_query_fragment"]
        ),
        {
            "start_pos": search_params["start_pos"],
            "end_pos": search_params["end_pos"],
            "min_mh_l": search_params["min_mh_l"],
            "dbsnp": search_params["dbsnp"],
            "clinvar": search_params["clinvar"],
            **search_params["search_query_data"]
        }
    )
    variant_count = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM guides WHERE variant_id IN ("
        "  SELECT id FROM variants WHERE (chr IN {}) AND (geneloc IN {}) AND (mh_l >= :min_mh_l) "
        "  AND NOT ((:dbsnp AND rs == '-') OR (:clinvar AND gene_info_clinvar IS NULL)) AND ({}) AND ({}))".format(
            search_params["chr_fragment"],
            search_params["geneloc_fragment"],
            search_params["position_filter_fragment"],
            search_params["search_query_fragment"]
        ),
        {
            "start_pos": search_params["start_pos"],
            "end_pos": search_params["end_pos"],
            "min_mh_l": search_params["min_mh_l"],
            "dbsnp": search_params["dbsnp"],
            "clinvar": search_params["clinvar"],
            **search_params["search_query_data"]
        }
    )
    return json.jsonify({
        "variants": variant_count,
        "guides": c.fetchone()[0]
    })


@app.route("/fields", methods=["GET"])
def fields():
    c = get_db().cursor()
    return json.jsonify({
        "variants": get_variants_columns(c),
        "guides": get_guides_columns(c)
    })


@app.route("/metadata", methods=["GET"])
def metadata():
    """
    Returns various metadata and summary statistics about the entries in the database. Does not respect filtering
    parameters.
    :return: A JSON response with metadata and summary statistics.
    """
    c = get_db().cursor()
    c.execute("SELECT MIN(start) AS min_pos, MAX(end) AS max_pos, MAX(mh_l) AS max_mh_l FROM variants")
    return json.jsonify({
        **dict(c.fetchone()),
        "chr": CHR_VALUES,
        "geneloc": GENELOC_VALUES,
        "version": __version__
    })


@app.teardown_appcontext
def close_connection(_exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


if __name__ == "__main__":
    app.run()

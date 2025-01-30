#!/usr/bin/env python3


# MHcut browser is a web application for browsing data from the MHcut tool.
# Copyright (C) 2018-2019  the Canadian Centre for Computational Genomics
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import datetime
import os
import os.path
import psycopg2
import psycopg2.extras
import re
import secrets
import smtplib

from email.message import EmailMessage
from flask import Flask, g, json, request, Response
from json.decoder import JSONDecodeError
from typing import Pattern


BASE_DIR = os.path.dirname(__file__)

# Version for Metadata Endpoint
__version__ = json.load(open(os.path.join(BASE_DIR, "web/package.json"), "r"))["version"]


DATASETS = {
    "cas": {
        "name": "Cas9",
        "database": os.environ.get("DB_NAME_CAS")
    },
    "xcas": {
        "name": "xCas9",
        "database": os.environ.get("DB_NAME_XCAS")
    }
}

DEFAULT_DATASET = "cas"
BUG_REPORT_DATASET = DEFAULT_DATASET


# Preferred Column Order
COLUMN_ORDER = ("id", "chr", "pos_start", "pos_end", "location", "rs", "gene_info", "clndn", "clnsig", "var_l",
                "flank", "mh_score", "mh_l", "mh_1l", "hom", "mh_max_cons", "mh_dist", "mh_1dist", "mh_seq_1",
                "mh_seq_2", "pam_mot", "pam_uniq", "guides_no_nmh", "cartoon", "caf", "topmed", "pm", "mc", "af_exac",
                "af_tgp", "allele_id", "dbvarid", "gene_info_clinvar", "mc_clinvar", "citation", "nbmm",
                "guides_min_nmh", "gc", "max_2_cuts_dist", "max_indelphi_freq_mean", "max_indelphi_freq_mesc",
                "max_indelphi_freq_u2os", "max_indelphi_freq_hek293", "max_indelphi_freq_hct116",
                "max_indelphi_freq_k562")


# Search Operator / Condition Domains
SEARCH_OPERATORS = {
    "equals": ("=", "{}"),
    "<": ("<", "{}"),
    "<=": ("<=", "{}"),
    ">": (">", "{}"),
    ">=": (">=", "{}"),

    # TEXT
    "contains": ("ILIKE", "%{}%"),
    "starts_with": ("ILIKE", "{}%"),
    "ends_with": ("ILIKE", "%{}"),

    # NULLABLE
    "is_null": ("IS NULL", "")
}

# Domain lists for metadata endpoint
CHR_VALUES = ("chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9", "chr10",
              "chr11", "chr12", "chr13", "chr14", "chr15", "chr16", "chr17", "chr18", "chr19",
              "chr20", "chr21", "chr22", "chrX", "chrY")
LOCATION_VALUES = ("intronic", "exonic", "intergenic", "utr")

# Domains
CHR_DOMAIN = re.compile(r"^(chr(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|X|Y)|any)$")
POS_INT_DOMAIN = re.compile(r"^[1-9]\d*$")
NON_NEG_INT_DOMAIN = re.compile(r"^\d+$")
BOOLEAN_DOMAIN = re.compile(r"^(true|false)$")
POSITION_OPERATOR_DOMAIN = re.compile(r"^(overlap|not_overlap|within)$")
SORT_ORDER_DOMAIN = re.compile(r"^(ASC|DESC)$")

app = Flask(__name__)

email_tokens = {}


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
    return f"search_cond_{str(c).strip()}"


def get_db(dataset="cas"):
    dbs = getattr(g, "databases", dict())
    if dataset not in dbs:
        g.databases = dict()
        dbs[dataset] = g.databases[dataset] = psycopg2.connect(f"dbname={DATASETS[dataset]['database']} "
                                                               f"user={os.environ.get('DB_USER')} "
                                                               f"password={os.environ.get('DB_PASSWORD')}")
    return dbs[dataset]


def get_variants_columns(c):
    c.execute("SELECT column_name, is_nullable, data_type FROM information_schema.columns "
              "WHERE table_schema = 'public' AND table_name = 'variants' AND column_name != 'full_row'")
    return tuple(sorted([dict(i) for i in c.fetchall()], key=lambda i: COLUMN_ORDER.index(i["column_name"])))


def build_variants_columns_domain(c):
    return re.compile(f"^({'|'.join([i['column_name'] for i in get_variants_columns(c)])})$")


def get_guides_columns(c):
    c.execute("SELECT column_name, is_nullable, data_type FROM information_schema.columns "
              "WHERE table_schema = 'public' AND table_name = 'guides'")
    return tuple([dict(i) for i in c.fetchall()])


def build_search_query(raw_query, c):
    search_query_fragment = ""
    search_query_data = {}

    try:
        column_names = [c["column_name"] for c in get_variants_columns(c)]

        query_obj = json.loads(raw_query)
        for c in query_obj:
            if c["field"] not in column_names:
                continue

            if c["operator"] not in SEARCH_OPERATORS.keys():
                continue

            op_data = SEARCH_OPERATORS[c["operator"]]

            if search_query_fragment != "":
                search_query_fragment += f" {c['boolean']} "

            search_query_fragment += f"({'NOT ' if c['negated'] else ''}({c['field']} {op_data[0]}"

            if op_data[1] != "":
                search_query_fragment += f" %({search_param(c['id'])})s"
                search_query_data[search_param(c["id"])] = op_data[1].format(c["value"])

            search_query_fragment += "))"

    except (JSONDecodeError, TypeError, AttributeError):
        if raw_query.strip() == "":
            return "true", search_query_data

        search_query_fragment = "full_row LIKE %(full_row_cond)s "
        search_query_data = {"full_row_cond": f"%{raw_query.strip().lower()}%"}

    return search_query_fragment, search_query_data


def get_search_params_from_request(c):
    # Ensure chromosomes match spec. Make chrx/chry into chrX/chrY.
    chromosomes = [ch.upper().replace("CHR", "chr") for ch in request.args.get("chr", ",".join(CHR_VALUES)).split(",")
                   if re.match(CHR_DOMAIN, ch.upper().replace("CHR", "chr"))]
    chr_fragment = "(" + ",".join([f"'{ch}'::CHROMOSOME" for ch in chromosomes]) + ")"
    if len(chromosomes) == 0:
        chr_fragment = "(" + ",".join([f"'{ch}'::CHROMOSOME" for ch in CHR_VALUES]) + ")"

    start_pos = int(verify_domain(request.args.get("start", "0"), NON_NEG_INT_DOMAIN))
    end_pos = int(verify_domain(request.args.get("end", "1000000000000"), POS_INT_DOMAIN))
    position_filter_fragment = ("pos_start <= %(end_pos)s AND pos_end >= %(start_pos)s"
                                if not (start_pos == 0 and end_pos == 1000000000000) else "true")

    gene_locations = [l.strip() for l in request.args.get("location", "").split(",") if l.strip() in LOCATION_VALUES]
    if len(gene_locations) == 0:
        gene_locations = list(LOCATION_VALUES)
    location_fragment = "(" + ",".join([f"'{l}'::VARIANT_LOCATION" for l in gene_locations]) + ")"

    min_mh_1l = int(verify_domain(request.args.get("min_mh_1l", "3"), NON_NEG_INT_DOMAIN))

    clinvar = verify_domain(request.args.get("clinvar", "false"), BOOLEAN_DOMAIN) == "true"

    ngg_pam_avail = verify_domain(request.args.get("ngg_pam_avail", "false"), BOOLEAN_DOMAIN) == "true"
    unique_guide_avail = verify_domain(request.args.get("unique_guide_avail", "false"), BOOLEAN_DOMAIN) == "true"

    search_query_fragment, search_query_data = build_search_query(request.args.get("search_query", ""), c)

    return {
        "chr": chromosomes,
        "chr_fragment": chr_fragment,

        "start_pos": start_pos,
        "end_pos": end_pos,

        "position_filter_fragment": position_filter_fragment,
        "location": gene_locations,
        "location_fragment": location_fragment,

        "min_mh_1l": min_mh_1l,

        "clinvar": clinvar,

        "ngg_pam_avail": ngg_pam_avail,
        "unique_guide_avail": unique_guide_avail,

        "search_query_fragment": search_query_fragment,
        "search_query_data": search_query_data
    }


def build_variants_query(c, selection, search_params, cartoons=False, sort_by=None, sort_order=None, page=None,
                         items_per_page=None, outer_query=True):
    outer_selection = (f"SELECT {selection} FROM variants "
                       f"{'LEFT JOIN cartoons ON id = variant_id' if cartoons else ''} "
                       f"WHERE id IN ") if outer_query else ""

    chr_in = f"(chr IN {search_params['chr_fragment']}) AND " if len(search_params["chr"]) < len(CHR_VALUES) else ""
    loc_in = (f"(location IN {search_params['location_fragment']}) AND "
              if len(search_params["location"]) < len(LOCATION_VALUES) else "")
    mh_1l = "(mh_1l >= %(min_mh_1l)s) AND " if search_params["min_mh_1l"] > 0 else ""

    limit = "LIMIT %(items_per_page)s " if items_per_page is not None else ""
    offset = "OFFSET %(start)s" if page is not None else ""

    order_string = f"ORDER BY {sort_by} {sort_order} " if sort_by is not None and sort_order is not None else ""

    return c.mogrify(
        f"{outer_selection} (SELECT {selection if not outer_query else 'id'} FROM variants "
        f"WHERE {chr_in}{loc_in}{mh_1l} NOT (%(clinvar)s AND gene_info_clinvar IS NULL) "
        f"AND (pam_mot > 0 OR NOT %(ngg_pam_avail)s) AND (pam_uniq > 0 OR NOT %(unique_guide_avail)s) "
        f"AND ({search_params['position_filter_fragment']}) AND ({search_params['search_query_fragment']}) "
        f"{order_string}{limit}{offset}) {order_string if outer_query else ''}",
        {
            "start": ((page if page is not None else 0) - 1) * (items_per_page if items_per_page is not None else 0),
            "items_per_page": items_per_page,
            "start_pos": search_params["start_pos"],
            "end_pos": search_params["end_pos"],
            "min_mh_1l": search_params["min_mh_1l"],
            "clinvar": search_params["clinvar"],
            "ngg_pam_avail": search_params["ngg_pam_avail"],
            "unique_guide_avail": search_params["unique_guide_avail"],
            **search_params["search_query_data"]
        }
    )


def build_variants_query_str(*args, **kwargs):
    return build_variants_query(*args, **kwargs).decode("utf-8")


def get_entries_with_cache(dataset: str, c, query):
    c.execute("SELECT * FROM entries_query_cache WHERE e_query = %s::bytea", (query,))
    cache_value = c.fetchone()

    if cache_value is not None:
        return cache_value[1]

    c.execute(query)
    num_entries = c.fetchone()[0]
    c.execute("INSERT INTO entries_query_cache VALUES(%s::bytea, %s) ON CONFLICT DO NOTHING ", (query, num_entries))
    get_db(dataset).commit()

    return num_entries


@app.get("/datasets/")
def datasets() -> Response:
    return json.jsonify(sorted([{"id": k, **v} for k, v in DATASETS.items()], key=lambda x: x["id"]))


@app.get("/datasets/<string:dataset>/")
def dataset_index(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute(build_variants_query(
        c,
        "variants.*, cartoon_text AS cartoon",
        get_search_params_from_request(c),
        cartoons=True,
        sort_by=verify_domain(request.args.get("sort_by", "id"), build_variants_columns_domain(c)),
        sort_order=verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN),
        page=int(verify_domain(request.args.get("page", "1"), POS_INT_DOMAIN)),
        items_per_page=int(verify_domain(request.args.get("items_per_page", "100"), POS_INT_DOMAIN))
    ))

    results = c.fetchall()
    for r in results:
        del r["full_row"]
    return json.jsonify(results)


@app.get("/datasets/<string:dataset>/tsv")
def variants_tsv(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    search_params = get_search_params_from_request(c)

    sort_by = verify_domain(request.args.get("sort_by", "id"), build_variants_columns_domain(c))
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    column_names = [i["column_name"] for i in get_variants_columns(c)]

    def generate():
        with app.app_context():
            c2 = get_db(dataset).cursor("variants-tsv-cursor")
            c2.execute(build_variants_query(c2, ",".join(column_names), search_params, sort_by=sort_by,
                                            sort_order=sort_order))

            yield "\t".join(column_names) + "\n"
            row = c2.fetchone()
            while row is not None:
                yield "\t".join([str(col) if col is not None else "NA" for col in row]) + "\n"
                row = c2.fetchone()

    return Response(generate(), mimetype="text/tab-separated-values",
                    headers={"Content-Disposition": "Content-Disposition: attachment; filename=\"variants.tsv\""})


@app.get("/datasets/<string:dataset>/variants/<int:variant_id>/guides")
def variant_guides(dataset: str, variant_id: int):
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM guides WHERE variant_id = %s", (variant_id,))
    return json.jsonify(c.fetchall())


@app.get("/datasets/<string:dataset>/variants/<int:variant_id>/guides/tsv")
def variant_guides_tsv(dataset: str, variant_id: int) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    column_names = [i["column_name"] for i in get_guides_columns(c)]

    def generate():
        with app.app_context():
            c2 = get_db(dataset).cursor("variant-guides-tsv-cursor")
            c2.execute("SELECT * FROM guides WHERE variant_id = %s", (variant_id,))

            yield "\t".join(column_names) + "\n"
            row = c2.fetchone()
            while row is not None:
                yield "\t".join([str(col) if col is not None else "NA" for col in row]) + "\n"
                row = c2.fetchone()

    return Response(generate(), mimetype="text/tab-separated-values",
                    headers={"Content-Disposition": f"Content-Disposition: attachment; "
                                                    f"filename=\"variant_{variant_id}_guides.tsv\""})


@app.get("/datasets/<string:dataset>/guides")
def guides(dataset: str) -> Response:
    page = int(verify_domain(request.args.get("page", "1"), POS_INT_DOMAIN))
    items_per_page = int(verify_domain(request.args.get("items_per_page", "100"), POS_INT_DOMAIN))

    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    search_params = get_search_params_from_request(c)

    sort_by = verify_domain(request.args.get("sort_by", "id"), build_variants_columns_domain(c))
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    # TODO: ALLOW SORTING GUIDES AS WELL?

    query_str = build_variants_query_str(
        c,
        "id",
        search_params,

        sort_by=sort_by,
        sort_order=sort_order,

        page=page,
        items_per_page=items_per_page,

        outer_query=False
    )

    c.execute(f"SELECT * FROM guides WHERE variant_id IN ({query_str}) ORDER BY id")
    return json.jsonify(c.fetchall())


@app.get("/datasets/<string:dataset>/guides/tsv")
def guides_tsv(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)
    search_params = get_search_params_from_request(c)
    variant_column_names = [i["column_name"] for i in get_variants_columns(c)]
    column_names = [i["column_name"] for i in get_guides_columns(c)]

    guides_with_variant_info = request.args.get("guides_with_variant_info", "true").lower() == "true"

    def generate():
        with app.app_context():
            c2 = get_db(dataset).cursor("guides-tsv-cursor")

            if guides_with_variant_info:
                c2.execute(f"SELECT {', '.join([f'variants.{col}' for col in variant_column_names[1:]])}, "
                           f"guides.* FROM variants RIGHT JOIN guides ON variants.id = guides.variant_id "
                           f"WHERE variant_id IN ({build_variants_query_str(c, 'id', search_params)})")
                yield "\t".join(variant_column_names[1:] + column_names) + "\n"

            else:
                c2.execute(f"SELECT * FROM guides WHERE variant_id IN "
                           f"({build_variants_query_str(c, 'id', search_params)})")
                yield "\t".join(column_names) + "\n"

            row = c2.fetchone()
            while row is not None:
                yield "\t".join([str(col) if col is not None else "NA" for col in row]) + "\n"
                row = c2.fetchone()

    return Response(generate(), mimetype="text/tab-separated-values",
                    headers={"Content-Disposition": "Content-Disposition: attachment; filename=\"guides.tsv\""})


@app.get("/datasets/<string:dataset>/combined/tsv")
def combined_tsv(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)

    search_params = get_search_params_from_request(c)

    guides_with_variant_info = request.args.get("guides_with_variant_info", "true").lower() == "true"

    sort_by = verify_domain(request.args.get("sort_by", "id"), build_variants_columns_domain(c))
    sort_order = verify_domain(request.args.get("sort_order", "ASC").upper(), SORT_ORDER_DOMAIN)

    variants_column_names = [i["column_name"] for i in get_variants_columns(c)]
    guides_column_names = [i["column_name"] for i in get_guides_columns(c)]

    def generate():
        with app.app_context():
            c2 = get_db(dataset).cursor("combined-tsv-cursor")
            c2.execute(build_variants_query(c, ",".join(variants_column_names), search_params, sort_by, sort_order))

            yield "\t".join(variants_column_names + [col if col != "id" else "guide_id"
                                                     for col in guides_column_names]) + "\n"
            c3 = get_db(dataset).cursor()
            row = c2.fetchone()
            while row is not None:
                row_to_return = [str(col) if col is not None else "NA" for col in row]

                c3.execute("SELECT * FROM guides WHERE variant_id = %s", (row_to_return[0],))
                guide_row = c3.fetchone()

                if guide_row is None or not guides_with_variant_info:
                    # No guides, or displaying guides with variant info is disabled
                    yield "\t".join(row_to_return) + "\n"

                while guide_row is not None:
                    guide_info = [str(col) if col is not None else "NA" for col in guide_row]
                    if guides_with_variant_info:
                        yield "\t".join(row_to_return + guide_info) + "\n"
                    else:
                        yield "\t".join(([""] * len(variants_column_names)) + guide_info) + "\n"
                    guide_row = c3.fetchone()

                row = c2.fetchone()

    return Response(generate(), mimetype="text/tab-separated-values",
                    headers={"Content-Disposition": "Content-Disposition: attachment; "
                                                    "filename=\"variants_with_guides.tsv\""})


@app.get("/datasets/<string:dataset>/variants/entries")
def variants_entries(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)
    entries_query = build_variants_query(c, "COUNT(*)", get_search_params_from_request(c), outer_query=False)
    return json.jsonify(get_entries_with_cache(dataset, c, entries_query))


@app.get("/datasets/<string:dataset>/guides/entries")
def guides_entries(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)
    entries_query = c.mogrify(
        f"SELECT COUNT(*) FROM guides WHERE variant_id IN "
        f"({build_variants_query_str(c, 'id', get_search_params_from_request(c), outer_query=False)})"
    )
    return json.jsonify(get_entries_with_cache(dataset, c, entries_query))


@app.get("/datasets/<string:dataset>/variants/fields")
def variant_fields(dataset: str) -> Response:
    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)
    return json.jsonify({col["column_name"]: col for col in get_variants_columns(c)})


@app.get("/datasets/<string:dataset>/metadata")
def metadata(dataset: str) -> Response:
    """
    Returns various metadata and summary statistics about the entries in the database. Does not respect filtering
    parameters.
    :return: A JSON response with metadata and summary statistics.
    """

    c = get_db(dataset).cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT (SELECT CAST(s_value AS INTEGER) FROM summary_statistics WHERE s_key = 'min_pos') AS min_pos, "
              "  (SELECT CAST(s_value AS INTEGER) FROM summary_statistics WHERE s_key = 'max_pos') AS max_pos, "
              "  MAX(mh_l) AS max_mh_l, MAX(mh_1l) AS max_mh_1l FROM variants")
    return json.jsonify({
        **dict(c.fetchone()),
        "chr": CHR_VALUES,
        "location": LOCATION_VALUES,
        "version": __version__
    })


@app.get("/token")
def email_token() -> Response:
    token = secrets.token_hex(24)
    expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    email_tokens[token] = expiry
    return json.jsonify({"token": token, "expiry": int(expiry.timestamp())})


@app.post("/report")
def bug_report() -> Response:
    data = request.get_json()
    if "token" not in data:
        return Response(status=400, content_type="application/json",
                        response=json.jsonify({"success": False, "reason": "token passed incorrectly"}))

    now = datetime.datetime.now()
    for token in email_tokens:
        if email_tokens[token] < now:
            del email_tokens[token]

    token = data["token"]
    if token not in email_tokens.keys():
        return Response(status=400, content_type="application/json",
                        response=json.jsonify({"success": False, "reason": "invalid token"}))

    c = get_db(BUG_REPORT_DATASET).cursor()
    c.execute("INSERT INTO bug_reports(email, report) VALUES(%s, %s) RETURNING id", (data["email"], data["text"]))
    bug_report_id = c.fetchone()[0]

    message = EmailMessage()

    # Email headers
    message["From"] = "no-reply@mhcut-browser.genap.ca"
    message["To"] = os.environ.get("BUG_REPORT_EMAIL").strip()
    message["Subject"] = f"MHcut Bug Report (ID: {bug_report_id})"
    message["Reply-To"] = data["email"]

    # Email content
    message.set_content(
        f"{data['email']} submitted the following bug report:\n"
        f"--------------------------------------------------------------------------------\n\n"
        f"{data['text']}"
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(os.environ.get("GMAIL_SENDER_EMAIL"), os.environ.get("GMAIL_SENDER_PASSWORD"))
            smtp.send_message(message)
            return json.jsonify({"success": True})
    except ConnectionRefusedError:
        return json.jsonify({"success": False, "reason": "could not connect to mail server"})
    except smtplib.SMTPResponseException as e:
        print(e)
        return json.jsonify({"success": False, "reason": "smtp error"})
    finally:
        del email_tokens[token]


@app.teardown_appcontext
def close_connection(_exception):
    dbs = getattr(g, "databases", dict())
    for ds in dbs:
        dbs[ds].close()


if __name__ == "__main__":
    app.run()

#!/usr/bin/env python3

import csv
import getpass
import os
import psycopg2
import sys

from io import StringIO
from tqdm import tqdm


def int_or_null_cast(x):
    """
    Casts a provided value to an integer string, and returns backslash-N if the cast fails.
    :param x: The value to attempt to cast to an integer.
    :return: The cast value, or None if the cast fails.
    """
    try:
        return str(int(x))
    except ValueError:
        return "\\N"


def int_or_none_cast(x):
    """
    Casts a provided value to an integer, and returns None if the cast fails.
    :param x: The value to attempt to cast to an integer.
    :return: The cast value, or None if the cast fails.
    """
    try:
        return int(x)
    except ValueError:
        return None


def main():
    """
    Main method, runs when the script is ran directly.
    """

    if len(sys.argv) != 5:
        print("Usage: ./tsv_to_postgres.py variants_file.tsv guides_file.tsv database_name database_user")
        exit(1)

    db_password = os.environ.get("DB_PASSWORD")
    if db_password is None:
        db_password = getpass.getpass(prompt="Password for Database User: ")

    conn = psycopg2.connect("dbname={} user={} password={}".format(sys.argv[3], sys.argv[4], db_password))
    c = conn.cursor()

    with open("./sql/schema.sql", "r") as s:
        c.execute(s.read())

    # Get number of lines for progress bars.
    n_variants = 0
    n_guides = 0
    with open(sys.argv[1], "r") as vs_file, open(sys.argv[2], "r") as gs_file:
        # Skip headers:
        next(vs_file)
        next(gs_file)

        for _ in vs_file:
            n_variants += 1

        for _ in gs_file:
            n_guides += 1

    variant_copy = StringIO()

    with open(sys.argv[1], "r", newline="") as vs_file:
        reader = csv.DictReader(vs_file, delimiter="\t")
        i = 1
        for variant in tqdm(reader, total=n_variants, desc="variants"):
            rs = variant["RS"].strip()
            if rs == "-":
                # Treat - as null (NA does not occur)
                rs = "\\N"

            af_exac = variant["AF_EXAC"].strip()
            if af_exac == "NA":
                # Treat NA as null
                af_exac = "\\N"

            gene_info_clinvar = variant["GENEINFO.ClinVar"].strip()
            if gene_info_clinvar == "NA":
                # Treat NA, but not -, as null
                gene_info_clinvar = "\\N"

            main_rows = (str(i), variant["chr"], variant["start"], variant["end"], rs, variant["CAF"],
                         variant["TOPMED"], variant["GENEINFO"], variant["PM"], variant["MC"], af_exac,
                         variant["AF_TGP"], int_or_null_cast(variant["ALLELEID"]), variant["CLNDN"], variant["CLNSIG"],
                         variant["DBVARID"], gene_info_clinvar, variant["MC.ClinVar"], variant["citation"],
                         variant["geneloc"], variant["varL"], variant["mhL"], variant["mh1L"], variant["hom"],
                         variant["nbMM"], int_or_null_cast(variant["mhDist"]), variant["MHseq1"], variant["MHseq2"],
                         int_or_null_cast(variant["pamMot"]), int_or_null_cast(variant["pamUniq"]),
                         int_or_null_cast(variant["guidesNoOT"]), int_or_null_cast(variant["guidesMinOT"]))

            variant_copy.write("\t".join((*main_rows, " ".join(main_rows).lower())) + "\n")

            if i % 500000 == 0:
                variant_copy.seek(0)
                c.copy_from(variant_copy, "variants")
                variant_copy = StringIO()
                conn.commit()

            i += 1

    # Copy stragglers
    variant_copy.seek(0)
    c.copy_from(variant_copy, "variants")

    conn.commit()

    print("Creating indices...")
    c.execute(open("./sql/variants_indices.sql", "r").read())
    print("\tDone.")

    conn.commit()

    c.execute("INSERT INTO summary_statistics VALUES(%s, (SELECT MIN(pos_start) FROM variants))", ("min_pos",))
    c.execute("INSERT INTO summary_statistics VALUES(%s, (SELECT MAX(pos_end) FROM variants))", ("max_pos",))
    c.execute("INSERT INTO summary_statistics VALUES(%s, (SELECT MAX(mh_l) FROM variants))", ("max_mh_l",))

    conn.commit()

    with open(sys.argv[2], "r", newline="") as gs_file:
        reader = csv.DictReader(gs_file, delimiter="\t")
        guide_copy = StringIO()
        j = 1
        for guide in tqdm(reader, total=n_guides, desc="guides"):
            c.execute("SELECT id FROM variants WHERE chr = %s AND pos_start = %s AND pos_end = %s "
                      "AND rs {}".format("IS NULL -- %s" if guide["RS"] == "-" else "= %s"),
                      (guide["chr"], int(guide["start"]), int(guide["end"]), guide["RS"]))

            variant = c.fetchone()
            if variant is None:
                tqdm.write("Could not find associated variant for guide:")
                tqdm.write(str(guide))

            variant_id = variant[0]

            guide_copy.write("\t".join((str(j), str(variant_id), guide["protospacer"], int_or_null_cast(guide["mm0"]),
                                        int_or_null_cast(guide["mm1"]), int_or_null_cast(guide["mm2"]),
                                        guide["m1Dist1"], guide["m1Dist2"], guide["mhDist1"],
                                        guide["mhDist2"], int_or_null_cast(guide["nbOffTgt"]),
                                        int_or_null_cast(guide["largestOffTgt"]), guide["botScore"],
                                        int_or_null_cast(guide["botSize"]), int_or_null_cast(guide["botVarL"]),
                                        int_or_null_cast(guide["botGC"]), guide["botSeq"])) + "\n")

            j += 1

            if j % 50000 == 0:
                guide_copy.seek(0)
                c.copy_from(guide_copy, "guides")
                guide_copy = StringIO()
                conn.commit()

    guide_copy.seek(0)
    c.copy_from(guide_copy, "guides")

    conn.commit()

    c.execute("CREATE INDEX guides_variant_id_idx ON guides(variant_id)")
    c.execute("CLUSTER guides USING guides_variant_id_idx")

    conn.commit()

    c.close()
    conn.close()


if __name__ == "__main__":
    main()

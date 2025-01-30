#!/usr/bin/env python3


# MHcut browser is a web application for browsing data from the MHcut tool.
# Copyright (C) 2018-2025  the Canadian Centre for Computational Genomics
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


import getpass
import os
import psycopg2

from io import StringIO
from tqdm import tqdm
from typing import Tuple

import sys

CHROMOSOMES = ("chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8", "chr9", "chr10",
               "chr11", "chr12", "chr13", "chr14", "chr15", "chr16", "chr17", "chr18", "chr19",
               "chr20", "chr21", "chr22", "chrX", "chrY")


def int_or_null(x):
    """
    Checks if a provided value is an integer string, and returns backslash-N if the cast fails.
    :param x: The value to test.
    :return: The cast value, or None if the cast fails.
    """

    return x if x.isdigit() or (x.startswith("-") and x[1:].isdigit()) else "\\N"


def pos_int_or_null(x):
    return x if x.isdigit() else "\\N"


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


def str_or_null(x: str):
    return x.strip() if x != "NA" else "\\N"


def schema_setup(conn):
    c = conn.cursor()

    with open("./sql/schema.sql", "r") as s:
        c.execute(s.read())

    conn.commit()


def get_n_variants_guides(variants_path: str, guides_path: str) -> Tuple[int, int]:
    with open(variants_path, "r") as vs_file, open(guides_path, "r") as gs_file:
        # Skip headers:
        next(vs_file)
        next(gs_file)

        n_variants = sum(1 for _ in vs_file)
        n_guides = sum(1 for _ in gs_file)

    return n_variants, n_guides


def ingest_variants(conn, variants_path: str, n_variants: int, id_cache: dict):
    c = conn.cursor()
    variant_copy = StringIO()

    with open(variants_path, "r", newline="") as vs_file:
        # reader = csv.DictReader(vs_file, delimiter="\t")
        i = 1

        headers = next(vs_file)[:-1].split("\t")
        h_chr = headers.index("chr")
        h_start = headers.index("start")
        h_end = headers.index("end")
        h_geneloc = headers.index("geneloc")
        h_rs = headers.index("RS")
        h_geneinfo = headers.index("GENEINFO")
        h_clndn = headers.index("CLNDN")
        h_clnsig = headers.index("CLNSIG")
        h_var_l = headers.index("varL")
        h_flank = headers.index("flank")
        h_mh_score = headers.index("mhScore")
        h_mh_l = headers.index("mhL")
        h_mh1_l = headers.index("mh1L")
        h_hom = headers.index("hom")
        h_mh_max_cons = headers.index("mhMaxCons")
        h_mh_dist = headers.index("mhDist")
        h_mh1_dist = headers.index("mh1Dist")
        h_mh_seq_1 = headers.index("MHseq1")
        h_mh_seq_2 = headers.index("MHseq2")
        h_pam_mot = headers.index("pamMot")
        h_pam_uniq = headers.index("pamUniq")
        h_guides_no_nmh = headers.index("guidesNoNMH")

        h_guides_min_nmh = headers.index("guidesMinNMH")
        h_caf = headers.index("CAF")
        h_topmed = headers.index("TOPMED")
        h_pm = headers.index("PM")
        h_mc = headers.index("MC")
        h_af_exac = headers.index("AF_EXAC")
        h_af_tgp = headers.index("AF_TGP")
        h_alleleid = headers.index("ALLELEID")
        h_dbvarid = headers.index("DBVARID")
        h_geneinfo_clinvar = headers.index("GENEINFO.ClinVar")
        h_mc_clinvar = headers.index("MC.ClinVar")
        h_citation = headers.index("citation")
        h_nb_mm = headers.index("nbMM")
        h_gc = headers.index("GC")
        h_max2cuts_dist = headers.index("max2cutsDist")

        h_max_in_delphi_freq_mean = headers.index("maxInDelphiFreqMean")
        h_max_in_delphi_freq_mesc = headers.index("maxInDelphiFreqmESC")
        h_max_in_delphi_freq_u2os = headers.index("maxInDelphiFreqU2OS")
        h_max_in_delphi_freq_hek293 = headers.index("maxInDelphiFreqHEK293")
        h_max_in_delphi_freq_hct116 = headers.index("maxInDelphiFreqHCT116")
        h_max_in_delphi_freq_k562 = headers.index("maxInDelphiFreqK562")

        for variant in tqdm(vs_file, total=n_variants, desc="variants"):
            variant = variant[:-1].split("\t")

            id_cache[CHROMOSOMES.index(variant[h_chr]), int(variant[h_start]), int(variant[h_end]),
                     int_or_none_cast(variant[h_rs])] = i

            main_rows = (str(i), variant[h_chr], variant[h_start], variant[h_end], variant[h_geneloc].lower(),
                         int_or_null(variant[h_rs].strip()),
                         variant[h_geneinfo], variant[h_clndn], variant[h_clnsig], variant[h_var_l], variant[h_flank],
                         variant[h_mh_score], variant[h_mh_l], variant[h_mh1_l], variant[h_hom],
                         int_or_null(variant[h_mh_max_cons]), int_or_null(variant[h_mh_dist]),
                         int_or_null(variant[h_mh1_dist]), variant[h_mh_seq_1], variant[h_mh_seq_2],
                         pos_int_or_null(variant[h_pam_mot]), pos_int_or_null(variant[h_pam_uniq]),
                         pos_int_or_null(variant[h_guides_no_nmh]),
                         # cartoon goes here...

                         pos_int_or_null(variant[h_guides_min_nmh]),
                         variant[h_caf], variant[h_topmed], variant[h_pm], variant[h_mc],
                         str_or_null(variant[h_af_exac]), variant[h_af_tgp],
                         pos_int_or_null(variant[h_alleleid]), variant[h_dbvarid],
                         str_or_null(variant[h_geneinfo_clinvar]),
                         variant[h_mc_clinvar], variant[h_citation], variant[h_nb_mm],
                         str_or_null(variant[h_gc]), int_or_null(variant[h_max2cuts_dist]),

                         str_or_null(variant[h_max_in_delphi_freq_mean]),
                         str_or_null(variant[h_max_in_delphi_freq_mesc]),
                         str_or_null(variant[h_max_in_delphi_freq_u2os]),
                         str_or_null(variant[h_max_in_delphi_freq_hek293]),
                         str_or_null(variant[h_max_in_delphi_freq_hct116]),
                         str_or_null(variant[h_max_in_delphi_freq_k562]))

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
    c.close()


def ingest_guides(conn, guides_path: str, n_guides: int, id_cache: dict):
    c = conn.cursor()
    guide_copy = StringIO()

    with open(guides_path, "r", newline="") as gs_file:
        # reader = csv.DictReader(gs_file, delimiter="\t")

        headers = next(gs_file)[:-1].split("\t")

        h_chr = headers.index("chr")
        h_start = headers.index("start")
        h_end = headers.index("end")
        h_rs = headers.index("RS")
        h_nmh_gc = headers.index("nmhGC")
        h_protospacer = headers.index("protospacer")
        h_mm0 = headers.index("mm0")
        h_m1_dist1 = headers.index("m1Dist1")
        h_m1_dist2 = headers.index("m1Dist2")
        h_mh_dist1 = headers.index("mhDist1")
        h_mh_dist2 = headers.index("mhDist2")
        h_nb_nmh = headers.index("nbNMH")
        h_largest_nmh = headers.index("largestNMH")
        h_nmh_score = headers.index("nmhScore")
        h_nmh_size = headers.index("nmhSize")
        h_nmh_var_l = headers.index("nmhVarL")
        h_nmh_seq = headers.index("nmhSeq")
        h_in_delphi_freq_mean = headers.index("inDelphiFreqMean")
        h_in_delphi_freq_mesc = headers.index("inDelphiFreqmESC")
        h_in_delphi_freq_u2os = headers.index("inDelphiFreqU2OS")
        h_in_delphi_freq_hek293 = headers.index("inDelphiFreqHEK293")
        h_in_delphi_freq_hct116 = headers.index("inDelphiFreqHCT116")
        h_in_delphi_freq_k562 = headers.index("inDelphiFreqK562")

        j = 1
        for guide in tqdm(gs_file, total=n_guides, desc="guides"):
            guide = guide[:-1].split("\t")

            variant_id = id_cache[CHROMOSOMES.index(guide[h_chr]), int(guide[h_start]), int(guide[h_end]),
                                  int_or_none_cast(guide[h_rs])]

            nmh_gc = guide[h_nmh_gc].strip()
            if nmh_gc == "NA":
                # Treat NA as null
                nmh_gc = "\\N"

            guide_copy.write("\t".join((str(j), str(variant_id), guide[h_protospacer], int_or_null(guide[h_mm0]),
                                        guide[h_m1_dist1], guide[h_m1_dist2], guide[h_mh_dist1],
                                        guide[h_mh_dist2], int_or_null(guide[h_nb_nmh]),
                                        int_or_null(guide[h_largest_nmh]), guide[h_nmh_score],
                                        int_or_null(guide[h_nmh_size]), int_or_null(guide[h_nmh_var_l]),
                                        nmh_gc, guide[h_nmh_seq], str_or_null(guide[h_in_delphi_freq_mean]),
                                        str_or_null(guide[h_in_delphi_freq_mesc]),
                                        str_or_null(guide[h_in_delphi_freq_u2os]),
                                        str_or_null(guide[h_in_delphi_freq_hek293]),
                                        str_or_null(guide[h_in_delphi_freq_hct116]),
                                        str_or_null(guide[h_in_delphi_freq_k562]))) + "\n")

            j += 1

            if j % 250000 == 0:
                guide_copy.seek(0)
                c.copy_from(guide_copy, "guides")
                guide_copy = StringIO()
                conn.commit()

    guide_copy.seek(0)
    c.copy_from(guide_copy, "guides")

    conn.commit()

    print("Creating guide index...")

    c.execute("CREATE INDEX guides_variant_id_idx ON guides(variant_id)")
    c.execute("CLUSTER guides USING guides_variant_id_idx")

    conn.commit()
    c.close()


def ingest_cartoons(conn, cartoons_path: str):
    c = conn.cursor()

    print("Saving cartoons...")  # TODO: TQDM with real progress

    with open(cartoons_path, "r", newline="") as cs_file:
        # Skip variant header row
        next(cs_file)
        next(cs_file)

        line = next(cs_file)
        line_no = 3

        current_stage = 0
        current_variant = []
        current_cartoon = ""

        k = 1
        with tqdm(desc="cartoons") as pr:
            while True:
                try:
                    if line == "\n":
                        if len(current_variant) > 0:
                            if k < 14903120:
                                current_stage = 0
                                current_variant = []
                                current_cartoon = ""

                                pr.update(1)
                                k += 1

                                continue

                            next_cartoon = {
                                "cartoon": current_cartoon,
                                "chr": current_variant[0],
                                "pos_start": int(current_variant[1]),
                                "pos_end": int(current_variant[2]),
                                "rs": current_variant[3]
                            }

                            try:
                                c.execute(
                                    "SELECT id FROM variants WHERE chr = %(chr)s "
                                    "AND pos_start = %(pos_start)s AND pos_end = %(pos_end)s "
                                    "AND rs {}".format(
                                        "IS NULL" if next_cartoon["rs"] == "-" else "= CAST(%(rs)s AS INT)"),
                                    next_cartoon
                                )

                                var = c.fetchone()

                                if var is None:
                                    tqdm.write(str(next_cartoon))
                                    tqdm.write("COULD NOT SAVE THE ABOVE CARTOON (LINE {}).".format(line_no))

                                else:
                                    v_id = var[0]

                                    c.execute("INSERT INTO cartoons VALUES(%s, %s) ON CONFLICT DO NOTHING",
                                              (v_id, next_cartoon["cartoon"]))

                            except psycopg2.DataError as e:
                                conn.commit()
                                tqdm.write(str(e))
                                tqdm.write(str(line_no))

                            # try:
                            #     v_id = id_cache[CHROMOSOMES.index(next_cartoon["chr"]), next_cartoon["pos_start"],
                            #                     next_cartoon["pos_end"], int_or_none_cast(next_cartoon["rs"])]
                            #
                            #     c.execute("INSERT INTO cartoons VALUES(%s, %s) ON CONFLICT DO NOTHING",
                            #               (v_id, next_cartoon["cartoon"]))
                            #
                            #     conn.commit()
                            #
                            # except KeyError:
                            #     tqdm.write(str(next_cartoon))
                            #     tqdm.write("COULD NOT SAVE THE ABOVE CARTOON.")

                            current_stage = 0
                            current_variant = []
                            current_cartoon = ""

                            pr.update(1)
                            k += 1

                            if k % 50000 == 0:
                                conn.commit()

                        while line == "\n":
                            line = next(cs_file)
                            line_no += 1

                        continue

                    if current_stage == 0:
                        current_variant = line.split("\t")
                        current_stage = 1
                        line = next(cs_file)
                        line_no += 1
                        continue

                    elif current_stage == 1:
                        current_cartoon = line + next(cs_file) + next(cs_file).strip()
                        current_stage = 2
                        line = next(cs_file)
                        line_no += 3
                        continue

                    elif current_stage == 2:
                        # Optional stage where other non-blank lines are skipped.
                        while line != "\n":
                            line = next(cs_file)
                            line_no += 1

                except StopIteration:
                    break

    # Clear the TQDM bar
    print()

    conn.commit()
    c.close()


def main():
    """
    Main method, runs when the script is run directly.
    """

    if len(sys.argv) != 6:
        print("Usage: ./tsv_to_postgres.py variants_file.tsv guides_file.tsv cartoons_file.tsv database_name "
              "database_user")
        exit(1)

    variants_path = sys.argv[1]
    guides_path = sys.argv[2]
    cartoons_path = sys.argv[3]

    db_password = os.environ.get("DB_PASSWORD")
    if db_password is None:
        db_password = getpass.getpass(prompt="Password for Database User: ")

    conn = psycopg2.connect("dbname={} user={} password={}".format(sys.argv[4], sys.argv[5], db_password))

    # Set up database structure
    schema_setup(conn)

    # Get number of lines for progress bars.
    n_variants, n_guides = get_n_variants_guides(variants_path, guides_path)

    id_cache = {}  # Cache for IDs to avoid repeated query lookups

    # Ingest variants
    ingest_variants(conn, variants_path, n_variants, id_cache)

    # Ingest guides
    ingest_guides(conn, guides_path, n_guides, id_cache)

    # Ingest cartoons
    ingest_cartoons(conn, cartoons_path)

    conn.close()


if __name__ == "__main__":
    main()

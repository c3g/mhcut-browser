#!/usr/bin/env python3


# MHcut browser is a web application for browsing data from the MHcut tool.
# Copyright (C) 2018-2019  David Lougheed
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


import csv
import getpass
import os
import psycopg2
import time

from io import StringIO
from multiprocessing import Process, Queue, Value
from queue import Empty
from tqdm import tqdm

import sys

NUM_PROCESSES = len(os.sched_getaffinity(0))


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


def main():
    """
    Main method, runs when the script is ran directly.
    """

    if len(sys.argv) != 6:
        print("Usage: ./tsv_to_postgres.py variants_file.tsv guides_file.tsv cartoons_file.tsv database_name "
              "database_user")
        exit(1)

    db_password = os.environ.get("DB_PASSWORD")
    if db_password is None:
        db_password = getpass.getpass(prompt="Password for Database User: ")

    conn = psycopg2.connect("dbname={} user={} password={}".format(sys.argv[4], sys.argv[5], db_password))
    c = conn.cursor()

    with open("./sql/schema.sql", "r") as s:
        c.execute(s.read())

    conn.commit()

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
            rs = int_or_null(variant["RS"].strip())
            af_exac = str_or_null(variant["AF_EXAC"])

            # Treat NA, but not -, as null
            gene_info_clinvar = str_or_null(variant["GENEINFO.ClinVar"])

            main_rows = (str(i), variant["chr"], variant["start"], variant["end"], variant["geneloc"].lower(), rs,
                         variant["GENEINFO"], variant["CLNDN"], variant["CLNSIG"], variant["varL"], variant["flank"],
                         variant["mhScore"], variant["mhL"], variant["mh1L"], variant["hom"],
                         int_or_null(variant["mhMaxCons"]), int_or_null(variant["mhDist"]),
                         int_or_null(variant["mh1Dist"]), variant["MHseq1"], variant["MHseq2"],
                         pos_int_or_null(variant["pamMot"]), pos_int_or_null(variant["pamUniq"]),
                         pos_int_or_null(variant["guidesNoNMH"]),
                         # cartoon goes here...

                         pos_int_or_null(variant["guidesMinNMH"]),
                         variant["CAF"], variant["TOPMED"], variant["PM"], variant["MC"], af_exac, variant["AF_TGP"],
                         pos_int_or_null(variant["ALLELEID"]), variant["DBVARID"], gene_info_clinvar,
                         variant["MC.ClinVar"], variant["citation"], variant["nbMM"],
                         str_or_null(variant["GC"]), int_or_null(variant["max2cutsDist"]),

                         str_or_null(variant["maxInDelphiFreqMean"]), str_or_null(variant["maxInDelphiFreqmESC"]),
                         str_or_null(variant["maxInDelphiFreqU2OS"]), str_or_null(variant["maxInDelphiFreqHEK293"]),
                         str_or_null(variant["maxInDelphiFreqHCT116"]), str_or_null(variant["maxInDelphiFreqK562"]))

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

            nmh_gc = guide["nmhGC"].strip()
            if nmh_gc == "NA":
                # Treat NA as null
                nmh_gc = "\\N"

            guide_copy.write("\t".join((str(j), str(variant_id), guide["protospacer"], int_or_null(guide["mm0"]),
                                        # int_or_null_cast(guide["mm1"]), int_or_null_cast(guide["mm2"]),
                                        guide["m1Dist1"], guide["m1Dist2"], guide["mhDist1"],
                                        guide["mhDist2"], int_or_null(guide["nbNMH"]),
                                        int_or_null(guide["largestNMH"]), guide["nmhScore"],
                                        int_or_null(guide["nmhSize"]), int_or_null(guide["nmhVarL"]),
                                        nmh_gc, guide["nmhSeq"], str_or_null(guide["inDelphiFreqMean"]),
                                        str_or_null(guide["inDelphiFreqmESC"]),
                                        str_or_null(guide["inDelphiFreqU2OS"]),
                                        str_or_null(guide["inDelphiFreqHEK293"]),
                                        str_or_null(guide["inDelphiFreqHCT116"]),
                                        str_or_null(guide["inDelphiFreqK562"]))) + "\n")

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

    def cartoon_saver(q, dc, s2):
        conn2 = psycopg2.connect("dbname={} user={} password={}".format(sys.argv[4], sys.argv[5], db_password))
        c2 = conn2.cursor()

        with tqdm(desc="{}".format(s2), position=s2) as pr:
            while not (q.empty() and dc.value == 1):
                try:
                    next_cartoon = q.get(False)

                    c2.execute("SELECT id FROM variants WHERE chr = %(chr)s "
                               "AND pos_start = %(pos_start)s AND pos_end = %(pos_end)s "
                               "AND rs {}".format("IS NULL" if next_cartoon["rs"] == "-" else "= CAST(%(rs)s AS INT)"),
                               next_cartoon)

                    var = c2.fetchone()

                    if var is None:
                        tqdm.write(str(next_cartoon))
                        tqdm.write("COULD NOT SAVE THE ABOVE CARTOON.")

                    else:
                        v_id = var[0]
                        c2.execute("INSERT INTO cartoons VALUES(%s, %s) ON CONFLICT DO NOTHING",
                                   (v_id, next_cartoon["cartoon"]))

                    pr.update(1)

                except Empty:
                    continue

        conn2.commit()
        conn2.close()

    print("Saving cartoons...")  # TODO: TQDM with real progress

    done_cartoons = Value("i", 0)
    cartoon_queue = Queue()

    processes = []
    for s in range(NUM_PROCESSES):
        processes.append(Process(target=cartoon_saver, args=(cartoon_queue, done_cartoons, s)))
        processes[-1].start()

    with open(sys.argv[3], "r", newline="") as cs_file:
        # Skip variant header row
        next(cs_file)
        next(cs_file)

        line = next(cs_file)
        current_stage = 0
        current_variant = []
        current_cartoon = ""

        k = 1
        while True:
            try:
                if line == "\n":
                    if len(current_variant) > 0:
                        cartoon_queue.put({
                            "cartoon": current_cartoon,
                            "chr": current_variant[0],
                            "pos_start": int(current_variant[1]),
                            "pos_end": int(current_variant[2]),
                            "rs": current_variant[3]
                        })

                        if cartoon_queue.qsize() > 1000000:
                            time.sleep(0.1)

                        current_stage = 0
                        current_variant = []
                        current_cartoon = ""

                        k += 1

                    while line == "\n":
                        line = next(cs_file)

                    continue

                if current_stage == 0:
                    current_variant = line.split("\t")
                    current_stage = 1
                    line = next(cs_file)
                    continue

                elif current_stage == 1:
                    current_cartoon = line + next(cs_file) + next(cs_file).strip()
                    current_stage = 2
                    line = next(cs_file)
                    continue

                elif current_stage == 2:
                    # Optional stage where other non-blank lines are skipped.
                    while line != "\n":
                        line = next(cs_file)

            except StopIteration:
                break

    cartoon_queue.close()
    cartoon_queue.join_thread()

    done_cartoons.value = 1

    for p in processes:
        p.join()

    for _ in range(NUM_PROCESSES):
        # Clear the TQDM bars
        print()

    conn.commit()

    c.close()
    conn.close()


if __name__ == "__main__":
    main()

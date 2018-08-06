#!/usr/bin/env python3

import csv
import sqlite3
import sys

from tqdm import tqdm


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

    if len(sys.argv) != 3:
        print("Usage: ./tsv_to_sqlite.py variants_file.tsv guides_file.tsv")
        exit(1)

    conn = sqlite3.connect("./db.sqlite")
    c = conn.cursor()

    with open("./schema.sql", "r") as s:
        c.executescript(s.read())

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

    with open(sys.argv[1], "r") as vs_file:
        reader = csv.DictReader(vs_file, delimiter="\t")
        i = 0
        for variant in tqdm(reader, total=n_variants, desc="variants"):  # TODO: Find total with wc -l
            gene_info_clinvar = variant["GENEINFO.ClinVar"].strip()
            if gene_info_clinvar == "NA":
                # Treat NA, but not -, as null
                gene_info_clinvar = None
            c.execute("INSERT INTO variants(chr, start, end, rs, caf, topmed, gene_info, pm, mc, af_exac, af_tgp, "
                      "                     allele_id, clndn, clnsig, dbvarid, gene_info_clinvar, mc_clinvar, "
                      "                     citation, geneloc, var_l, mh_l, mh_1l, hom, nbmm, mh_dist, mh_seq_1, "
                      "                     mh_seq_2, pam_mot, pam_uniq, guides_no_ot, guides_min_ot) "
                      "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                      "       ?, ?)",
                      (variant["chr"].strip(), int(variant["start"]), int(variant["end"]),
                       int_or_none_cast(variant["RS"]), variant["CAF"].strip(), variant["TOPMED"].strip(),
                       variant["GENEINFO"].strip(), variant["PM"].strip(), variant["MC"].strip(),
                       variant["AF_EXAC"].strip(), variant["AF_TGP"].strip(), variant["ALLELEID"].strip(),
                       variant["CLNDN"].strip(), variant["CLNSIG"].strip(), variant["DBVARID"].strip(),
                       gene_info_clinvar, variant["MC.ClinVar"].strip(), variant["citation"].strip(),
                       variant["geneloc"].strip(), int(variant["varL"]), int(variant["mhL"]), int(variant["mh1L"]),
                       variant["hom"].strip(), int(variant["nbMM"]), int_or_none_cast(variant["mhDist"]),
                       variant["MHseq1"].strip(), variant["MHseq2"].strip(), int_or_none_cast(variant["pamMot"]),
                       int_or_none_cast(variant["pamUniq"]), int_or_none_cast(variant["guidesNoOT"]),
                       int_or_none_cast(variant["guidesMinOT"])))
            i += 1

    conn.commit()

    with open(sys.argv[2], "r") as gs_file:
        reader = csv.DictReader(gs_file, delimiter="\t")
        for guide in tqdm(reader, total=n_guides, desc="guides"):
            c.execute("SELECT id FROM variants WHERE chr = :chr AND start = :start AND end = :end", {
                "chr": guide["chr"],
                "start": int(guide["start"]),
                "end": int(guide["end"])
            })
            variant_id = c.fetchone()[0]
            c.execute("INSERT INTO guides(variant, protospacer, mm0, mm1, mm2, m1_dist_1, m1_dist_2, mh_dist_1, "
                      "mh_dist_2, nb_off_tgt, largest_off_tgt, bot_score, bot_size, bot_var_l, bot_gc, bot_seq)"
                      "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (variant_id, guide["protospacer"].strip(), int_or_none_cast(guide["mm0"]),
                       int_or_none_cast(guide["mm1"]), int_or_none_cast(guide["mm2"]), int(guide["m1Dist1"]),
                       int(guide["m1Dist2"]), int(guide["mhDist1"]), int(guide["mhDist2"]), int(guide["nbOffTgt"]),
                       int(guide["largestOffTgt"]), guide["botScore"].strip(), int_or_none_cast(guide["botSize"]),
                       int_or_none_cast(guide["botVarL"]), int_or_none_cast(guide["botGC"]), guide["botSeq"].strip()))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()

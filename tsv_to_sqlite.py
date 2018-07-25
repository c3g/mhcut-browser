#!/usr/bin/env python3

import csv
import sqlite3

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

    conn = sqlite3.connect("./db.sqlite")
    c = conn.cursor()

    with open("./schema.sql", "r") as s:
        c.executescript(s.read())

    with open("./variants-subset.tsv", "r") as vs_file:
        reader = csv.DictReader(vs_file, delimiter="\t")
        i = 0
        for variant in tqdm(reader):  # TODO: Find total with wc -l
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
                       variant["GENEINFO.ClinVar"].strip(), variant["MC.ClinVar"].strip(), variant["citation"].strip(),
                       variant["geneloc"].strip(), int(variant["varL"]), int(variant["mhL"]), int(variant["mh1L"]),
                       variant["hom"].strip(), int(variant["nbMM"]), int_or_none_cast(variant["mhDist"]),
                       variant["MHseq1"].strip(), variant["MHseq2"].strip(), int_or_none_cast(variant["pamMot"]),
                       int_or_none_cast(variant["pamUniq"]), int_or_none_cast(variant["guidesNoOT"]),
                       int_or_none_cast(variant["guidesMinOT"])))
            i += 1

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()

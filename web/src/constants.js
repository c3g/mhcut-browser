export const CONDITION_OPERATORS = {
    both: ["equals", "<", "<=", ">", ">="],
    text: ["contains", "starts_with", "ends_with"],
    nullable: ["is_null"]
};

export const DEFAULT_CONDITION_BOOLEAN = "AND";

export const COLUMN_HELP_TEXT = {
    id: "Database ID.",
    chr: "Chromosome.",
    pos_start: "Starting position.",
    pos_end: "Ending position.",
    rs: "dbSNP ID.",
    caf: "Allele frequency from 1000GP, extracted from dbSNP.",
    topmed: "Allele frequency from TOPMED, extracted from dbSNP.",
    gene_info: "Genes overlapping the variants extracted from dbSNP.",
    pm: "Variant is precious (clinical, PubMed-cited). Extracted from dbSNP.",
    mc: "Molecular consequences, from dbSNP. Acronym Key: NSF=frameshift, NSN=nonsense, NSM=missense, " +
        "SYN=synonymous, INT=intronic, ASS/DSS=in acceptor/donor splice site, U3/U5=in UTR 3/5, " +
        "R3/R5=in upstream/downstream gene region.",
    af_exac: "Allele frequency from ExAC, extracted from ClinVar.",
    af_tgp: "Allele frequency from 1000GP, extracted from ClinVar.",
    allele_id: "ClinVar ID.",
    clndn: "ClinVar's preferred disease name for the concept specified by disease identifiers in CLNDISDB.",
    clnsig: "Clinical significance. E.g. \"Pathogenic\".",
    dbvarid: "Some variants in ClinVar are not in dbSNP but in dbVar. In that case this column contains the dbVar ID.",
    gene_info_clinvar: "Same as gene_info, but extracted from ClinVar.",
    mc_clinvar: "Molecular consequences, extracted from ClinVar.",

    citation: "The citation(s) associated with the variant (from PubMed, PubMedCentral, or the NCBI Bookshelf).", // TODO
    location: "The location of the variant relative to genes (Gencode v28).", // TODO
    var_l: "The variant size (bp).", // TODO

    mh_l: "MH length.",
    mh_1l: "Number of first consecutive matches.",
    hom: "Proportion of matches.",
    nbmm: "Number of mismatches.",
    mh_dist: "Distance between the end of MH and the variant boundary.",
    mh_seq_1: "Sequence 1 of the MH.",
    mh_seq_2: "Sequence 2 of the MH.",
    pam_mot: "The number of PAMs in a valid location.",
    pam_uniq: "The number of PAMs in a valid location and whose protospacer sequence is unique in the genome.",
    guides_no_ot: "The number of guides that have no off-target MH.",
    guides_min_ot: "The number of off-target MHs for the guide which has the least off-target MHs.",
    max_2_cuts_dist: "TODO", // TODO

    variant_id: "Corresponding variant database ID.",

    protospacer: "The sequence of the protospacer.",
    mm0: "The number of positions in the genome where the sequence aligns with no mismatches.",
    mm1: "The number of positions in the genome where the sequence aligns with 1 mismatch.",
    mm2: "The number of positions in the genome where the sequence aligns with 2 mismatches.",
    m1_dist_1: "Considering perfect homology only, the distance between the cut position and the upstream micro-homology.", // TODO: grammar???
    m1_dist_2: "Considering perfect homology only, the distance between the cut position and the downstream micro-homology.", // TODO: grammar???
    mh_dist_1: "The distance between the cut position and the upstream micro-homology.", // TODO: grammar???
    mh_dist_2: "The distance between the cut position and the downstream micro-homology.", // TODO: grammar???
    nb_off_tgt: "The number of off-target MHs.",
    largest_off_tgt: "The size of the largest off-target MH.",
    bot_score: "The MMEJ score of the best off-target MH (\"best\" defined as the highest MMEJ score).",
    bot_size: "The MH length of the best off-target MH (\"best\" defined as the highest MMEJ score).",
    bot_var_l: "The length of the variant created by the best off-target MH (\"best\" defined as the highest MMEJ score).",
    bot_gc: "The GC content of the best off-target MH (\"best\" defined as the highest MMEJ score).",
    bot_seq: "The sequence of the best off-target MH (\"best\" defined as the highest MMEJ score).",
};

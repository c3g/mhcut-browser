CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP TABLE IF EXISTS variants CASCADE;
DROP TABLE IF EXISTS guides CASCADE;
DROP TABLE IF EXISTS summary_statistics CASCADE;
DROP TABLE IF EXISTS entries_query_cache CASCADE;

DROP INDEX IF EXISTS variants_start_idx;
DROP INDEX IF EXISTS variants_end_idx;
DROP INDEX IF EXISTS variants_chr_start_end_rs_idx;
DROP INDEX IF EXISTS variants_mh_l_start_end_idx;
DROP INDEX IF EXISTS variants_rs_idx;
DROP INDEX IF EXISTS variants_caf_idx;
DROP INDEX IF EXISTS variants_topmed_idx;
DROP INDEX IF EXISTS variants_gene_info_idx;
DROP INDEX IF EXISTS variants_gene_info_trgm_idx;
DROP INDEX IF EXISTS variants_pm_idx;
DROP INDEX IF EXISTS variants_mc_idx;
DROP INDEX IF EXISTS variants_af_exac_idx;
DROP INDEX IF EXISTS variants_af_tgp_idx;
DROP INDEX IF EXISTS variants_allele_id_idx;
DROP INDEX IF EXISTS variants_clndn_idx;
DROP INDEX IF EXISTS variants_clnsig_idx;
DROP INDEX IF EXISTS variants_dbvarid_idx;
DROP INDEX IF EXISTS variants_gene_info_clinvar_idx;
DROP INDEX IF EXISTS variants_gene_info_clinvar_trgm_idx;
DROP INDEX IF EXISTS variants_mc_clinvar_idx;
DROP INDEX IF EXISTS variants_citation_idx;
DROP INDEX IF EXISTS variants_location_idx;
DROP INDEX IF EXISTS variants_var_l_idx;
DROP INDEX IF EXISTS variants_mh_l_idx;
DROP INDEX IF EXISTS variants_mh_1l_idx;
DROP INDEX IF EXISTS variants_hom_idx;
DROP INDEX IF EXISTS variants_nbmm_idx;
DROP INDEX IF EXISTS variants_mh_dist_idx;
DROP INDEX IF EXISTS variants_mh_seq_1_idx;
DROP INDEX IF EXISTS variants_mh_seq_2_idx;
DROP INDEX IF EXISTS variants_pam_mot_idx;
DROP INDEX IF EXISTS variants_pam_uniq_idx;
DROP INDEX IF EXISTS variants_guides_no_ot_idx;
DROP INDEX IF EXISTS variants_guides_min_ot_idx;
DROP INDEX IF EXISTS variants_full_row_trgm_idx;

DROP INDEX IF EXISTS guides_variant_id_idx;

DROP TYPE IF EXISTS CHROMOSOME;
DROP TYPE IF EXISTS VARIANT_LOCATION;

CREATE TYPE CHROMOSOME AS ENUM ('chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10',
                                'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19',
                                'chr20', 'chr21', 'chr22', 'chrX', 'chrY');

CREATE TYPE VARIANT_LOCATION AS ENUM ('intergenic', 'intronic', 'exonic');

CREATE TABLE variants (
  id INTEGER PRIMARY KEY,
  chr CHROMOSOME NOT NULL,
  pos_start INTEGER NOT NULL CHECK (pos_start >= 0),
  pos_end INTEGER NOT NULL CHECK (pos_end >= 0),
  rs TEXT, -- NULL means "-"
  caf TEXT, -- TODO: WHAT IS THIS?
  topmed TEXT, -- TODO: WHAT IS THIS?
  gene_info TEXT, -- TODO: WHAT IS THIS?
  pm TEXT, -- TODO: WHAT IS THIS? - NA VS. "-"
  mc TEXT, -- TODO: NA VS. "-"?
  af_exac TEXT, -- NULL means NA
  af_tgp TEXT,
  allele_id INTEGER CHECK (allele_id >= 0),
  clndn TEXT,
  clnsig TEXT,
  dbvarid TEXT,
  gene_info_clinvar TEXT, -- NA is represented as NULL, '-' is left as-is
  mc_clinvar TEXT,
  citation TEXT,
  location VARIANT_LOCATION NOT NULL,
  var_l INTEGER NOT NULL CHECK (var_l >= 0), -- Variant Size
  mh_l INTEGER NOT NULL CHECK (mh_l >= 0), -- Micro-Homology Length
  mh_1l INTEGER NOT NULL CHECK (mh_1l >= 0), -- Number of First Consecutive Matches
  hom TEXT, -- Decimal field with precision 1 or 2
  nbmm INTEGER NOT NULL CHECK (nbmm >= 0),
  mh_dist INTEGER,
  mh_seq_1 TEXT,
  mh_seq_2 TEXT,
  pam_mot INTEGER CHECK (pam_mot >= 0), -- NULL means NA
  pam_uniq INTEGER CHECK (pam_uniq >= 0), -- NULL means NA
  guides_no_ot INTEGER CHECK (guides_min_ot >= 0), -- NULL means NA
  guides_min_ot INTEGER CHECK (guides_min_ot >= 0), -- NULL means NA

  full_row TEXT NOT NULL
);

CREATE TABLE guides (
  id INTEGER PRIMARY KEY,
  variant_id INTEGER NOT NULL REFERENCES variants ON DELETE CASCADE,
  protospacer TEXT,
  mm0 INTEGER, -- NULL means NA
  mm1 INTEGER, -- NULL means NA
  mm2 INTEGER, -- NULL means NA
  m1_dist_1 INTEGER NOT NULL,
  m1_dist_2 INTEGER NOT NULL,
  mh_dist_1 INTEGER NOT NULL,
  mh_dist_2 INTEGER NOT NULL,
  nb_off_tgt INTEGER, -- NULL means NA
  largest_off_tgt INTEGER, -- NULL means NA
  bot_score TEXT NOT NULL,
  bot_size TEXT,
  bot_var_l INTEGER, -- NULL means NA
  bot_gc INTEGER, -- NULL means NA
  bot_seq TEXT -- NULL means NA
);

CREATE TABLE summary_statistics (
  s_key TEXT PRIMARY KEY,
  s_value NUMERIC NOT NULL
);

CREATE TABLE entries_query_cache (
  e_query BYTEA PRIMARY KEY,
  e_value INTEGER NOT NULL
);

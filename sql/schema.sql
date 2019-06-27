-- MHcut browser is a web application for browsing data from the MHcut tool.
-- Copyright (C) 2018-2019  David Lougheed
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.


DROP TABLE IF EXISTS variants CASCADE;
DROP TABLE IF EXISTS guides CASCADE;
DROP TABLE IF EXISTS cartoons CASCADE;
DROP TABLE IF EXISTS summary_statistics CASCADE;
DROP TABLE IF EXISTS entries_query_cache CASCADE;

DROP INDEX IF EXISTS variants_start_idx;
DROP INDEX IF EXISTS variants_end_idx;
DROP INDEX IF EXISTS variants_chr_start_end_rs_idx;
DROP INDEX IF EXISTS variants_mh_l_start_end_idx;
DROP INDEX IF EXISTS variants_mh_1l_start_end_idx;
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
DROP INDEX IF EXISTS variants_flank_idx;
DROP INDEX IF EXISTS variants_mh_score_idx;
DROP INDEX IF EXISTS variants_mh_max_cons_idx;
DROP INDEX IF EXISTS variants_mh_l_idx;
DROP INDEX IF EXISTS variants_mh_1l_idx;
DROP INDEX IF EXISTS variants_hom_idx;
DROP INDEX IF EXISTS variants_nbmm_idx;
DROP INDEX IF EXISTS variants_mh_dist_idx;
DROP INDEX IF EXISTS variants_mh_1dist_idx;
DROP INDEX IF EXISTS variants_mh_seq_1_idx;
DROP INDEX IF EXISTS variants_mh_seq_2_idx;
DROP INDEX IF EXISTS variants_gc_idx;
DROP INDEX IF EXISTS variants_pam_mot_idx;
DROP INDEX IF EXISTS variants_pam_uniq_idx;
DROP INDEX IF EXISTS variants_guides_no_nmh_idx;
DROP INDEX IF EXISTS variants_guides_min_nmh_idx;
DROP INDEX IF EXISTS variants_max_2_cuts_dist_idx;
DROP INDEX IF EXISTS variants_full_row_trgm_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_mean_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_mesc_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_u2os_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_hek293_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_hct116_idx;
DROP INDEX IF EXISTS variants_max_indelphi_freq_k562_idx;

-- TODO: REMOVE
DROP INDEX IF EXISTS variants_guides_no_ot_idx;
DROP INDEX IF EXISTS variants_guides_min_ot_idx;

DROP INDEX IF EXISTS guides_variant_id_idx;

DROP TYPE IF EXISTS CHROMOSOME;
DROP TYPE IF EXISTS VARIANT_LOCATION;

CREATE TYPE CHROMOSOME AS ENUM ('chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10',
                                'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19',
                                'chr20', 'chr21', 'chr22', 'chrX', 'chrY');

CREATE TYPE VARIANT_LOCATION AS ENUM ('intergenic', 'intronic', 'exonic', 'utr');

CREATE TABLE variants (
  id INTEGER PRIMARY KEY,
  chr CHROMOSOME NOT NULL,
  pos_start INTEGER NOT NULL CHECK (pos_start >= 0),
  pos_end INTEGER NOT NULL CHECK (pos_end >= 0),
  location VARIANT_LOCATION NOT NULL,
  rs INTEGER, -- NULL means "-"
  gene_info TEXT, -- TODO: WHAT IS THIS?
  clndn TEXT,
  clnsig TEXT,
  var_l INTEGER NOT NULL CHECK (var_l >= 0), -- Variant Size
  flank INTEGER NOT NULL CHECK (flank >= 0),
  mh_score INTEGER NOT NULL CHECK (mh_score >= 0),
  mh_l INTEGER NOT NULL CHECK (mh_l >= 0), -- Micro-Homology Length
  mh_1l INTEGER NOT NULL CHECK (mh_1l >= 0), -- Number of First Consecutive Matches
  hom TEXT, -- Decimal field with precision 1 or 2
  mh_max_cons INTEGER,
  mh_dist INTEGER,
  mh_1dist INTEGER,
  mh_seq_1 TEXT,
  mh_seq_2 TEXT,
  pam_mot INTEGER CHECK (pam_mot >= 0), -- NULL means NA
  pam_uniq INTEGER CHECK (pam_uniq >= 0), -- NULL means NA
  guides_no_nmh INTEGER CHECK (guides_no_nmh >= 0), -- NULL means NA

  guides_min_nmh INTEGER CHECK (guides_min_nmh >= 0), -- NULL means NA
  caf TEXT, -- TODO: WHAT IS THIS?
  topmed TEXT, -- TODO: WHAT IS THIS?
  pm TEXT, -- TODO: WHAT IS THIS? - NA VS. "-"
  mc TEXT, -- TODO: NA VS. "-"?
  af_exac TEXT, -- NULL means NA
  af_tgp TEXT,
  allele_id INTEGER CHECK (allele_id >= 0),
  dbvarid TEXT,
  gene_info_clinvar TEXT, -- NA is represented as NULL, '-' is left as-is
  mc_clinvar TEXT,
  citation TEXT,
  nbmm INTEGER NOT NULL CHECK (nbmm >= 0),
  gc NUMERIC CHECK (gc >= 0 AND gc <= 1),
  max_2_cuts_dist INTEGER, -- NULL means NA TODO: WHAT IS THIS?

  max_indelphi_freq_mesc NUMERIC CHECK (max_indelphi_freq_mesc >= 0), -- NULL means NA
  max_indelphi_freq_mean NUMERIC CHECK (max_indelphi_freq_mean >= 0), -- NULL means NA
  max_indelphi_freq_u2os NUMERIC CHECK (max_indelphi_freq_u2os >= 0), -- NULL means NA
  max_indelphi_freq_hek293 NUMERIC CHECK (max_indelphi_freq_hek293 >= 0), -- NULL means NA
  max_indelphi_freq_hct116 NUMERIC CHECK (max_indelphi_freq_hct116 >= 0), -- NULL means NA
  max_indelphi_freq_k562 NUMERIC CHECK (max_indelphi_freq_k562 >= 0), -- NULL means NA

  full_row TEXT NOT NULL
);

CREATE TABLE guides (
  id INTEGER PRIMARY KEY,
  variant_id INTEGER NOT NULL REFERENCES variants ON DELETE CASCADE,
  protospacer TEXT,
  mm0 INTEGER, -- NULL means NA
  -- mm1 INTEGER, -- NULL means NA
  -- mm2 INTEGER, -- NULL means NA
  m1_dist_1 INTEGER NOT NULL,
  m1_dist_2 INTEGER NOT NULL,
  mh_dist_1 INTEGER NOT NULL,
  mh_dist_2 INTEGER NOT NULL,
  nb_nmh INTEGER, -- NULL means NA
  largest_nmh INTEGER, -- NULL means NA
  nmh_score TEXT NOT NULL,
  nmh_size TEXT,
  nmh_var_l INTEGER, -- NULL means NA
  nmh_gc NUMERIC CHECK (nmh_gc >= 0 AND nmh_gc <= 1), -- NULL means NA
  nmh_seq TEXT, -- NULL means NA

  indelphi_freq_mesc NUMERIC CHECK (indelphi_freq_mesc >= 0), -- NULL means NA
  indelphi_freq_mean NUMERIC CHECK (indelphi_freq_mean >= 0), -- NULL means NA
  indelphi_freq_u2os NUMERIC CHECK (indelphi_freq_u2os >= 0), -- NULL means NA
  indelphi_freq_hek293 NUMERIC CHECK (indelphi_freq_hek293 >= 0), -- NULL means NA
  indelphi_freq_hct116 NUMERIC CHECK (indelphi_freq_hct116 >= 0), -- NULL means NA
  indelphi_freq_k562 NUMERIC CHECK (indelphi_freq_k562 >= 0) -- NULL means NA
);

CREATE TABLE cartoons (
  variant_id INTEGER PRIMARY KEY REFERENCES variants ON DELETE CASCADE,
  cartoon_text TEXT
);

CREATE TABLE summary_statistics (
  s_key TEXT PRIMARY KEY,
  s_value NUMERIC NOT NULL
);

CREATE TABLE entries_query_cache (
  e_query BYTEA PRIMARY KEY,
  e_value INTEGER NOT NULL
);

-- We don't drop and re-create bug_reports, because it should be preserved across imports.

CREATE TABLE IF NOT EXISTS bug_reports (
    id SERIAL,
    email TEXT,
    report TEXT
);

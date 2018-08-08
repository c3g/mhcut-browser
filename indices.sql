DROP INDEX IF EXISTS variants_chr_idx;
DROP INDEX IF EXISTS variants_start_idx;
DROP INDEX IF EXISTS variants_end_idx;

CREATE INDEX variants_chr_idx ON variants(chr);
CREATE INDEX variants_start_idx ON variants(start);
CREATE INDEX variants_end_idx ON variants(end);

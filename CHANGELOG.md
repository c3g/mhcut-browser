# Changelog

## Version 0.3.0 (UNRELEASED)

### Front End

  * Logo added to sidebar.
  * Sidebar width increased and layout changed for increased vertical space.
  * Fix status text showing 0 total pages if no results were found.
  * Remove "Position Filter Type" quick filter option (by request).
  * Add "Minimum mhL" and "Database Sources" quick filter options (by request).

### Server and API

  * `NA` now treated internally as `NULL` for the `gene_info_clinvar` database
    column.

### Miscellaneous

  * `tsv_to_sqlite.py` now accepts a mandatory argument for the TSV file
    instead of always using `variants-subset.tsv`.
  * uWSGI ini file and example systemd service files are now available.


## Version 0.2.0 (2018-07-31)

### Front End

  * Name changed to "CRISPR Cut Browser".
  * Citations now link to their respective pages on NCBI PubMed / Bookshelf.
  * Entries in the `gene_info_clinvar` now also link to NCBI Gene entries.


## Version 0.1.0 (2018-07-30)

Initial release.

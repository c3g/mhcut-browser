# Changelog

## Version 0.4.0 (UNRELEASED)

### Front End

  * Reset "Minimum mhL" and "Database Sources" properly when filters are
    cleared.
  * Allow keyboard submission of filtering and searching form.
  * Allow the user to escape the advanced search modal with the escape key.
  * Add instructions on using the advanced search feature.
  * Add an export modal window for exporting variant, guide, and combined
    search results as TSV files.
  * Fix some quick filters not resetting properly.
  * Add quick filters for "NGG PAM avail."/"Unique guide avail."
  * Add tab for viewing guides that relate to the currently-loaded set of
    variants.
  * Add modal table for viewing a specific variant's guides.
  * Add a non-sortable column for viewing variant cartoons.
  * Add tooltips for variant table columns.
  * Several changes to aid performance with the complete data-set.

### Server and API

  * Add endpoint for exporting TSV-formatted variant, guide, and combined
    search results.
  * Add filtering support for "NGG PAM avail."/"Unique guide avail."
  * Add endpoints for viewing guides.
  * Include cartoons in variants endpoint.
  * Several querying changes to aid performance with the complete data-set.
  
### Database

  * Moved to **PostgreSQL**.
  * Schema now includes tables for guides and key-value metadata.
  * `tsv_to_postgres.py` now takes in additional arguments for guides and
    cartoons files, as well as database name and user.
  * Several schema changes to aid performance with the complete data-set.


## Version 0.3.1 (2018-08-02)

### Server and API

  * Fix issue with loading version number in production.


## Version 0.3.0 (2018-08-02)

### Front End

  * Logo added to sidebar.
  * Sidebar width increased and layout changed for increased vertical space.
  * Fix status text showing 0 total pages if no results were found.
  * Remove "Position Filter Type" quick filter option (by request).
  * Add "Minimum mhL" and "Database Sources" quick filter options (by request).

### Server and API

  * `NA` now treated internally as `NULL` for the `gene_info_clinvar` database
    column.
  * Add application version to metadata endpoint.
  * Add `min_mh_l` (minimum mhL value), `dbsnp` (must an entry be in dbSNP?),
    and `clinvar` (must an entry be in ClinVar?) search parameters.

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

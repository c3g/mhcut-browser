# Changelog

## Version 1.1.0 (2025-01-30)

### Front End

  * Update dependencies
  * Drop compatibility for deployment with old NPM versions (<10)

### Server and API

  * Update dependencies and remove `simplejson` dependency
  * Refactor to use new Flask route methods
  * Drop compatibility for deployment with old Python versions (<3.9)

### Miscellaneous

  * Remove dead multiprocessing code from `tsv_to_postgres.py`



## Version 1.0.2 (2020-03-17)

### Front End

  * Update dependencies
  * Add correct DOI ([10.1038/s41467-019-12829-8](https://dx.doi.org/10.1038/s41467-019-12829-8))
  * Fix some `rel` attributes on links

### Server and API

  * Update dependencies



## Version 1.0.1 (2019-12-09)

### Front End

  * Update dependencies
  * Add license to `package.json`

### Miscellaneous

  * Add credits to `README.md`



## Version 1.0.0 (2019-09-24)

Final release version for publication. Incorporates changes from initial
submission as well (listed separately).

### Since Initial Submission:

#### Front End

  * Update dependencies
  * Document functions
  * Update tooltip text
  * Revise layout
  * Show cartoons in table instead of modal
  * Set default `min_mh_1l` to 3
  * Improve display by grouping columns
      * Allows expanding/collapsing and hidden columns
  * Add inDelphi scores, bar charts
  * Fix some small user interface issues
  * Fix ClinVar URLs linking to the wrong variants
  * Fix loading forever when no results are found
  * Add "no results" message
  * Improve loading performance
  * Add terms and conditions
  * Add bug reporting form

#### Server and API

  * Update dependencies
  * Fix GC content in variants endpoint
  * Add bug reporting support
  * Add inDelphi scores


#### Database

  * Add bug reporting support
  * Add inDelphi scores


#### Miscellaneous

  * Add LICENSE


### Prior to Initial Submission:

#### Front End

  * Update dependencies
  * Fix some small user interface issues
  * Remove dbSNP checkbox
  * Add "developed by CiRA / C3G"

#### Server and API

  * Update dependencies
  * Use `min_mh_1l` instead of `min_mh_l` for queries
  * Make some string search operations case insensitive


#### Database

  * Update schema to support new TSV format


#### Miscellaneous

  * Update documentation
  * Clean up some vestigial stuff



## Version 0.4.0 (2018-08-23)

Renamed once again, this time to "MHcut Browser".

### Front End

  * Allow keyboard submission of filtering and searching form.
  * Allow the user to escape modals with the escape key.
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
  * Fix column formatting for PMC citations.
  * Made several changes to aid performance with the complete data-set.

### Server and API

  * Add endpoint for exporting TSV-formatted variant, guide, and combined
    search results.
  * Add filtering support for "NGG PAM avail."/"Unique guide avail."
  * Add endpoints for viewing guides.
  * Include cartoons in variants endpoint.
  * Made several querying changes to aid performance with the complete
    data-set.

### Database

  * Moved to **PostgreSQL**.
  * Schema now includes tables for guides, cartoons, key-value metadata, and
    cached counts.
  * `tsv_to_postgres.py` now takes in additional arguments for guides and
    cartoons files, as well as database name and user; it now adds these values
    to the database and pre-computes some metadata.
  * Made several schema changes to aid performance with the complete data-set.



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
  * uWSGI ini file and example `systemd` service files are now available.



## Version 0.2.0 (2018-07-31)

### Front End

  * Name changed to "CRISPR Cut Browser".
  * Citations now link to their respective pages on NCBI PubMed / Bookshelf.
  * Entries in the `gene_info_clinvar` now also link to NCBI Gene entries.



## Version 0.1.0 (2018-07-30)

Initial release.

import * as d3 from "d3";

let dataDisplay = "variants";

let page = 1;
let itemsPerPage = 100;
let loadedVariants = [];
let loadedGuides = [];
let totalVariantsCount = 0;
let totalGuidesCount = 0;

let variantFields = [];
let guideFields = [];
let metadata = {};

let sortBy = "id";
let sortOrder = "ASC";

let selectedChromosomes = [];

let startPos = 0;
let endPos = 12000000000000;

let selectedGeneLocations = [];

let minMHL = 0;

let mustHaveDBSNP = false;
let mustHaveClinVar = false;

let currentFilterID = 0;
let advancedSearchFilters = [];

let transitioning = true;

let searchContainer = null;
let exportContainer = null;
let variantGuidesContainer = null;


const CONDITION_OPERATORS = {
    BOTH: ["equals", "<", "<=", ">", ">="],
    TEXT: ["contains", "starts_with", "ends_with"],
    NULLABLE: ["is_null"]
};

const DEFAULT_CONDITION_BOOLEAN = "AND";


document.addEventListener("DOMContentLoaded", function () {
    searchContainer = d3.select("#advanced-search-container");
    exportContainer = d3.select("#export-options-container");
    variantGuidesContainer = d3.select("#variant-guides-container");

    document.addEventListener("keyup", e => {
        if (e.keyCode === 27 && searchContainer.classed("shown")) searchContainer.classed("shown", false);
        else if (e.keyCode === 27 && exportContainer.classed("shown")) exportContainer.classed("shown", false);
        else if (e.keyCode === 27 && variantGuidesContainer.classed("shown"))
            variantGuidesContainer.classed("shown", false);
    });

    // noinspection JSCheckFunctionSignatures
    Promise.all([
        fetch(new Request(`/api/?page=${page.toString(10)}&items_per_page=${itemsPerPage}`)),
        fetch(new Request(`/api/guides?page=${page.toString(10)}&items_per_page=${itemsPerPage}`)),
        fetch(new Request("/api/entries")),
        fetch(new Request("/api/fields")),
        fetch(new Request("/api/metadata"))
    ]).then(rs => Promise.all(rs.map(r => r.json()))).then(data => {
        itemsPerPage = parseInt(d3.select("#items-per-page").property("value"), 10);
        loadedVariants = data[0];
        loadedGuides = data[1];
        totalVariantsCount = data[2]["variants"];
        totalGuidesCount = data[2]["guides"];
        variantFields = data[3]["variants"];
        guideFields = data[3]["guides"];
        metadata = data[4];
        selectedChromosomes = [...metadata["chr"]];
        selectedGeneLocations = [...metadata["geneloc"]];

        startPos = parseInt(metadata["min_pos"], 10);
        endPos = parseInt(metadata["max_pos"], 10);

        populateEntryTable();
        updatePagination();
        updateTableColumnHeaders();

        d3.select("#view-variants").on("click", () => selectTablePage("variants"));
        d3.select("#view-guides").on("click", () => selectTablePage("guides"));

        if (window.location.hash === "#variants") selectTablePage("variants");
        if (window.location.hash === "#guides") selectTablePage("guides");

        d3.select("#show-export").on("click", () => exportContainer.classed("shown", true));
        d3.select("#hide-export").on("click", () => exportContainer.classed("shown", false));

        d3.select("#hide-variant-guides").on("click", () => variantGuidesContainer.classed("shown", false));
        const variantGuideTableColumns = d3.select("table#variant-guides-table thead").append("tr")
            .selectAll("th").data(guideFields, f => f["name"]);

        variantGuideTableColumns.enter().append("th").text(f => f["name"])
            .append("span").attr("class", "material-icons");
        variantGuideTableColumns.exit().remove();

        d3.select("#export-variants").on("click", () => {
            let downloadURL = new URL("/api/tsv", window.location.origin);
            let params = getSearchParams();
            Object.keys(params).forEach(key => downloadURL.searchParams.append(key, params[key]));
            window.location.href = downloadURL.toString();
        });

        d3.select("#export-guides").on("click", () => {
            let downloadURL = new URL("/api/guides/tsv", window.location.origin);
            let params = getSearchParams();
            Object.keys(params).forEach(key => downloadURL.searchParams.append(key, params[key]));
            window.location.href = downloadURL.toString();
        });


        const chromosomeLabels = d3.select("#chromosome-checkboxes").selectAll("label").data(metadata["chr"])
            .enter()
            .append("label")
            .attr("for", c => c);
        chromosomeLabels.append("input")
            .attr("type", "checkbox")
            .attr("id", c => c)
            .attr("class", "chr-checkbox")
            .attr("name", c => c)
            .attr("checked", "checked")
            .on("change", function () {
                selectedChromosomes = [];
                d3.selectAll(".chr-checkbox")
                    .filter(function () { return d3.select(this).property("checked"); })
                    .each(function () { selectedChromosomes.push(d3.select(this).attr("id")); });

                if (selectedChromosomes.length === 0) {
                    this.checked = true;
                }
            });
        chromosomeLabels.append("span").text(c => `${c.replace("chr", "")}`);


        d3.select("#start")
            .attr("min", metadata["min_pos"])
            .attr("max", metadata["max_pos"])
            .property("value", metadata["min_pos"])
            .on("change", function () {
                startPos = parseInt(this.value, 10);
                if (isNaN(startPos)) startPos = parseInt(metadata["min_pos"], 10);
            });
        d3.select("#end")
            .attr("min", metadata["min_pos"])
            .attr("max", metadata["max_pos"])
            .property("value", metadata["max_pos"])
            .on("change", function () {
                endPos = parseInt(this.value, 10);
                if (isNaN(endPos)) endPos = parseInt(metadata["max_pos"], 10);
            });


        const geneLocationLabels = d3.select("#gene-location-checkboxes").selectAll("label").data(metadata["geneloc"])
            .enter()
            .append("label")
            .attr("class", "checkbox-label")
            .attr("for", l => l);
        geneLocationLabels.append("input")
            .attr("type", "checkbox")
            .attr("id", l => l)
            .attr("class", "geneloc-checkbox")
            .attr("name", l => l)
            .attr("checked", "checked")
            .on("change", function () {
                selectedGeneLocations = [];
                d3.selectAll(".geneloc-checkbox")
                    .filter(function () { return d3.select(this).property("checked"); })
                    .each(function () { selectedGeneLocations.push(d3.select(this).attr("id")); });

                if (selectedGeneLocations.length === 0) {
                    this.checked = true;
                }
            });
        geneLocationLabels.append("span").text(l => " " + l);


        d3.select("#min-mh-l")
            .attr("min", 0)
            .attr("max", metadata["max_mh_l"])
            .property("value", minMHL)
            .on("change", function () {
                minMHL = parseInt(this.value, 10);
                if (isNaN(minMHL)) minMHL = 0;
            });


        d3.select("#dbsnp").property("checked", mustHaveDBSNP).on("change", function () {
            mustHaveDBSNP = d3.select(this).property("checked");
        });
        d3.select("#clinvar").property("checked", mustHaveClinVar).on("change", function () {
            mustHaveClinVar = d3.select(this).property("checked");
        });


        d3.select("#show-advanced-search").on("click", () => searchContainer.classed("shown", true));
        d3.select("#hide-advanced-search").on("click", () => searchContainer.classed("shown", false));
        d3.select("#toggle-advanced-search-help").on("click", () => d3.select("#advanced-search-help").classed("shown",
            !d3.select("#advanced-search-help").classed("shown")));
        d3.select("#add-search-condition").on("click", () => addAdvancedSearchCondition());
        d3.select("#save-search-query").on("click", () => {
            if (advancedSearchFilters.length > 0)
                d3.select("#search-query").property("value", JSON.stringify(advancedSearchFilters));
            searchContainer.classed("shown", false);
        });

        d3.selectAll(".modal-container").on("click", function () { d3.select(this).classed("shown", false); });
        d3.selectAll(".modal").on("click", () => d3.event.stopPropagation());

        d3.select("#filter-search-form").on("submit", () => {
            d3.event.preventDefault();
            page = 1;
            reloadPage();
        });

        d3.select("#clear-filters").on("click", () => {
            selectedChromosomes = [...metadata["chr"]];

            startPos = parseInt(metadata["min_pos"], 10);
            endPos = parseInt(metadata["max_pos"], 10);

            selectedGeneLocations = [...metadata["geneloc"]];

            d3.selectAll(".chr-checkbox").property("checked", true);
            d3.selectAll(".geneloc-checkbox").property("checked", true);

            minMHL = 0;

            mustHaveDBSNP = false;
            mustHaveClinVar = false;

            d3.select("#search-query").property("value", "");
            advancedSearchFilters = [];

            updateFilterDOM();
            reloadPage();
        });

        d3.select("#first-page").on("click", () => {
            if (transitioning) return;
            page = 1;
            reloadPage();
        });

        d3.select("#prev-page").on("click", () => {
            if (transitioning) return;
            page = Math.max(page - 1, 1);
            reloadPage();
        });

        d3.select("#next-page").on("click", () => {
            if (transitioning) return;
            page = Math.min(page + 1, parseInt(getTotalPages(), 10));
            reloadPage();
        });

        d3.select("#last-page").on("click", () => {
            if (transitioning) return;
            page = parseInt(getTotalPages(), 10);
            reloadPage();
        });

        d3.select("#items-per-page").on("change", () => {
            itemsPerPage = parseInt(d3.event.target.value, 10);
            page = 1;
            reloadPage();
        });

        d3.select("#table-display").classed("loading", false);
        transitioning = false;
    });
});

function selectTablePage(p) {
    dataDisplay = p;
    window.location.hash = p;

    d3.select("table#entry-table").attr("class", dataDisplay);

    d3.select("#view-variants").classed("active", dataDisplay === "variants");
    d3.select("#view-guides").classed("active", dataDisplay === "guides");

    populateEntryTable();
    updatePagination();
    updateTableColumnHeaders();
}

function populateEntryTable() {
    const fields = (dataDisplay === "variants" ? variantFields : guideFields);
    const entries = (dataDisplay === "variants" ? loadedVariants : loadedGuides);
    const tableColumns = d3.select("table#entry-table thead tr").selectAll("th").data(fields, f => f["name"]);
    // TODO: Use original column name for display
    tableColumns.enter()
        .append("th")
        .text(f => f["name"])
        .on("click", f => {
            if (dataDisplay === "guides") return;

            if (sortBy === f["name"]) {
                sortOrder = (sortOrder === "ASC" ? "DESC" : "ASC");
            } else {
                sortOrder = "ASC";
                sortBy = f["name"];
            }

            page = 1;
            reloadPage();
        })
        .append("span").attr("class", "material-icons");
    tableColumns.exit().remove();

    const tableRows = d3.select("table#entry-table tbody").selectAll("tr")
        .data(entries, () => Math.random().toString()); // TODO: Fix IDs
    const rowEntry = tableRows.enter().append("tr");

    fields.forEach(f => rowEntry.append("td")
        .classed("lighter", e => e[f["name"]] === null || e[f["name"]] === "NA" || e[f["name"]] === "-")
        .html(e => formatTableCell(e, f)));

    rowEntry.select(".show-guides-modal").on("mousedown", e => {
        variantGuidesContainer.classed("shown", true);
        d3.select("#variant-for-guides").text(e["id"]);
        fetch(new Request(`/api/variants/${e["id"]}/guides`)).then(r => r.json()).then(guides => {
            // noinspection JSUnresolvedFunction
            const variantGuides = d3.select("#variant-guides-table tbody").selectAll("tr").data(guides, g => g["id"]);
            const variantGuideEntry = variantGuides.enter().append("tr");
            guideFields.forEach(f => variantGuideEntry.append("td")
                .classed("lighter", e => e[f["name"]] === null || e[f["name"]] === "NA" || e[f["name"]] === "-")
                .html(e => formatTableCell(e, f)));
            variantGuides.exit().remove();
        });
    });

    tableRows.exit().remove();
}

function formatTableCell(e, f) {
    if (f["name"] === "rs") {
        if (e["rs"] === null) return "-";
        return `<a href="https://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${e["rs"]}"
                   target="_blank" rel="noopener">${e["rs"]}</a>`
    } else if (f["name"] === "gene_info" && e["gene_info"] !== "-" && e["gene_info"] !== "NA") {
        return e["gene_info"]
            .split("|")
            .map(og => `<a href="https://www.ncbi.nlm.nih.gov/gene/${og.split(":")[1]}/"
                           target="_blank" rel="noopener">${og}</a>`)
            .join("|");
    } else if (f["name"] === "gene_info_clinvar" && e["gene_info_clinvar"] !== null) {
        return e["gene_info_clinvar"]
            .split("|")
            .map(og => `<a href="https://www.ncbi.nlm.nih.gov/gene/${og.split(":")[1]}/"
                           target="_blank" rel="noopener">${og}</a>`)
            .join("|");
    } else if (f["name"] === "citation" && e["citation"] !== "NA" && e["citation"] !== "-") {
        return e["citation"]
            .split(";")
            .map(id => id.substring(0, 2) === "NB"
                ? `<a href="https://www.ncbi.nlm.nih.gov/books/${id}/" target="_blank" rel="noopener">${id}</a>`
                : `<a href="https://www.ncbi.nlm.nih.gov/pubmed/${id.replace("PM", "")}/"
                      target="_blank" rel="noopener">${id}</a>`)
            .join(";");
    } else if (f["name"] === "allele_id" && e["allele_id"] !== "NA") {
        return `<a href="https://www.ncbi.nlm.nih.gov/clinvar/variation/${e["allele_id"]}/"
                   target="_blank" rel="noopener">${e["allele_id"]}</a>`;
    } else if (f["name"] === "pam_uniq" && e["pam_uniq"] !== null && e["pam_uniq"] > 0) {
        return `<strong><a class="show-guides-modal">${e["pam_uniq"]}</a></strong>`;
    }

    return e[f["name"]] === null ? "NA" : e[f["name"]]; // TODO: Maybe shouldn't always be NA
}

function updateTableColumnHeaders() {
    const fields = (dataDisplay === "variants" ? variantFields : guideFields);
    d3.selectAll("table#entry-table thead th").data(fields, f => f["name"])
        .select("span.material-icons")
        .text(f => (sortBy === f["name"] ? (sortOrder === "ASC" ? "expand_less" : "expand_more") : ""));
}

function updatePagination() {
    const totalPages = getTotalPages();

    d3.select("#current-page").text(page.toFixed(0));
    d3.select("#total-pages").text(totalPages);
    d3.select("#total-variants").text(totalVariantsCount);
    d3.select("#total-guides").text(totalGuidesCount);

    d3.select("#matching-variants-export").text(totalVariantsCount);
    d3.select("#matching-guides-export").text(totalGuidesCount);

    d3.select("#first-page").attr("disabled", page === 1 ? "disabled" : null);
    d3.select("#prev-page").attr("disabled", page === 1 ? "disabled" : null);
    d3.select("#next-page").attr("disabled", page.toString(10) === totalPages ? "disabled" : null);
    d3.select("#last-page").attr("disabled", page.toString(10) === totalPages ? "disabled" : null);
}

function reloadPage() {
    transitioning = true;

    if (itemsPerPage >= 100) d3.select("#table-display").classed("loading", true)
        .on("transitionend", () => transitioning = false);

    let variantsURL = new URL("/api/", window.location.origin);
    let guidesURL = new URL("/api/guides", window.location.origin);
    let countURL = new URL("/api/entries", window.location.origin);
    let params = {
        page: page.toString(10),
        items_per_page: itemsPerPage,
        ...getSearchParams()
    };
    Object.keys(params).forEach(key => {
        variantsURL.searchParams.append(key, params[key]);
        guidesURL.searchParams.append(key, params[key]);
        countURL.searchParams.append(key, params[key]);
    });

    // noinspection JSCheckFunctionSignatures
    return Promise.all([
            fetch(new Request(variantsURL.toString())),
            fetch(new Request(guidesURL.toString())),
            fetch(new Request(countURL.toString()))
        ])
        .then(rs => Promise.all(rs.map(r => r.json())))
        .then(data => {
            loadedVariants = data[0];
            loadedGuides = data[1];
            totalVariantsCount = data[2]["variants"];
            totalGuidesCount = data[2]["guides"];
            if (transitioning && itemsPerPage >= 100) {
                d3.select("#table-display").on("transitionend", () => {
                    populateEntryTable();
                    updatePagination();
                    updateTableColumnHeaders();
                    d3.select("#table-display").classed("loading", false);
                    transitioning = false;
                });
                // Fallback if the transitionend event is not triggered.
                setTimeout(() => d3.select("#table-display").dispatch("transitionend"), 300);
            } else {
                populateEntryTable();
                updatePagination();
                updateTableColumnHeaders();
                d3.select("#table-display").classed("loading", false);
                transitioning = false;
            }
        });
}

function getTotalPages() {
    return Math.max(Math.ceil(totalVariantsCount / itemsPerPage), 1).toFixed(0);
}

function updateFilterDOM() {
    d3.select("#start").property("value", startPos);
    d3.select("#end").property("value", endPos);

    d3.select("#min-mh-l").property("value", minMHL);

    d3.select("#dbsnp").property("checked", mustHaveDBSNP);
    d3.select("#clinvar").property("checked", mustHaveClinVar);
}

function addAdvancedSearchCondition() {
    advancedSearchFilters.push({
        id: getFilterID(),
        boolean: DEFAULT_CONDITION_BOOLEAN,
        negated: false,
        field: "",
        operator: "equals",
        value: ""
    });

    updateSearchFilterDOM();
}

function updateSearchFilterDOM() {
    const filters = d3.select("ul#advanced-search-conditions")
        .selectAll("li.advanced-search-filter")
        .data(advancedSearchFilters, c => c.id);
    const filterEntry = filters.enter()
        .append("li")
        .attr("class", "advanced-search-filter")
        .attr("id", c => `advanced-search-filter-${c.id}`);
    filterEntry.append("div").attr("class", "boolean-type-placeholder");
    filterEntry.filter((f, i) => i > 0)
        .append("select")
        .attr("class", "select-boolean-type")
        .on("change", function (f) {
            f.boolean = this.value;
            updateSearchFilterDOM();
        })
        .selectAll("option")
        .data(["AND", "OR"])
        .enter()
        .append("option")
        .attr("value", b => b)
        .attr("selected", b => b === DEFAULT_CONDITION_BOOLEAN ? "selected" : null)
        .text(b => b);
    filterEntry.append("select")
        .attr("class", "select-condition-negation")
        .on("change", function (f) {
            f.negated = this.value !== "";
        })
        .selectAll("option")
        .data(["", "NOT"])
        .enter()
        .append("option")
        .attr("value", n => n)
        .text(n => n);
    filterEntry.append("select")
        .attr("class", "select-condition-field")
        .on("change", function (f) {
            f.field = this.value;
            updateSearchFilterDOM();
        })
        .selectAll("option")
        .data([{name: ""}, ...variantFields], f => f["name"])
        .enter()
        .append("option")
        .attr("value", f => f["name"])
        .text(f => f["name"]);
    filterEntry.append("select")
        .attr("class", "select-operator")
        .on("change", function (f) {
            f.operator = this.value;
            d3.select(`li#advanced-search-filter-${f.id}`).select(".search-filter-value")
                .attr("disabled", f.operator === "is_null" ? "disabled" : null);
        });
    filterEntry.append("input")
        .attr("type", "text")
        .attr("class", "search-filter-value")
        .on("change", function (f) {
            f.value = this.value;
        });
    filterEntry.append("button")
        .attr("class", "remove-search-condition")
        .on("click", c => {
            advancedSearchFilters = advancedSearchFilters.filter(c2 => c2.id !== c.id);
            updateSearchFilterDOM();
        })
        .append("span")
        .attr("class", "material-icons")
        .text("close");
    filters.exit().remove();

    const allFilters = filterEntry.merge(filters);
    allFilters.select("div.boolean-type-placeholder").style("display", (f, i) => i === 0 ? "inline-block" : "none");
    allFilters.select("select.select-boolean-type").style("display", (f, i) => i > 0 ? "inline-block" : "none");
    const filterOperators = allFilters.select("select.select-operator")
        .selectAll("option")
        .data(f => [
            ...CONDITION_OPERATORS["BOTH"],
            ...(f.field === "" ? [] : CONDITION_OPERATORS[variantFields.find(f2 => f2["name"] === f.field)["type"]]),
            ...(f.field !== ""
                ? (variantFields.find(f2 => f2["name"] === f.field)["notnull"] === 0
                    ? CONDITION_OPERATORS["NULLABLE"]
                    : [])
                : [])
        ], o => o);
    filterOperators.enter().append("option").attr("value", o => o).text(o => o);
    filterOperators.exit().remove();
}

function getFilterID() {
    currentFilterID++;
    return currentFilterID - 1;
}

function getSearchParams() {
    return {
        sort_by: sortBy,
        sort_order: sortOrder,

        chr: selectedChromosomes,
        start: startPos,
        end: endPos,
        geneloc: selectedGeneLocations,
        min_mh_l: minMHL,

        dbsnp: mustHaveDBSNP,
        clinvar: mustHaveClinVar,

        search_query: d3.select("#search-query").property("value")
    };
}

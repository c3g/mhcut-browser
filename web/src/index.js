import * as d3 from "d3";
import Modal from "./Modal";

import {
    CONDITION_OPERATORS,
    DEFAULT_CONDITION_BOOLEAN,
    COLUMN_HELP_TEXT,
    VARIANTS_LAYOUT,
    GUIDES_LAYOUT
} from "./constants";


let dataDisplay = "variants";

let page = 1;
let itemsPerPage = 100;
let loadedVariants = [];
let loadedGuides = [];
let totalVariantsCount = 0;
let totalGuidesCount = 0;

// Used in advanced search (for now)
let variantFields = [];

let metadata = {};

let sortBy = "id";
let sortOrder = "ASC";

let expandedGroups = {
    variants: new Set(),
    guides: new Set()
};

let selectedChromosome = null;

let startPos = 0;
let endPos = 12000000000000;

let selectedVariantLocations = [];

let minMH1L = 3;

let mustHaveClinVar = false;

let mustHaveNGGPAM = false;
let mustHaveUniqueGuide = false;

let currentFilterID = 0;
let advancedSearchFilters = [];

let transitioning = true;
let loadingEntryCounts = false;

let searchModal = null;
let exportModal = null;
let variantGuidesModal = null;
let termsOfUseModal = null;
let reportBugModal = null;

let emailToken = null;

const dbSNPURL = rs => `https://www.ncbi.nlm.nih.gov/snp/rs${rs}/`;
const geneURL = gene => `https://www.ncbi.nlm.nih.gov/gene/${gene}/`;
const bookshelfURL = nbk => `https://www.ncbi.nlm.nih.gov/books/${nbk}/`;
const pubMedURL = pm => `https://www.ncbi.nlm.nih.gov/pubmed/${pm}/`;
const pmcURL = pmc => `https://www.ncbi.nlm.nih.gov/pmc/articles/${pmc}/`;
const clinVarURL = cv => `https://www.ncbi.nlm.nih.gov/clinvar/variation/${cv}/`;


document.addEventListener("DOMContentLoaded", async function () {
    // Initialize modals.

    searchModal = new Modal("#advanced-search-container");
    exportModal = new Modal("#export-options-container");
    variantGuidesModal = new Modal("#variant-guides-container");
    termsOfUseModal = new Modal("#terms-of-use-container");
    reportBugModal = new Modal("#report-bug-container");
    reportBugModal.addListener("modalShow", async () => emailToken = await fetchJSON("/api/token"));
    reportBugModal.addListener("modalHide", () => emailToken = null);


    // Initialize items per page

    itemsPerPage = parseInt(d3.select("#items-per-page").property("value"), 10);


    // Start parallel API calls to load data

    loadingEntryCounts = true;

    d3.select("#apply-filters").attr("disabled", "disabled");
    d3.select("#clear-filters").attr("disabled", "disabled");

    await Promise.all([
        (async () => {
            // Load various data

            [loadedVariants, loadedGuides, variantFields, metadata] = await Promise.all([
                fetchJSON(`/api/?page=${page.toString(10)}&items_per_page=${itemsPerPage}`),
                fetchJSON(`/api/guides?page=${page.toString(10)}&items_per_page=${itemsPerPage}`),
                fetchJSON("/api/variants/fields"),
                fetchJSON("/api/metadata")
            ]);
        })(),
        (async () => {
            // Start loading variant / guide counts

            [totalVariantsCount, totalGuidesCount] = await Promise.all([
                fetchJSON("/api/variants/entries"),
                fetchJSON("/api/guides/entries")
            ]);
        })()
    ]);

    loadingEntryCounts = false;

    d3.select("#apply-filters").attr("disabled", null);
    d3.select("#clear-filters").attr("disabled", null);

    updatePagination();

    // Finish loading all data


    d3.select("#toggle-all-additional-columns").on("click", () => {
        const set = expandedGroups[dataDisplay];
        const layout = getLayout();

        if (set.size === layout.length) {
            // All are expanded, so contract them
            set.clear();
        } else {
            // Some are still contracted, so expand them
            layout.forEach(g => set.add(g.group_name));
        }

        populateEntryTable();
        updateTableColumnHeaders();
    });

    selectedVariantLocations = [...metadata["location"]];

    startPos = parseInt(metadata["min_pos"], 10);
    endPos = parseInt(metadata["max_pos"], 10);

    populateEntryTable();
    updateTableColumnHeaders();

    d3.select("#view-variants").on("click", () => selectTablePage("variants"));
    d3.select("#view-guides").on("click", () => selectTablePage("guides"));

    if (window.location.hash === "#variants") selectTablePage("variants");
    if (window.location.hash === "#guides") selectTablePage("guides");

    d3.select("#show-export").on("click", () => exportModal.show());

    d3.select("#sidebar-toggle").on("click", () => {
        d3.select("body").classed("no-sidebar", !d3.select("body").classed("no-sidebar"));
        d3.select("#sidebar-toggle").classed("active", !d3.select("body").classed("no-sidebar"));
    });

    // TODO: FIX THIS (SHOULDN'T BE HERE)

    const variantGuideTableGroups = d3.select("table#variant-guides-table thead").append("tr")
        .attr("class", "group-row")
        .selectAll("th").data(GUIDES_LAYOUT, g => g.group_name);

    variantGuideTableGroups.enter().append("th")
        .attr("colspan", g => g.default_columns.length + g.optional_columns.length)
        .append("div").append("span").attr("class", "group-name").text(g => g.group_name);

    const variantGuideTableColumns = d3.select("table#variant-guides-table thead").append("tr")
        .attr("class", "header-row")
        .selectAll("th").data(headersFromLayout(GUIDES_LAYOUT, true), h => h.column);

    variantGuideTableColumns.enter().append("th")
        .attr("class", h => h.classes)
        .append("div")
        .text(h => h.column)
        .on("mouseover", h => showColumnHelp(d3.event, h.column))
        .on("mousemove", () => updateColumnHelp(d3.event))
        .on("mouseout", () => hideColumnHelp())
        .append("span").attr("class", "material-icons");
    variantGuideTableColumns.exit().remove();

    d3.select("#export-variants")
        .on("click", () => {
            let downloadURL = new URL("/api/tsv", window.location.origin);
            const params = getSearchParams();
            Object.keys(params).forEach(key => downloadURL.searchParams.append(key, params[key]));
            window.location.href = downloadURL.toString();
        })
        .on("mouseover", () => {
            d3.select("#label-guides-with-variants-info").transition().style("opacity", 0.5);
        })
        .on("mouseout", () => {
            d3.select("#label-guides-with-variants-info").transition().style("opacity", 1);
        });

    d3.select("#export-guides").on("click", () => {
        let downloadURL = new URL("/api/guides/tsv", window.location.origin);
        let params = getSearchParams();
        Object.keys(params).forEach(key => downloadURL.searchParams.append(key, params[key]));
        downloadURL.searchParams.append("guides_with_variant_info",
            d3.select("#guides-with-variant-info").property("checked"));
        window.location.href = downloadURL.toString();
    });

    d3.select("#export-combined").on("click", () => {
        let downloadURL = new URL("/api/combined/tsv", window.location.origin);
        let params = getSearchParams();
        Object.keys(params).forEach(key => downloadURL.searchParams.append(key, params[key]));
        downloadURL.searchParams.append("guides_with_variant_info",
            d3.select("#guides-with-variant-info").property("checked"));
        window.location.href = downloadURL.toString();
    });


    d3.select("#search-query").on("change", () => {
        try {
            const filters = JSON.parse(d3.event.target.value);
            if (validateAdvancedSearchFilters(filters)) {
                advancedSearchFilters = filters;
            }
        } catch {
            advancedSearchFilters = [];
        }
        updateSearchFilterDOM();
    });


    const onPositionQueryChange = () => {
        const positionData = d3.select("#position-query").property("value").replace(/[ ]/g, "").split(":");
        if (![1, 2].includes(positionData.length) || positionData[0] === "") {
            selectedChromosome = null;
            startPos = parseInt(metadata["min_pos"], 10);
            endPos = parseInt(metadata["max_pos"], 10);
            return;
        }

        const chromosome = positionData[0].toLocaleLowerCase()
            .replace("x", "X")
            .replace("y", "Y");
        selectedChromosome = chromosome;

        if (positionData.length === 1) {
            startPos = parseInt(metadata["min_pos"], 10);
            endPos = parseInt(metadata["max_pos"], 10);
            return;
        }

        const startEnd = positionData[1].split("-").map(p => parseInt(p, 10));
        if (startEnd.length !== 2) return;

        selectedChromosome = chromosome;
        startPos = startEnd[0];
        endPos = startEnd[1];
    };

    d3.select("#position-query").on("change", onPositionQueryChange);
    onPositionQueryChange();


    const geneLocationLabels = d3.select("#gene-location-checkboxes").selectAll("label").data(metadata["location"])
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
            selectedVariantLocations = [];

            d3.selectAll(".geneloc-checkbox")
                .filter(function () { return d3.select(this).property("checked"); })
                .each(function () { selectedVariantLocations.push(d3.select(this).attr("id")); });

            if (selectedVariantLocations.length === 0) this.checked = true;
        });
    geneLocationLabels.append("span").text(l => " " + l);


    d3.select("#min-mh-1l")
        .attr("min", 0)
        .attr("max", metadata["max_mh_1l"])
        .property("value", minMH1L)
        .on("change", function () {
            minMH1L = parseInt(this.value, 10);
            if (isNaN(minMH1L)) minMH1L = 0;
        });


    d3.select("#clinvar").property("checked", mustHaveClinVar).on("change", () => {
        mustHaveClinVar = d3.select(d3.event.target).property("checked");
    });


    d3.select("#ngg-pam-available").property("checked", mustHaveNGGPAM).on("change", () => {
        mustHaveNGGPAM = d3.select(d3.event.target).property("checked");
    });

    d3.select("#unique-guide-available").property("checked", mustHaveUniqueGuide).on("change", () => {
        mustHaveUniqueGuide = d3.select(d3.event.target).property("checked");
    });


    d3.select("#show-advanced-search").on("click", () => searchModal.show());
    d3.select("#toggle-advanced-search-help").on("click", () => d3.select("#advanced-search-help").classed("shown",
        !d3.select("#advanced-search-help").classed("shown")));
    d3.select("#add-search-condition").on("click", () => addAdvancedSearchCondition());
    d3.select("#save-search-query").on("click", () => {
        if (advancedSearchFilters.length > 0) {
            d3.select("#search-query").property("value", JSON.stringify(advancedSearchFilters));
        }

        searchModal.hide();
    });

    d3.select("#filter-search-form").on("submit", async () => {
        if (loadingEntryCounts) return;
        d3.event.preventDefault();
        page = 1;
        await reloadPage(true);
    });

    d3.select("#clear-filters").on("click", async () => {
        resetFilters();
        updateFilterDOM();
        await reloadPage(true);
    });

    d3.select("#first-page").on("click", async () => {
        if (transitioning) return;
        page = 1;
        await reloadPage(false);
    });

    d3.select("#prev-page").on("click", async () => {
        if (transitioning) return;
        page = Math.max(page - 1, 1);
        await reloadPage(false);
    });

    d3.select("#next-page").on("click", async () => {
        if (transitioning) return;
        page = Math.min(page + 1, parseInt(getTotalPages(), 10));
        await reloadPage(false);
    });

    d3.select("#last-page").on("click", async () => {
        if (transitioning) return;
        page = parseInt(getTotalPages(), 10);
        await reloadPage(false);
    });

    d3.select("#items-per-page").on("change", async () => {
        itemsPerPage = parseInt(d3.event.target.value, 10);
        page = 1;
        await reloadPage(false);
    });

    d3.select("#terms-of-use").on("click", () => termsOfUseModal.show());
    d3.select("#report-bug").on("click", () => reportBugModal.show());

    d3.select("#report-bug-submit").on("click", async () => {
        const response = await fetch("/api/report", {
            method: "POST",
            mode: "cors",
            cache: "no-cache",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                token: emailToken.token,
                email: d3.select("#report-bug-email").property("value"),
                text: d3.select("#report-bug-text").property("value")
            })
        });

        const result = await response.json();
        alert(result.success
            ? "Bug report submitted successfully!"
            : `Something went wrong while submitting a bug report. Error message: ${result.reason}`);

        reportBugModal.hide();
    });

    d3.select("#table-display").classed("loading", false);
    transitioning = false;
});

function selectTablePage(p) {
    dataDisplay = p;
    window.location.hash = p;

    d3.select("table#entry-table").attr("class", dataDisplay);

    d3.select("#view-variants").classed("active", dataDisplay === "variants");
    d3.select("#view-guides").classed("active", dataDisplay === "guides");

    populateEntryTable();
    updateTableColumnHeaders();
}

function getLayout() {
    return dataDisplay === "variants" ? VARIANTS_LAYOUT : GUIDES_LAYOUT;
}

function headersFromLayout(layout, forceAll) {
    let headers = [];

    layout.forEach((group, gi) => {
        let columns = [...group.default_columns];
        if (expandedGroups[dataDisplay].has(group.group_name) || forceAll) {
            columns.push(...group.optional_columns);
        }

        columns.forEach((column, ci) => {
            let classes = gi % 2 === 0 ? "even" : "odd";
            if (ci === 0) classes += " first";
            if (ci === columns.length - 1) classes += " last";
            if (column === "cartoon") classes += " no-click";
            headers.push({column, classes: classes.trim()});
        });
    });

    return headers;
}

function populateEntryTable() {
    const layout = getLayout();
    const set = expandedGroups[dataDisplay];


    // Update Show/Hide Columns Button

    d3.select("#toggle-all-additional-columns")
        .text(`${set.size === layout.length ? "Hide" : "Show"} All Additional Columns`);


    // Update Table

    const entries = (dataDisplay === "variants" ? loadedVariants : loadedGuides);
    const headers = headersFromLayout(layout, false);

    const tableGroups = d3.select("table#entry-table thead tr.group-row")
        .selectAll("th")
        .data(layout, () => Math.random().toString()); // TODO: Fix ID

    const groupDiv = tableGroups.enter()
        .append("th")
        .attr("colspan", g =>
            g.default_columns.length + (set.has(g.group_name) ? g.optional_columns.length : 0))
        .append("div");

    groupDiv.append("span")
        .attr("class", "group-name")
        .text(g => g.group_name);

    groupDiv.append("button")
        .classed("toggle-optional-columns", true)
        .classed("hidden", g => g.optional_columns.length === 0)
        .html(g => set.has(g.group_name)
            ? '<span class="material-icons">chevron_left</span><span class="material-icons">chevron_left</span>'
            : '<span class="material-icons">chevron_right</span><span class="material-icons">chevron_right</span>')
        .on("click", g => {
            if (set.has(g.group_name)) {
                set.delete(g.group_name);
            } else {
                set.add(g.group_name);
            }

            // TODO: IS THIS RIGHT?
            populateEntryTable();
            updateTableColumnHeaders();
        });

    tableGroups.exit().remove();

    const tableColumns = d3.select("table#entry-table thead tr.header-row")
        .selectAll("th")
        .data(headers, h => h.column);

    const column = tableColumns.enter()
        .append("th")
        .attr("class", f => f.classes)
        .on("mouseover", f => showColumnHelp(d3.event, f.column))
        .on("mousemove", () => updateColumnHelp(d3.event))
        .on("mouseout", () => hideColumnHelp())
        .on("click", async f => {
            if (dataDisplay === "guides" || f.column === "cartoon") return;

            if (sortBy === f.column) {
                sortOrder = (sortOrder === "ASC" ? "DESC" : "ASC");
            } else {
                sortOrder = "ASC";
                sortBy = f.column;
            }

            page = 1;
            await reloadPage(false);
        });
    column.append("div").text(f => f.column).append("span").attr("class", "material-icons");
    tableColumns.exit().remove();

    const tableRows = d3.select("table#entry-table tbody").selectAll("tr")
        .data(entries, () => Math.random().toString()); // TODO: Fix IDs
    const rowEntry = tableRows.enter().append("tr");

    headers.forEach(f => rowEntry.append("td")
        .attr("class", e => getTableCellClasses(e, f))
        .append("div")
        .html(e => getTableCellContents(e, f)));

    rowEntry.select(".show-guides-modal").on("mousedown", async e => {
        variantGuidesModal.show();
        d3.select("#variant-for-guides").text(e["id"]);

        const guides = await fetchJSON(`/api/variants/${e["id"]}/guides`);
        const variantGuides = d3.select("#variant-guides-table tbody").selectAll("tr").data(guides, g => g["id"]);
        const variantGuideEntry = variantGuides.enter().append("tr");
        headersFromLayout(GUIDES_LAYOUT, true).forEach(h => variantGuideEntry.append("td")
            .attr("class", e => getTableCellClasses(e, h))
            .append("div")
            .html(e => getTableCellContents(e, h)));
        variantGuides.exit().remove();
        d3.select("#export-variant-guides").on("click", () => {
            const downloadURL = new URL(`/api/variants/${e["id"]}/guides/tsv`, window.location.origin);
            window.location.href = downloadURL.toString();
        });
    });

    tableRows.exit().remove();
}

function getTableCellClasses(e, f) {
    let classes = f.classes;
    if (e[f.column] === null || e[f.column] === "NA" || e[f.column] === "-") {
        classes += " lighter"
    }
    return classes;
}

function getTableCellContents(e, f) {
    if (f.column === "rs") {
        if (e["rs"] === null) return "-";
        return e["rs"].toString().split("|")
            .map(rs => `<a href="${dbSNPURL(rs)}" target="_blank" rel="noopener">${rs}</a>`)
            .join("|");
    } else if ((f.column === "gene_info" && e["gene_info"] !== "-" && e["gene_info"] !== "NA")
        || (f["column_name"] === "gene_info_clinvar" && e["gene_info_clinvar"] !== null)) {
        return e[f.column].split("|")
            .map(og => `<a href="${geneURL(og.split(":")[1])}" target="_blank" rel="noopener">${og}</a>`)
            .join("|");
    } else if (f.column === "citation" && e["citation"] !== "NA" && e["citation"] !== "-") {
        return e["citation"].split(";")
            .map(id => id.substring(0, 2) === "NB"
                ? `<a href="${bookshelfURL(id)}" target="_blank" rel="noopener">${id}</a>`
                : (id.substring(0, 3) === "PMC"
                    ? `<a href="${pmcURL(id)}" target="_blank" rel="noopener">${id}</a>`
                    : `<a href="${pubMedURL(id.replace("PM", ""))}" target="_blank" rel="noopener">${id}</a>`))
            .join(";");
    } else if (f.column === "allele_id" && e["allele_id"] !== null) {
        return `<a href="${clinVarURL(e["allele_id"])}/" target="_blank" rel="noopener">${e["allele_id"]}</a>`;
    } else if (f.column === "pam_uniq" && e["pam_uniq"] !== null && e["pam_uniq"] > 0) {
        return `<strong><a class="show-guides-modal">${e["pam_uniq"]}</a></strong>`;
    } else if (f.column === "cartoon" && e["cartoon"] !== null) {
        return `<pre>${e["cartoon"]}</pre>`;
    } else if (f.column.includes("indelphi") && e[f.column] !== null) {
        return `<div class="progress-bar-container">
                    <div class="progress-bar-outer">
                        <div class="progress-bar-inner" style="width: ${e[f.column]}%;"></div>
                    </div>
                    <div class="progress-bar-scalar">${e[f.column]}%</div>
                </div>`
    }

    return e[f.column] === null ? "NA" : e[f.column]; // TODO: Maybe shouldn't always be NA
}

function updateTableColumnHeaders() {
    const layout = getLayout();
    const headers = headersFromLayout(layout, false);

    d3.selectAll("table#entry-table thead tr.header-row th").data(headers, h => h.column)
        .attr("class", f => f.classes)
        .select("div")
        .select("span.material-icons")
        .text(h => (sortBy === h.column ? (sortOrder === "ASC" ? "expand_less" : "expand_more") : ""));
}

function getLoadingPagesText() {
    return loadedVariants.length >= itemsPerPage ? "multiple" : "1";
}

function getLoadingVariantsText() {
    return loadedVariants.length >= itemsPerPage ? "many" : loadedVariants.length.toString(10);
}

function getLoadingGuidesText() {
    return loadedVariants.length >= itemsPerPage ? "many" : loadedGuides.length.toString(10);
}

function updatePagination() {
    const totalPages = getTotalPages();

    d3.select("#current-page").text(page.toFixed(0));
    d3.select("#total-pages").text(loadingEntryCounts ? getLoadingPagesText() : totalPages);
    d3.select("#total-variants").text(loadingEntryCounts ? getLoadingVariantsText() : totalVariantsCount);
    d3.select("#total-guides").text(loadingEntryCounts ? getLoadingGuidesText() : totalGuidesCount);

    d3.select("#matching-variants-export").text(loadingEntryCounts ? getLoadingVariantsText() : totalVariantsCount);
    d3.select("#matching-guides-export").text(loadingEntryCounts ? getLoadingGuidesText() : totalGuidesCount);

    d3.select("#first-page").attr("disabled", page === 1 ? "disabled" : null);
    d3.select("#prev-page").attr("disabled", page === 1 ? "disabled" : null);
    d3.select("#next-page").attr("disabled", (page.toString(10) === totalPages) ? "disabled" : null);
    d3.select("#last-page").attr("disabled", (page.toString(10) === totalPages || loadingEntryCounts)
        ? "disabled" : null);
}

async function reloadPage(reloadCounts) {
    transitioning = true;

    if (itemsPerPage >= 100) d3.select("#table-display").classed("loading", true)
        .on("transitionend", () => transitioning = false);

    let variantsURL = new URL("/api/", window.location.origin);
    let guidesURL = new URL("/api/guides", window.location.origin);
    let variantCountURL = new URL("/api/variants/entries", window.location.origin);
    let guideCountURL = new URL("/api/guides/entries", window.location.origin);
    let params = {
        page: page.toString(10),
        items_per_page: itemsPerPage,
        ...getSearchParams()
    };
    Object.keys(params).forEach(key => {
        variantsURL.searchParams.append(key, params[key]);
        guidesURL.searchParams.append(key, params[key]);
        if (reloadCounts) {
            variantCountURL.searchParams.append(key, params[key]);
            guideCountURL.searchParams.append(key, params[key]);
        }
    });

    if (reloadCounts) {
        totalVariantsCount = 0;
        totalGuidesCount = 0;

        loadingEntryCounts = true;
        d3.select("#apply-filters").attr("disabled", "disabled");
        d3.select("#clear-filters").attr("disabled", "disabled");
        updatePagination();
    }

    try {
        [loadedVariants, loadedGuides] = await Promise.all([
            fetchJSON(variantsURL.toString()),
            fetchJSON(guidesURL.toString())
        ]);

        if (loadedVariants.length === itemsPerPage && loadingEntryCounts) {
            // Re-enable next page button to let people do some basic exploration while counts are loading...
            totalVariantsCount = page * itemsPerPage + 1;
        } else if (page === 1 && loadedVariants.length < itemsPerPage && loadingEntryCounts) {
            totalVariantsCount = loadedVariants.length;
            totalGuidesCount = loadedGuides.length;
            d3.select("#apply-filters").attr("disabled", null);
            d3.select("#clear-filters").attr("disabled", null);
            loadingEntryCounts = false;
        }

        updatePagination();

        if (reloadCounts && loadingEntryCounts && loadedVariants.length !== 0) {
            [totalVariantsCount, totalGuidesCount] = await Promise.all([
                fetchJSON(variantCountURL.toString()),
                fetchJSON(guideCountURL.toString())
            ]);

            loadingEntryCounts = false;
            d3.select("#apply-filters").attr("disabled", null);
            d3.select("#clear-filters").attr("disabled", null);
            updatePagination();
        } else if (loadedVariants.length === 0) {
            d3.select("#apply-filters").attr("disabled", null);
            d3.select("#clear-filters").attr("disabled", null);
        }

        if (transitioning && itemsPerPage >= 100) {
            d3.select("#table-display").on("transitionend", () => {
                populateEntryTable();
                updateTableColumnHeaders();
                d3.select("#table-display").classed("loading", false);
                transitioning = false;
            });
            // Fallback if the transitionend event is not triggered.
            setTimeout(() => d3.select("#table-display").dispatch("transitionend"), 300);
        } else {
            populateEntryTable();
            updateTableColumnHeaders();
            d3.select("#table-display").classed("loading", false);
            transitioning = false;
        }
    } catch (err) {
        console.error(err);
    }
}

function getTotalPages() {
    return Math.max(Math.ceil(totalVariantsCount / itemsPerPage), 1).toFixed(0);
}

function resetFilters() {
    selectedChromosome = null;

    startPos = parseInt(metadata["min_pos"], 10);
    endPos = parseInt(metadata["max_pos"], 10);

    selectedVariantLocations = [...metadata["location"]];

    d3.selectAll(".chr-checkbox").property("checked", true);
    d3.selectAll(".geneloc-checkbox").property("checked", true);

    minMH1L = 3;

    mustHaveClinVar = false;

    mustHaveNGGPAM = false;
    mustHaveUniqueGuide = false;

    d3.select("#search-query").property("value", "");
    advancedSearchFilters = [];
}

function updateFilterDOM() {
    d3.select("#start").property("value", startPos);
    d3.select("#end").property("value", endPos);

    d3.select("#min-mh-1l").property("value", minMH1L);

    d3.select("#clinvar").property("checked", mustHaveClinVar);

    d3.select("#ngg-pam-available").property("checked", mustHaveNGGPAM);
    d3.select("#unique-guide-available").property("checked", mustHaveUniqueGuide);
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

function validateAdvancedSearchFilters(filters) {
    let valid = true;

    filters.forEach(f => {
        valid = valid && f.hasOwnProperty("id");
        valid = valid && f.hasOwnProperty("boolean");
        valid = valid && f.hasOwnProperty("negated");
        valid = valid && f.hasOwnProperty("field");
        valid = valid && f.hasOwnProperty("operator");
        valid = valid && f.hasOwnProperty("value");
    });

    return valid;
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
        .data([{column_name: ""}, ...headersFromLayout(VARIANTS_LAYOUT, true).filter(f => f.column !== "cartoon")],
            f => f["column_name"])
        .enter()
        .append("option")
        .attr("value", f => f.column)
        .text(f => f.column);
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
            ...CONDITION_OPERATORS.both,
            ...(f.field !== ""
                ? (CONDITION_OPERATORS[variantFields[f.field]["data_type"]] || [])
                : []),
            ...(f.field !== ""
                ? (variantFields[f.field]["is_nullable"] === "YES"
                    ? CONDITION_OPERATORS.nullable
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

        chr: selectedChromosome,
        start: startPos,
        end: endPos,
        location: selectedVariantLocations,
        min_mh_1l: minMH1L,

        clinvar: mustHaveClinVar,

        ngg_pam_avail: mustHaveNGGPAM,
        unique_guide_avail: mustHaveUniqueGuide,

        search_query: d3.select("#search-query").property("value")
    };
}


function showColumnHelp(event, columnName) {
    d3.select("#column-help-text")
        .classed("shown", true)
        .style("top", `${(event.clientY + 10).toString(10)}px`)
        .style("left", `${(event.clientX + 15).toString(10)}px`)
        .text(COLUMN_HELP_TEXT[columnName]);
}

function updateColumnHelp(event) {
    d3.select("#column-help-text")
        .style("top", `${(event.clientY + 10).toString(10)}px`)
        .style("left", `${(event.clientX + 15).toString(10)}px`);
}

function hideColumnHelp() {
    d3.select("#column-help-text").classed("shown", false);
}


async function fetchJSON(url) {
    return (await fetch(url)).json();
}

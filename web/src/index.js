import * as d3 from "d3";

let page = 1;
let itemsPerPage = 100;
let loadedEntries = [];
let totalCount = 0;
let fields = [];

document.addEventListener("DOMContentLoaded", function () {
    Promise.all([
        fetch(new Request(`/api/?page=${page.toString(10)}&items_per_page=${itemsPerPage}`)),
        fetch(new Request("/api/entries")),
        fetch(new Request("/api/fields")),
    ]).then(rs => Promise.all(rs.map(r => r.json()))).then(data => {
        loadedEntries = data[0];
        totalCount = parseInt(data[1], 10);
        fields = data[2];
        populateEntryTable();
        updatePagination();

        d3.select("#prev-page").on("click", () => {
            page = Math.max(page - 1, 1);
            reloadPage();
        });

        d3.select("#next-page").on("click", () => {
            page = Math.min(page + 1, parseInt(getTotalPages(), 10));
            reloadPage();
        });

        d3.select("#items-per-page").on("change", () => {
            itemsPerPage = parseInt(d3.event.target.value, 10);
            page = 1;
            reloadPage();
        });

        d3.select("#table-display").classed("loading", false);
    });
});

function populateEntryTable() {
    const tableColumns = d3.select("table#entry-table thead").selectAll("th").data(fields, f => f["name"]);
    tableColumns.enter().append("th").text(f => f["name"]); // TODO: Use original column name for display
    tableColumns.exit().remove();

    const tableRows = d3.select("table#entry-table tbody").selectAll("tr").data(loadedEntries, e => e["id"]);
    const rowEntry = tableRows.enter().append("tr");

    fields.forEach(f => rowEntry.append("td")
        .classed("lighter", e => e[f["name"]] === null || e[f["name"]] === "NA" || e[f["name"]] === "-")
        .html(e => formatEntryCell(e, f)));

    tableRows.exit().remove();
}

function formatEntryCell(e, f) {
    if (f["name"] === "rs") {
        return `<a href="https://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=${e["rs"]}"
                   target="_blank" rel="noopener">${e["rs"]}</a>`
    }
    if (f["name"] === "gene_info" && e["gene_info"] !== "-") {
        return e["gene_info"]
            .split("|")
            .map(og => `<a href="https://www.ncbi.nlm.nih.gov/gene/${og.split(":")[1]}/"
                           target="_blank" rel="noopener">${og}</a>`)
            .join("|");
    }
    if (f["name"] === "allele_id" && e["allele_id"] !== "NA") {
        return `<a href="https://www.ncbi.nlm.nih.gov/clinvar/variation/${e["allele_id"]}/"
                   target="_blank" rel="noopener">${e["allele_id"]}</a>`
    }
    return e[f["name"]] === null ? "NA" : e[f["name"]];
}

function updatePagination() {
    const totalPages = getTotalPages();
    d3.select("#current-page").text(page.toFixed(0));
    d3.select("#total-pages").text(totalPages);
    d3.select("#prev-page").attr("disabled", page === 1 ? "disabled" : null);
    d3.select("#next-page").attr("disabled", page.toString(10) === totalPages ? "disabled" : null);
}

function reloadPage() {
    let transitionEnded = false;
    if (itemsPerPage >= 100) d3.select("#table-display").classed("loading", true)
        .on("transitionend", () => transitionEnded = true);
    return fetch(new Request(`/api/?page=${page.toString(10)}&items_per_page=${itemsPerPage}`))
        .then(r => r.json())
        .then(data => {
            loadedEntries = data;
            if (!transitionEnded) {
                d3.select("#table-display").on("transitionend", () => {
                    populateEntryTable();
                    updatePagination();
                    d3.select("#table-display").classed("loading", false);
                });
            } else {
                populateEntryTable();
                updatePagination();
                d3.select("#table-display").classed("loading", false);
            }
        });
}

function getTotalPages() {
    return Math.ceil(totalCount / itemsPerPage).toFixed(0);
}

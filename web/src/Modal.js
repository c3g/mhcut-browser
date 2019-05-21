import * as d3 from "d3";

export default class {
    constructor(selector) {
        this.container = d3.select(selector);

        this.container.on("click", () => this.hide());
        this.container.select(".modal").on("click", () => d3.event.stopPropagation());
        this.container.select(".close-modal").on("click", () => this.hide());

        document.addEventListener("keyup", e => {
            if (e.key === "Escape" && this.container.classed("shown")) {
                this.hide();
            }
        });
    }

    show() {
        this.container.classed("shown", true);
    }

    hide() {
        this.container.classed("shown", false);
    }
}

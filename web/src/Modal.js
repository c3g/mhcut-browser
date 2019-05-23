import * as d3 from "d3";

export default class {
    constructor(selector) {
        this.container = d3.select(selector);
        this.listeners = {};

        this.container.on("click", () => this.hide());
        this.container.select(".modal").on("click", () => d3.event.stopPropagation());
        this.container.select(".close-modal").on("click", () => this.hide());

        document.addEventListener("keyup", e => {
            if (e.key === "Escape" && this.container.classed("shown")) {
                this.hide();
            }
        });
    }

    addListener(event, func) {
        if (!Object.keys(this.listeners).includes(event)) this.listeners[event] = [];
        this.listeners[event].push(func);
    }

    dispatch(event) {
        if (!Object.keys(this.listeners).includes(event)) return;
        this.listeners[event].forEach(f => f());
    }

    show() {
        this.container.classed("shown", true);
        this.dispatch("modalShow");
    }

    hide() {
        this.container.classed("shown", false);
        this.dispatch("modalHide");
    }
}

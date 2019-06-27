/*
    MHcut browser is a web application for browsing data from the MHcut tool.
    Copyright (C) 2018-2019  David Lougheed

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/


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

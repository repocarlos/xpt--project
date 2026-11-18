(function attachDashboardComponents(global) {
  function node(tag, text, className) {
    const item = document.createElement(tag);
    if (text !== undefined && text !== null) item.textContent = String(text);
    if (className) item.className = className;
    return item;
  }

  function qualityList(config) {
    const panel = node("dl", null, "quality-grid");
    const entries = [
      ["Source attribution", config.attribution || "Not supplied"],
      ["Study update time", config.updatedAt || "Not supplied"],
      ["Quote freshness", config.quoteFreshness || "Not assessed; no quote is loaded"],
      ["Coverage gaps", Array.isArray(config.coverageGaps)
        ? (config.coverageGaps.length ? config.coverageGaps.join("; ") : "No gaps reported")
        : "Not assessed"],
      ["Uncertainty bounds", config.uncertainty || "Not supplied"],
    ];

    for (const [label, value] of entries) {
      panel.append(node("dt", label));
      panel.append(node("dd", value));
    }

    const flagTerm = node("dt", "Data-quality flags");
    panel.append(flagTerm);
    const flagList = node("dd");
    if (!Array.isArray(config.flags)) {
      flagList.textContent = "Not assessed";
    } else if (config.flags.length === 0) {
      flagList.textContent = "No flags supplied";
    } else {
      const list = node("ul", null, "quality-flags");
      for (const flag of config.flags) {
        const isObject = flag !== null && typeof flag === "object";
        const label = isObject ? flag.label || flag.code || "Data-quality flag" : String(flag);
        const detail = isObject ? flag.detail || "" : "";
        const item = node("li", detail ? `${label}: ${detail}` : label, "quality-flag");
        if (isObject && flag.code) item.dataset.flagCode = flag.code;
        list.append(item);
      }
      flagList.append(list);
    }
    panel.append(flagList);
    return panel;
  }

  function dataTable(config) {
    const wrapper = node("div", null, "table-scroll visualization-table");
    if (!Array.isArray(config.columns) || !Array.isArray(config.rows) || config.rows.length === 0) {
      wrapper.append(node("p", config.tableEmptyMessage || "No datapoints supplied. Missing observations are unavailable, not zero."));
      return wrapper;
    }

    const table = node("table");
    const caption = node("caption", config.tableCaption || `${config.title} data table`);
    table.append(caption);
    const head = node("thead");
    const headRow = node("tr");
    config.columns.forEach((column) => headRow.append(node("th", column.label, undefined)));
    headRow.querySelectorAll("th").forEach((cell) => cell.scope = "col");
    head.append(headRow);
    table.append(head);

    const body = node("tbody");
    config.rows.forEach((row) => {
      const tableRow = node("tr");
      config.columns.forEach((column, index) => {
        const value = Array.isArray(row) ? row[index] : row[column.key];
        const cell = node(index === 0 ? "th" : "td", value === null || value === undefined || value === "" ? "Not reported" : value);
        if (index === 0) cell.scope = "row";
        tableRow.append(cell);
      });
      body.append(tableRow);
    });
    table.append(body);
    wrapper.append(table);
    return wrapper;
  }

  function renderVisualization(config) {
    const panel = node("div", null, "visualization-component");
    panel.append(node("h3", config.title));
    panel.append(node("p", config.description || "Study-specific visualization; its axes and measures are defined by this study."));

    const figure = node("figure", null, "chart-frame");
    const slot = node("div", null, "chart-area");
    if (config.chartNode instanceof Node) {
      if (!config.chartNode.getAttribute("aria-label") && config.chartDescription) {
        config.chartNode.setAttribute("aria-label", config.chartDescription);
      }
      slot.append(config.chartNode);
    } else {
      slot.setAttribute("role", "status");
      slot.textContent = config.chartEmptyMessage || "Chart unavailable until reviewed study data is supplied.";
    }
    figure.append(slot);
    figure.append(node("figcaption", config.caption || "Chart-specific visual; see the accessible data table below."));
    panel.append(figure);

    const qualityHeading = node("h4", "Data quality and provenance");
    panel.append(qualityHeading);
    panel.append(qualityList(config));
    panel.append(dataTable(config));
    return panel;
  }

  global.DashboardComponents = Object.freeze({ renderVisualization });
})(window);

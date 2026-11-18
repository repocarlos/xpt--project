const studies = {
  weather: {
    type: "weather_probability_comparison",
    title: "Daily temperature pilot",
    sector: "Weather",
    parentTitle: "Weather markets",
    parentHref: "#/sectors/weather",
    scope: "Pilot · selected daily temperature markets",
    question: "How do selected daily high-temperature market prices compare with forecast probabilities?",
    resolution: "Contract questions, station, settlement source, local date, and rule version will appear here after review.",
    analysis: "Market quotes and forecast vintages will be shown as separate series with their own timestamps.",
    chart: "Weather comparison chart unavailable",
    gap: "No authorized study dataset is loaded. No calibration result is claimed.",
    domainTitle: "Weather study module",
    domainDetail: "Weather market prices and forecast probabilities will be displayed as separate observations after source and study review.",
  },
  "cross-venue": {
    type: "cross_venue_discrepancy",
    title: "Polymarket–Kalshi comparison",
    sector: "Cross-cutting studies",
    parentTitle: "Cross-cutting studies",
    parentHref: "#/collections/research",
    scope: "Pilot · selected matched contracts",
    question: "Do reviewed equivalent contracts show synchronized price differences?",
    resolution: "Matched outcomes, payout rules, settlement sources, and rule versions will appear here after review.",
    analysis: "Each venue's bid, ask, midpoint basis, timestamp, and spread will be displayed separately.",
    chart: "Matched quote chart unavailable",
    gap: "No matched pairs or authorized quotes are loaded. A price difference is not a validated opportunity.",
    domainTitle: "Cross-venue study module",
    domainDetail: "Matched quotes, settlement equivalence, spread, and timestamp alignment will be shown together after the pair set is reviewed.",
  },
  options: {
    type: "prediction_market_options_surface",
    title: "Prediction-market options feasibility",
    sector: "Cross-cutting studies",
    parentTitle: "Cross-cutting studies",
    parentHref: "#/collections/research",
    scope: "Feasibility pilot · selected threshold and expiry",
    question: "Can a prediction-market threshold curve be compared with a matched listed-options benchmark?",
    resolution: "Underlying reference, threshold, expiry, and settlement convention will appear here after review.",
    analysis: "Risk-neutral quantities and Black–Scholes-equivalent volatility will be labeled as model-derived estimates.",
    chart: "Threshold and volatility comparison unavailable",
    gap: "No synchronized, licensed quotes are loaded. A model estimate is not a real-world event probability.",
    domainTitle: "Options study module",
    domainDetail: "Threshold bounds and any Black–Scholes-equivalent quantities will be labeled as model-derived and kept separate from listed option quotes.",
  },
};

const app = document.querySelector("#main");
const evidenceLabels = {
  descriptive: "Descriptive",
  model_estimate: "Model estimate",
  validated_forecast: "Validated forecast",
  validated_finding: "Validated finding",
  candidate_discrepancy: "Candidate discrepancy",
  executable_opportunity: "Executable opportunity",
};
const home = `
  <section class="hero" aria-labelledby="page-title">
    <p class="eyebrow">Research overview</p>
    <h1 id="page-title">Understand what prediction markets are pricing</h1>
    <p class="lede">Explore research by market sector, then open the studies that explain the evidence and its limits.</p>
    <p class="status-line"><strong>Current data:</strong> unavailable. Source-use review and data capture are pending.</p>
  </section>
  <section aria-labelledby="sectors-title">
    <h2 id="sectors-title">Sectors</h2>
    <div class="card-grid">
      <article class="study-card">
        <span class="scope-tag">Sector · pilot study available</span>
        <h2>Weather</h2>
        <p>Explore research on selected daily temperature markets and forecast comparisons.</p>
        <a class="button-link" href="#/sectors/weather">Open Weather sector</a>
      </article>
    </div>
  </section>
  <section aria-labelledby="collection-title">
    <h2 id="collection-title">Research across sectors</h2>
    <p>Some analyses compare venues or use another market as a benchmark. They are grouped separately from market sectors.</p>
    <a class="button-link" href="#/collections/research">Browse cross-cutting studies</a>
  </section>
  <section class="panel" aria-labelledby="interpret-title">
    <h2 id="interpret-title">How to read a study</h2>
    <p>Market observations, external estimates, validated findings, and candidate differences are separate evidence types. This shell contains no market observations.</p>
  </section>`;

function sectorIndexPage() {
  return `
    <p class="eyebrow"><a href="#/">Home</a> / Sectors</p>
    <section class="hero" aria-labelledby="page-title">
      <span class="scope-tag">Sector directory</span>
      <h1 id="page-title">Explore sectors</h1>
      <p class="lede">Browse the sectors with research available in this prototype. Each study covers only its stated sample.</p>
    </section>
    <div class="card-grid">
      <article class="study-card">
        <span class="scope-tag">Pilot · selected markets and dates</span>
        <h2>Weather</h2>
        <p>Weather contracts can depend on a named station, local date, measurement window, and exact bucket boundaries.</p>
        <a class="button-link" href="#/sectors/weather">Open Weather sector</a>
      </article>
    </div>`;
}

function researchCollectionPage() {
  const studyIds = ["cross-venue", "options"];
  return `
    <p class="eyebrow"><a href="#/">Home</a> / Research across sectors</p>
    <section class="hero" aria-labelledby="page-title">
      <span class="scope-tag">Cross-cutting research collection</span>
      <h1 id="page-title">Studies across sectors</h1>
      <p class="lede">These pilots compare venues or use another market as a benchmark. This collection is not a market sector.</p>
      <p class="status-line"><strong>Current data:</strong> unavailable while source-use review and data capture are pending.</p>
    </section>
    <div class="card-grid">
      ${studyIds.map((id) => {
        const study = studies[id];
        return `
          <article class="study-card">
            <span class="scope-tag">${study.scope}</span>
            <h2>${study.title}</h2>
            <p>${study.question}</p>
            <p class="status-line">Evidence: not evaluated in this shell</p>
            <a class="button-link" href="#/studies/${id}">Open study</a>
          </article>`;
      }).join("")}
    </div>`;
}

function sectorPage() {
  return `
    <p class="eyebrow"><a href="#/">Home</a> / Weather</p>
    <section class="hero" aria-labelledby="page-title">
      <span class="scope-tag">Sector overview</span>
      <h1 id="page-title">Weather markets</h1>
      <p class="lede">Weather contracts may depend on a named station, local date, measurement window, and precise bucket boundaries.</p>
      <p class="status-line"><strong>Data state:</strong> unavailable while source-use review is pending.</p>
    </section>
    <section class="panel" aria-labelledby="rules-title">
      <h2 id="rules-title">What weather contracts resolve on</h2>
      <p>Read the contract's exact resolution source and rule version. A nearby station or a general weather report is not automatically the settlement source.</p>
    </section>
    <section class="study-card" aria-labelledby="weather-study-title">
      <span class="scope-tag">Pilot · selected markets and dates</span>
      <h2 id="weather-study-title">Daily temperature pilot</h2>
      <p>${studies.weather.question}</p>
      <a class="button-link" href="#/studies/weather">Open the study</a>
    </section>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function optionalValue(value, fallback = "Not supplied") {
  return value === null || value === undefined || value === "" ? fallback : escapeHtml(value);
}

function renderStringList(items, emptyMessage) {
  if (!Array.isArray(items) || items.length === 0) return `<p>${escapeHtml(emptyMessage)}</p>`;
  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderMetrics(metrics) {
  if (!Array.isArray(metrics) || metrics.length === 0) {
    return `<p>No metrics are supplied. An absent metric is not a zero result.</p>`;
  }
  return `<div class="table-scroll"><table><thead><tr><th scope="col">Measure</th><th scope="col">Value</th><th scope="col">Definition</th></tr></thead><tbody>${metrics.map((metric) => `
    <tr><th scope="row">${optionalValue(metric.name)}</th><td>${optionalValue(metric.value, "Not reported")} ${optionalValue(metric.unit, "")}</td><td>${optionalValue(metric.definition)}</td></tr>`).join("")}</tbody></table></div>`;
}

function renderSourceList(sources) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return `<p>No source records are available. Source use remains unavailable until rights and provenance are reviewed.</p>`;
  }
  return `<ul>${sources.map((source) => {
    const name = escapeHtml(source.name || "Unnamed source");
    const uri = typeof source.uri === "string" && /^https:\/\//i.test(source.uri) ? source.uri : null;
    const label = uri ? `<a href="${escapeHtml(uri)}" rel="noreferrer">${name}</a>` : name;
    return `<li>${label} · Role: ${optionalValue(source.role)} · Accessed: ${optionalValue(source.accessed_at)} · Usage terms: ${optionalValue(source.usage_terms)}</li>`;
  }).join("")}</ul>`;
}

function studyRecordView(study) {
  return {
    study_type: study.type,
    title: study.title,
    research_question: study.question,
    example_notice: null,
    contract_scope: { description: study.resolution, markets: [] },
    data_coverage: {
      start: null,
      end: null,
      sample_count: null,
      coverage_summary: "No authorized dataset or coverage audit is loaded.",
      known_gaps: [study.gap],
    },
    method: { summary: study.analysis, benchmark: null, analysis_version: null, evaluation_split: null },
    findings: { summary: "No study finding is published from this unavailable input set.", metrics: [] },
    uncertainty: { summary: "Uncertainty has not been quantified for this prototype.", items: [] },
    limitations: [study.gap, "This page does not establish a trading opportunity."],
    evidence_status: null,
    updated_at: null,
    sources: [],
    reproducibility: {},
    domain: { title: study.domainTitle, detail: study.domainDetail, chart: study.chart },
  };
}

function studyPage(id) {
  const study = studies[id];
  if (!study) return `<section class="state-panel"><h1>Study not found</h1><p>This study route is not available in the prototype.</p><a href="#/">Return to the catalog</a></section>`;

  const record = studyRecordView(study);
  const markets = record.contract_scope.markets;
  const marketContent = markets.length
    ? `<p>${escapeHtml(record.contract_scope.description)}</p><ul>${markets.map((market) => {
      const permittedId = market.display_permission === "approved" ? ` · ID: ${optionalValue(market.market_id)}` : " · ID: withheld until display permission is confirmed";
      const effective = [market.valid_from, market.valid_to].some(Boolean)
        ? ` · Effective: ${optionalValue(market.valid_from)} to ${optionalValue(market.valid_to)}`
        : "";
      return `<li><strong>${optionalValue(market.venue)}:</strong> ${optionalValue(market.question)}${permittedId} · Resolution source: ${optionalValue(market.resolution_source)} · Rule: ${optionalValue(market.rule_version)} · Timezone: ${optionalValue(market.timezone)}${effective}</li>`;
    }).join("")}</ul>`
    : `<p>${escapeHtml(study.scope)}</p><p>${escapeHtml(record.contract_scope.description)}</p><p>Exact contract identity and settlement rule are not supplied in this prototype.</p>`;
  const marketDetails = record.data_coverage;
  const provenance = record.reproducibility;
  const provenanceEntries = [
    ["Schema version", provenance.schema_version],
    ["Repository", provenance.repository_uri],
    ["Analysis code", provenance.code_path],
    ["Code commit", provenance.code_commit],
    ["Data manifest", provenance.data_manifest_uri],
    ["Settlement rules", provenance.settlement_rules_uri],
  ].filter(([, value]) => value !== null && value !== undefined && value !== "");

  return `
    <p class="eyebrow"><a href="#/">Home</a> / <a href="${study.parentHref}">${escapeHtml(study.parentTitle)}</a> / ${escapeHtml(record.title)}</p>
    <section class="hero" aria-labelledby="page-title" data-study-section="summary">
      <span class="scope-tag">${escapeHtml(study.scope)} · ${escapeHtml(study.type)}</span>
      <h1 id="page-title">${escapeHtml(record.title)}</h1>
      <span class="evidence-tag">Evidence: ${escapeHtml(evidenceLabels[record.evidence_status] || "not evaluated")}</span>
      <p class="lede">${escapeHtml(record.research_question)}</p>
      ${record.example_notice ? `<p class="status-line">${escapeHtml(record.example_notice)}</p>` : ""}
    </section>
    <section class="state-panel" role="status" aria-label="Data availability">
      <h2>Study data unavailable</h2>
      <p>No market observations or derived values are loaded. Source rights, study inputs, and update times need review.</p>
    </section>
    <section class="panel" aria-labelledby="resolve-title" data-study-section="contract-scope">
      <h2 id="resolve-title">Contract scope and settlement</h2>
      ${marketContent}
    </section>
    <section class="panel" aria-labelledby="price-title" data-study-section="market-pricing">
      <h2 id="price-title">What is the market pricing?</h2>
      <p>No quote is available. Observed bid, ask, or midpoint values will be labeled separately from model estimates and will include their basis and timestamp.</p>
    </section>
    <section class="panel" aria-labelledby="coverage-title" data-study-section="data-coverage">
      <h2 id="coverage-title">Data period and coverage</h2>
      <dl class="data-list">
        <dt>Period start</dt><dd>${optionalValue(marketDetails.start)}</dd>
        <dt>Period end</dt><dd>${optionalValue(marketDetails.end)}</dd>
        <dt>Sample count</dt><dd>${optionalValue(marketDetails.sample_count, "Not reported")}</dd>
        <dt>Coverage summary</dt><dd>${escapeHtml(marketDetails.coverage_summary)}</dd>
      </dl>
      <h3>Known gaps</h3>
      ${renderStringList(marketDetails.known_gaps, "No coverage gaps have been reviewed.")}
    </section>
    <section class="panel" aria-labelledby="method-title" data-study-section="method">
      <h2 id="method-title">Method and benchmark</h2>
      <p>${escapeHtml(record.method.summary)}</p>
      <p>Benchmark: ${optionalValue(record.method.benchmark, "Not specified")}</p>
      <p>Analysis version: ${optionalValue(record.method.analysis_version)}</p>
      <p>Evaluation split: ${optionalValue(record.method.evaluation_split, "Not reported; no held-out validation is claimed")}</p>
    </section>
    <section class="panel" aria-labelledby="domain-title" data-study-section="domain">
      <h2 id="domain-title">${escapeHtml(record.domain.title)}</h2>
      <p>${escapeHtml(record.domain.detail)}</p>
      <div data-visualization-slot="${escapeHtml(id)}"></div>
    </section>
    <section class="panel" aria-labelledby="findings-title" data-study-section="findings">
      <h2 id="findings-title">Findings and measures</h2>
      <p>${escapeHtml(record.findings.summary)}</p>
      ${renderMetrics(record.findings.metrics)}
    </section>
    <section class="panel" aria-labelledby="uncertainty-title" data-study-section="uncertainty">
      <h2 id="uncertainty-title">Uncertainty</h2>
      <p>${escapeHtml(record.uncertainty.summary)}</p>
      ${renderStringList(record.uncertainty.items, "No itemized uncertainty is supplied.")}
    </section>
    <section class="panel" aria-labelledby="limits-title" data-study-section="limitations">
      <h2 id="limits-title">Limitations</h2>
      ${renderStringList(record.limitations, "No limitations have been supplied.")}
    </section>
    <section class="panel" aria-labelledby="freshness-title" data-study-section="freshness">
      <h2 id="freshness-title">Update time and freshness</h2>
      <p>Study updated: ${optionalValue(record.updated_at)}. Market quote time: not available.</p>
    </section>
    <section class="panel" aria-labelledby="sources-title" data-study-section="provenance">
      <h2 id="sources-title">Sources and reproducibility</h2>
      <h3>Sources</h3>
      ${renderSourceList(record.sources)}
      <h3>Reproducibility references</h3>
      ${provenanceEntries.length ? `<dl class="data-list">${provenanceEntries.map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${optionalValue(value)}</dd>`).join("")}</dl>` : `<p>No code revision, data manifest, or settlement-rule record is linked.</p>`}
    </section>`;
}

function unavailableRoute(title, description) {
  return `<section class="state-panel"><h1>${title}</h1><p>${description}</p><a href="#/">Return to the catalog</a></section>`;
}

function mountStudyVisualizations() {
  for (const slot of app.querySelectorAll("[data-visualization-slot]")) {
    const study = studies[slot.dataset.visualizationSlot];
    if (!study || !window.DashboardComponents) continue;
    const component = window.DashboardComponents.renderVisualization({
      title: study.chart,
      description: study.domainDetail,
      chartDescription: `${study.chart}; no data loaded`,
      chartEmptyMessage: "Chart unavailable until approved study data is supplied.",
      tableEmptyMessage: "No datapoints supplied. Missing observations are unavailable, not zero.",
      caption: "Study-specific chart; axes and measures depend on this domain's method.",
      columns: [],
      rows: [],
      attribution: null,
      updatedAt: null,
      quoteFreshness: null,
      coverageGaps: [study.gap],
      uncertainty: "Not quantified until the reviewed study inputs are available.",
      flags: null,
    });
    slot.replaceWith(component);
  }
}

function render() {
  const route = window.location.hash || "#/";
  if (route === "#/") app.innerHTML = home;
  else if (route === "#/sectors") app.innerHTML = sectorIndexPage();
  else if (route === "#/sectors/weather") app.innerHTML = sectorPage();
  else if (route.startsWith("#/sectors/")) app.innerHTML = unavailableRoute("Sector not available", "This sector has no reviewed content in the prototype.");
  else if (route === "#/collections/research") app.innerHTML = researchCollectionPage();
  else if (route.startsWith("#/collections/")) app.innerHTML = unavailableRoute("Collection not available", "This research collection is not part of the prototype.");
  else if (route.startsWith("#/studies/")) app.innerHTML = studyPage(route.slice("#/studies/".length));
  else app.innerHTML = unavailableRoute("Page not found", "That route is not available in this prototype.");

  mountStudyVisualizations();

  for (const link of document.querySelectorAll(".site-header nav a")) {
    if (link.getAttribute("href") === route) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

window.addEventListener("hashchange", render);
render();

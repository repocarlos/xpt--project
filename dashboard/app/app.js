const studies = {
  weather: {
    title: "Daily temperature pilot",
    sector: "Weather",
    scope: "Pilot · selected daily temperature markets",
    question: "How do selected daily high-temperature market prices compare with forecast probabilities?",
    resolution: "Contract questions, station, settlement source, local date, and rule version will appear here after review.",
    analysis: "Market quotes and forecast vintages will be shown as separate series with their own timestamps.",
    chart: "Weather comparison chart unavailable",
    gap: "No authorized study dataset is loaded. No calibration result is claimed.",
  },
  "cross-venue": {
    title: "Polymarket–Kalshi comparison",
    sector: "Cross-cutting study",
    scope: "Pilot · selected matched contracts",
    question: "Do reviewed equivalent contracts show synchronized price differences?",
    resolution: "Matched outcomes, payout rules, settlement sources, and rule versions will appear here after review.",
    analysis: "Each venue's bid, ask, midpoint basis, timestamp, and spread will be displayed separately.",
    chart: "Matched quote chart unavailable",
    gap: "No matched pairs or authorized quotes are loaded. A price difference is not a validated opportunity.",
  },
  options: {
    title: "Prediction-market options feasibility",
    sector: "Options study",
    scope: "Feasibility pilot · selected threshold and expiry",
    question: "Can a prediction-market threshold curve be compared with a matched listed-options benchmark?",
    resolution: "Underlying reference, threshold, expiry, and settlement convention will appear here after review.",
    analysis: "Risk-neutral quantities and Black–Scholes-equivalent volatility will be labeled as model-derived estimates.",
    chart: "Threshold and volatility comparison unavailable",
    gap: "No synchronized, licensed quotes are loaded. A model estimate is not a real-world event probability.",
  },
};

const app = document.querySelector("#main");
const home = `
  <section class="hero" aria-labelledby="page-title">
    <p class="eyebrow">Research overview</p>
    <h1 id="page-title">Understand what prediction markets are pricing</h1>
    <p class="lede">This prototype will explain contract rules, market-implied values, comparison evidence, and study limitations in one place.</p>
    <p class="status-line"><strong>Current data:</strong> unavailable. Source-use review and data capture are pending.</p>
  </section>
  <section aria-labelledby="studies-title">
    <h2 id="studies-title">Research pilots</h2>
    <div class="card-grid">
      ${Object.entries(studies).map(([id, study]) => `
        <article class="study-card">
          <span class="scope-tag">${study.scope}</span>
          <h2>${study.title}</h2>
          <p>${study.question}</p>
          <p class="status-line">Evidence: not evaluated in this shell</p>
          <a class="button-link" href="#/studies/${id}">Open study</a>
        </article>`).join("")}
    </div>
  </section>
  <section class="panel" aria-labelledby="interpret-title">
    <h2 id="interpret-title">How to read a study</h2>
    <p>Market observations, external estimates, validated findings, and candidate differences are separate evidence types. This shell contains no market observations.</p>
  </section>`;

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

function studyPage(id) {
  const study = studies[id];
  if (!study) return `<section class="state-panel"><h1>Study not found</h1><p>This route is not part of the prototype.</p><a href="#/">Return home</a></section>`;
  return `
    <p class="eyebrow"><a href="#/">Home</a> / ${study.sector}</p>
    <section class="hero" aria-labelledby="page-title">
      <span class="scope-tag">${study.scope}</span>
      <h1 id="page-title">${study.title}</h1>
      <span class="evidence-tag">Evidence: not evaluated</span>
      <p class="lede">${study.question}</p>
      <p class="status-line">Study updated: not available · Market quote time: not available</p>
    </section>
    <section class="state-panel" role="status" aria-label="Data availability">
      <h2>Study data unavailable</h2>
      <p>No market observations or derived values are loaded in this prototype. Source rights, study inputs, and update times need review.</p>
    </section>
    <div class="panel-grid">
      <section class="panel" aria-labelledby="resolve-title">
        <h2 id="resolve-title">What does the contract resolve on?</h2>
        <p>${study.resolution}</p>
      </section>
      <section class="panel" aria-labelledby="price-title">
        <h2 id="price-title">What is the market pricing?</h2>
        <p>No quote is available. A later view must show quote side, implied-price basis, spread, and timestamp together.</p>
      </section>
      <section class="panel" aria-labelledby="estimate-title">
        <h2 id="estimate-title">What is the comparison evidence?</h2>
        <p>${study.analysis}</p>
      </section>
      <section class="panel" aria-labelledby="chart-title">
        <h2 id="chart-title">${study.chart}</h2>
        <p>No chart points are shown without an approved dataset.</p>
      </section>
    </div>
    <section class="panel" aria-labelledby="limits-title">
      <h2 id="limits-title">Limitations and uncertainty</h2>
      <p>${study.gap}</p>
      <p>Nothing on this page establishes a trading opportunity.</p>
    </section>
    <section class="panel" aria-labelledby="sources-title">
      <h2 id="sources-title">Sources and reproducibility</h2>
      <p>No source links or data manifest are published in this prototype. They will appear only after source rights and provenance are confirmed.</p>
    </section>`;
}

function render() {
  const route = window.location.hash || "#/";
  if (route === "#/") app.innerHTML = home;
  else if (route === "#/sectors/weather") app.innerHTML = sectorPage();
  else if (route.startsWith("#/studies/")) app.innerHTML = studyPage(route.slice("#/studies/".length));
  else app.innerHTML = `<section class="state-panel"><h1>Page not found</h1><p>That route is not available in this prototype.</p><a href="#/">Return to the study overview</a></section>`;

  for (const link of document.querySelectorAll(".site-header nav a")) {
    if (link.getAttribute("href") === route) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

window.addEventListener("hashchange", render);
render();

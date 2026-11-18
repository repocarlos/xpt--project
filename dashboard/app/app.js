const studies = {
  weather: {
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
  },
  "cross-venue": {
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
  },
  options: {
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
  },
};

const app = document.querySelector("#main");
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

function studyPage(id) {
  const study = studies[id];
  if (!study) return `<section class="state-panel"><h1>Study not found</h1><p>This study route is not available in the prototype.</p><a href="#/">Return to the catalog</a></section>`;
  return `
    <p class="eyebrow"><a href="#/">Home</a> / <a href="${study.parentHref}">${study.parentTitle}</a> / ${study.title}</p>
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

function unavailableRoute(title, description) {
  return `<section class="state-panel"><h1>${title}</h1><p>${description}</p><a href="#/">Return to the catalog</a></section>`;
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

  for (const link of document.querySelectorAll(".site-header nav a")) {
    if (link.getAttribute("href") === route) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

window.addEventListener("hashchange", render);
render();

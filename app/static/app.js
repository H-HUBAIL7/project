const nav = document.getElementById("nav");
const stage = document.getElementById("stage");
const root = document.documentElement;

let cat = { pages: [], options: {} };
const state = {};
let sort = {};

const PILL = {
  active: "", registered: "", completed: "mute", graduated: "mute",
  retired: "mute", inactive: "mute", proposed: "warn", suspended: "warn",
  withdrawn: "stop",
};

const saved = localStorage.getItem("theme");
root.dataset.theme =
  saved || (matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark" : "light");

document.getElementById("theme").onclick = () => {
  root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", root.dataset.theme);
};

const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

function pill(value) {
  const node = el("span", `pill ${PILL[value] ?? "mute"}`, value);
  return node;
}

function buildNav() {
  nav.replaceChildren();
  [...new Set(cat.pages.map((p) => p.section))].forEach((section) => {
    nav.append(el("div", "section", section));
    cat.pages
      .filter((p) => p.section === section)
      .forEach((p) => {
        const node = el("a", "item", p.label);
        node.href = `#${p.id}`;
        node.dataset.id = p.id;
        nav.append(node);
      });
  });
}

function markNav(id) {
  nav.querySelectorAll(".item").forEach((node) => {
    node.classList.toggle("on", node.dataset.id === id);
  });
}

/* ------------------------------------------------------------ list view */

function filters(page) {
  const bar = el("form", "filters");
  bar.onsubmit = (event) => {
    event.preventDefault();
    load(page);
  };
  const values = state[page.id] || (state[page.id] = {});

  page.filters.forEach((spec) => {
    if (values[spec.name] === undefined) {
      values[spec.name] = spec.default || "";
    }
    const wrap = el("div", "field");
    wrap.append(el("label", null, spec.label));

    let input;
    if (spec.kind === "select") {
      input = el("select");
      const any = el("option", null, "Any");
      any.value = "";
      input.append(any);
      (cat.options[spec.source] || []).forEach((entry) => {
        const [value, text] = Array.isArray(entry) ? entry : [entry, entry];
        const option = el("option", null, text);
        option.value = value;
        input.append(option);
      });
      input.value = values[spec.name];
      input.onchange = () => {
        values[spec.name] = input.value;
      };
    } else {
      input = el("input");
      input.type = spec.kind === "number" ? "number" : "text";
      input.placeholder = spec.placeholder || "";
      input.value = values[spec.name];
      input.oninput = () => {
        values[spec.name] = input.value;
      };
    }
    wrap.append(input);
    bar.append(wrap);
  });

  const go = el("button", "go", "Search");
  go.type = "submit";

  const reset = el("button", "clear", "Reset");
  reset.type = "button";
  reset.onclick = () => {
    delete state[page.id];
    render();
  };
  bar.append(go, reset);
  return bar;
}

function table(page, rows) {
  if (!rows.length) return el("div", "empty", "No matching records");

  const order = sort[page.id];
  let data = rows;
  if (order) {
    data = [...rows].sort((a, b) => {
      const x = a[order.column];
      const y = b[order.column];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      const result = typeof x === "number" && typeof y === "number"
        ? x - y
        : String(x).localeCompare(String(y), "en-GB", { numeric: true });
      return order.desc ? -result : result;
    });
  }

  const node = el("table");
  const head = node.createTHead().insertRow();
  page.columns.forEach((column) => {
    const cell = el("th", null, column === "id" ? "ID" : column);
    if (order && order.column === column) cell.classList.add("sorted");
    cell.append(el("span", "arrow", order && order.desc ? "\u2193" : "\u2191"));
    cell.onclick = () => {
      sort[page.id] = {
        column,
        desc: order && order.column === column ? !order.desc : false,
      };
      render();
    };
    head.append(cell);
  });

  const body = node.createTBody();
  data.forEach((row) => {
    const line = body.insertRow();
    if (page.detail && row.id !== undefined) {
      line.classList.add("clickable");
      line.onclick = () => {
        location.hash = `${page.id}/${encodeURIComponent(row.id)}`;
      };
    }
    page.columns.forEach((column, index) => {
      const cell = line.insertCell();
      const value = row[column];

      if (column === "id") {
        cell.append(el("span", "key", value ?? "\u2014"));
        return;
      }
      cell.textContent =
        value === null || value === undefined || value === ""
          ? "\u2014"
          : value;
    });
    if (row.status) line.insertCell().append(pill(row.status));
  });

  if (data.some((row) => row.status)) {
    const cell = el("th", null, "Status");
    cell.onclick = () => {
      sort[page.id] = {
        column: "status",
        desc: order && order.column === "status" ? !order.desc : false,
      };
      render();
    };
    if (order && order.column === "status") cell.classList.add("sorted");
    head.append(cell);
  }

  return node;
}

async function load(page) {
  const values = state[page.id] || {};
  const query = new URLSearchParams(
    Object.entries(values).filter(([, value]) => value !== "")
  );
  const panel = document.getElementById("panel");
  const tally = document.getElementById("tally");
  try {
    const response = await fetch(`/api/page/${page.id}?${query}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    tally.textContent = `${data.count.toLocaleString("en-GB")} ${
      data.count === 1 ? "result" : "results"
    }`;
    panel.replaceChildren(table(page, data.rows));
  } catch (error) {
    tally.textContent = "";
    panel.replaceChildren(el("div", "empty error", String(error.message)));
  }
}

function listView(page) {
  markNav(page.id);
  const head = el("div", "head");
  head.append(el("h1", null, page.label));
  const tally = el("div", "tally");
  tally.id = "tally";
  head.append(tally);

  const panel = el("div", "panel");
  panel.id = "panel";
  panel.append(el("div", "empty", "Loading"));

  stage.replaceChildren(head, filters(page), panel);
  load(page);
}

/* ---------------------------------------------------------- detail view */

function renderPanel(panel) {
  if (panel.kind === "stack") {
    const wrap = document.createDocumentFragment();
    panel.blocks.forEach((block) => {
      const section = el("div", "block");
      section.append(el("h2", null, block.heading));
      section.append(renderPanel(block.body));
      wrap.append(section);
    });
    return wrap;
  }

  const card = el("div", "card");
  if (panel.kind === "fields") {
    const grid = el("dl", "fields");
    panel.items
      .filter((item) => item.value !== null && item.value !== "")
      .forEach((item) => {
        const pair = el("div", "pair");
        pair.append(el("dt", null, item.label));
        pair.append(el("dd", null, String(item.value)));
        grid.append(pair);
      });
    card.append(grid);
    return card;
  }

  if (!panel.rows.length) {
    card.append(el("div", "empty", "Nothing recorded"));
    return card;
  }

  const scroll = el("div", "scroll");
  const node = el("table");
  const head = node.createTHead().insertRow();
  panel.columns.forEach((column) => head.append(el("th", null, column)));
  const body = node.createTBody();
  panel.rows.forEach((row) => {
    const line = body.insertRow();
    panel.columns.forEach((column) => {
      const value = row[column];
      line.insertCell().textContent =
        value === null || value === undefined || value === ""
          ? "\u2014"
          : value;
    });
  });
  scroll.append(node);
  card.append(scroll);
  return card;
}

function detailView(page, record) {
  markNav(page.id);

  const back = el("div", "back", `\u2190 ${page.label}`);
  back.onclick = () => {
    location.hash = page.id;
  };

  const hero = el("div", "hero");
  const titles = el("div");
  const line = el("div");
  line.style.display = "flex";
  line.style.alignItems = "center";
  line.style.gap = "10px";
  line.append(el("h1", null, record.title));
  if (record.status) line.append(pill(record.status));
  titles.append(line);
  if (record.subtitle) titles.append(el("div", "sub", record.subtitle));
  hero.append(titles);

  const wrap = el("div", "detail");
  wrap.append(hero);

  if (record.stats && record.stats.length) {
    const strip = el("div", "stats");
    record.stats.forEach((stat) => {
      const card = el("div", "stat");
      card.append(el("b", null, String(stat.value ?? "\u2014")));
      card.append(el("span", null, stat.label));
      strip.append(card);
    });
    wrap.append(strip);
  }

  const tabs = el("div", "tabs");
  const body = el("div", "body");

  const show = (tab) => {
    tabs.querySelectorAll(".tab").forEach((node) => {
      node.classList.toggle("on", node.dataset.id === tab.id);
    });
    body.replaceChildren(renderPanel(tab.panel));
  };

  record.tabs.forEach((tab, index) => {
    const node = el("div", "tab", tab.label);
    node.dataset.id = tab.id;
    if (tab.count) node.append(el("span", "count", String(tab.count)));
    node.onclick = () => show(tab);
    tabs.append(node);
    if (index === 0) setTimeout(() => show(tab), 0);
  });

  wrap.append(tabs, body);
  stage.replaceChildren(back, wrap);
}

/* -------------------------------------------------------------- routing */

async function render() {
  const [pageId, key] = decodeURIComponent(
    location.hash.replace(/^#/, "")
  ).split("/");
  const page = cat.pages.find((p) => p.id === pageId) || cat.pages[0];
  if (!page) return;

  if (!key) {
    listView(page);
    return;
  }

  stage.replaceChildren(el("div", "empty", "Loading"));
  try {
    const response = await fetch(
      `/api/record/${page.detail}/${encodeURIComponent(key)}`
    );
    const record = await response.json();
    if (!response.ok) throw new Error(record.detail || "Not found");
    detailView(page, record);
  } catch (error) {
    stage.replaceChildren(el("div", "empty error", String(error.message)));
  }
}

addEventListener("hashchange", render);

(async () => {
  try {
    cat = await (await fetch("/api/catalogue")).json();
    document.getElementById("brand").textContent = cat.university;
    document.title = `${cat.university} Records`;
    buildNav();
    if (!location.hash) location.hash = cat.pages[0].id;
    render();
  } catch (error) {
    stage.replaceChildren(
      el("div", "empty error", "Cannot reach the database")
    );
  }
})();

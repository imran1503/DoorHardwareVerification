import React, { useEffect, useMemo, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMoon, faSun } from "@fortawesome/free-solid-svg-icons";
import {
  ArrowUpRight,
  BookOpenText,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  FilePlus2,
  Layers3,
  Library,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import "./styles.css";

const emptyProduct = {
  category: "automatic_operator",
  manufacturer: "",
  model: "",
  name: "",
  specifications: "{}",
  source_title: "",
  source_url: "",
  evidence_status: "research_lead",
  notes: "",
};
const emptyRule = {
  name: "",
  category_a: "automatic_operator",
  category_b: "activation_device",
  spec_a: "",
  comparison: "equals",
  spec_b: "",
  pass_outcome: "compatible",
  fail_outcome: "incompatible",
  rationale: "",
  source_title: "",
  source_url: "",
  evidence_status: "research_lead",
};
const emptyAssertion = {
  product_ids: [],
  outcome: "compatible",
  conditions: "{}",
  rationale: "",
  source_title: "",
  source_url: "",
  evidence_status: "research_lead",
};
const emptyOpening = {
  door_material: "",
  frame_material: "",
  configuration: "",
  handing: "",
  swing_direction: "",
  location: "",
  fire_rated: "",
  width_in: "",
  height_in: "",
  weight_lb: "",
  reveal_depth_mm: "",
};
const exampleScenarios = [
  {
    id: "wc16-strike",
    title: "Restroom kit + electric strike",
    description:
      "Manufacturer-documented CX-WC16-PS-M1 and CX-ED1799L-8 pairing.",
    expected: "Documented compatible",
    kind: "compatible",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC16-PS-M1"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
    ],
  },
  {
    id: "wc17-controller",
    title: "Restroom kit + controller",
    description: "CX-WC17SLVR paired with its documented CX-33 controller.",
    expected: "Documented compatible",
    kind: "compatible",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC17SLVR"],
      ["controller", "Camden Controls", "CX-33"],
    ],
  },
  {
    id: "call-annunciator",
    title: "Emergency call + annunciator",
    description:
      "CX-WEC10-K2 paired with the CM-AF141SO annunciator shown in its wiring documentation.",
    expected: "Documented compatible",
    kind: "compatible",
    products: [
      ["emergency_call", "Camden Controls", "CX-WEC10-K2"],
      ["alarm", "Camden Controls", "CM-AF141SO"],
    ],
  },
  {
    id: "operator-strike-unverified",
    title: "Operator + strike · unverified demo",
    description:
      "Shows how the checker reports a missing exact interface match. This is a test case, not an approval.",
    expected: "Test only · expected unverified",
    kind: "unverified",
    products: [
      ["automatic_operator", "LCN", "9540"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
    ],
  },
  {
    id: "operator-opening-limit",
    title: "Opening width limit · fit demo",
    description:
      "LCN 9540 with a 52 in opening, above its documented 48 in maximum. Intended to show a fit conflict.",
    expected: "Test only · expected incompatible",
    kind: "unverified",
    products: [["automatic_operator", "LCN", "9540"]],
    opening: { configuration: "single", width_in: "52", weight_lb: "300" },
  },
];
const hardwareGroups = [
  { label: "Door & frame", categories: ["door", "frame"] },
  { label: "Hinges & closers", categories: ["hinge", "closer"] },
  {
    label: "Locks & exit hardware",
    categories: [
      "mechanical_lock",
      "electric_lock",
      "electric_strike",
      "exit_device",
      "flush_bolt",
    ],
  },
  {
    label: "Operators & activation",
    categories: ["automatic_operator", "activation_device", "safety_sensor"],
  },
  {
    label: "Controls, power & washroom",
    categories: [
      "controller",
      "access_control",
      "power_supply",
      "request_to_exit",
      "emergency_release",
      "emergency_call",
      "door_contact",
      "alarm",
      "washroom_control",
    ],
  },
  {
    label: "Other door hardware",
    categories: ["door_seal", "threshold", "coordinator", "door_stop", "other"],
  },
];

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("The local database server could not be reached.");
  }
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Request failed.");
  return body;
}

function displayName(product) {
  return [product.manufacturer, product.model || product.name]
    .filter(Boolean)
    .join(" ");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"' && quoted && text[i + 1] === '"') {
      cell += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") i += 1;
      row.push(cell);
      if (row.some((value) => value.trim())) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  row.push(cell);
  if (row.some((value) => value.trim())) rows.push(row);
  if (rows.length < 2) return [];
  const headers = rows[0].map((header) => header.trim());
  return rows
    .slice(1)
    .map((values) =>
      Object.fromEntries(
        headers.map((header, index) => [header, values[index] || ""]),
      ),
    );
}

function StatusPill({ status }) {
  return (
    <span className={`status-pill status-${status}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

export default function ModelApp() {
  const [data, setData] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [page, setPage] = useState("check");
  const [databaseState, setDatabaseState] = useState("connecting");
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [themeMode, setThemeMode] = useState(() => {
    const saved = window.localStorage.getItem("door-hardware-theme");
    return ["auto", "light", "dark"].includes(saved) ? saved : "auto";
  });
  const [localTime, setLocalTime] = useState(() => new Date());
  const [productForm, setProductForm] = useState(null);
  const [ruleForm, setRuleForm] = useState(null);
  const [assertionForm, setAssertionForm] = useState(null);
  const [showProduct, setShowProduct] = useState(false);
  const [showRule, setShowRule] = useState(false);
  const [showAssertion, setShowAssertion] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [opening, setOpening] = useState(emptyOpening);
  const [openingPreview, setOpeningPreview] = useState(null);
  const [checkResult, setCheckResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const [importing, setImporting] = useState(false);
  const importInput = useRef(null);
  const evidenceImportInput = useRef(null);

  const isNight = localTime.getHours() >= 18 || localTime.getHours() < 6;
  const activeTheme =
    themeMode === "auto" ? (isNight ? "dark" : "light") : themeMode;
  const nextTheme = isNight ? "Light" : "Dark";
  const nextThemeTime = isNight ? "6 AM" : "6 PM";
  const themeLabel =
    themeMode === "auto"
      ? `Automatic theme; switches to ${nextTheme.toLowerCase()} at ${nextThemeTime} local time.`
      : `${activeTheme} theme; click to resume automatic mode.`;

  const loadData = async () => {
    const next = await api("/api/bootstrap");
    setData({
      ...next,
      products: next.products || [],
      assertions: next.assertions || [],
      compatibilityRules: next.compatibilityRules || [],
    });
    setDatabaseState((state) => (state === "saving" ? "saving" : "connected"));
  };
  const loadCoverage = async () => {
    const result = await api("/api/coverage");
    setCoverage(result);
  };

  useEffect(() => {
    loadData().catch((error) => {
      setDatabaseState("offline");
      setNotice(error.message);
    });
    const interval = window.setInterval(async () => {
      try {
        await api("/api/health");
        setDatabaseState((state) =>
          state === "saving" ? "saving" : "connected",
        );
      } catch {
        setDatabaseState("offline");
      }
    }, 15000);
    const clockInterval = window.setInterval(
      () => setLocalTime(new Date()),
      60000,
    );
    return () => {
      window.clearInterval(interval);
      window.clearInterval(clockInterval);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = activeTheme;
    window.localStorage.setItem("door-hardware-theme", themeMode);
  }, [activeTheme, themeMode]);

  useEffect(() => {
    if (page === "coverage")
      loadCoverage().catch((error) => setNotice(error.message));
  }, [page, data?.products?.length]);

  const categories = data?.productCategories || {};
  const productList = data?.products || [];
  const activeProducts = productList.filter((product) => product.active);
  const visibleProducts = useMemo(
    () =>
      activeProducts.filter((product) =>
        `${displayName(product)} ${product.name} ${categories[product.category] || product.category}`
          .toLowerCase()
          .includes(search.toLowerCase()),
      ),
    [productList, search, categories],
  );
  const selectedProducts = selectedIds
    .map((id) => activeProducts.find((product) => product.id === Number(id)))
    .filter(Boolean);
  const openingContext = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(opening)
          .filter(([, value]) => value !== "")
          .map(([key, value]) => [
            key,
            ["width_in", "height_in", "weight_lb", "reveal_depth_mm"].includes(
              key,
            )
              ? Number(value)
              : value,
          ]),
      ),
    [opening],
  );
  const hasOpeningDetails = Object.keys(openingContext).length > 0;

  useEffect(() => {
    if (!hasOpeningDetails) {
      setOpeningPreview(null);
      return undefined;
    }
    let current = true;
    const timer = window.setTimeout(async () => {
      setOpeningPreview({
        status: "unverified",
        message: "Checking opening details…",
        findings: [],
      });
      try {
        const result = await api("/api/opening-fit", {
          method: "POST",
          body: JSON.stringify({
            product_ids: selectedIds,
            opening: openingContext,
          }),
        });
        if (current) setOpeningPreview(result);
      } catch (error) {
        if (current)
          setOpeningPreview({
            status: "unverified",
            message: error.message,
            findings: [],
          });
      }
    }, 250);
    return () => {
      current = false;
      window.clearTimeout(timer);
    };
  }, [hasOpeningDetails, openingContext, selectedIds]);

  const markSaving = () => setDatabaseState("saving");
  const markSaved = async () => {
    await loadData();
    if (page === "coverage") await loadCoverage();
    setDatabaseState("connected");
  };
  const saveProduct = async (event) => {
    event.preventDefault();
    markSaving();
    try {
      const payload = {
        ...productForm,
        specifications: JSON.parse(productForm.specifications || "{}"),
      };
      await api(
        productForm.id ? `/api/products/${productForm.id}` : "/api/products",
        {
          method: productForm.id ? "PUT" : "POST",
          body: JSON.stringify(payload),
        },
      );
      setShowProduct(false);
      setProductForm(null);
      await markSaved();
      setNotice("Product saved.");
    } catch (error) {
      setDatabaseState("connected");
      setNotice(
        error.message === "Unexpected end of JSON input"
          ? "Specifications must be valid JSON."
          : error.message,
      );
    }
  };
  const removeProduct = async (product) => {
    if (
      !window.confirm(
        `Archive ${displayName(product)}? It will remain in existing assertions but leave future checks.`,
      )
    )
      return;
    markSaving();
    try {
      await api(`/api/products/${product.id}`, { method: "DELETE" });
      await markSaved();
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    }
  };
  const importProducts = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setImporting(true);
    markSaving();
    try {
      const rows = parseCsv(await file.text()).map((row) => ({
        ...row,
        specifications: row.specifications
          ? JSON.parse(row.specifications)
          : {},
        evidence_status: row.evidence_status || "research_lead",
      }));
      const result = await api("/api/products/import", {
        method: "POST",
        body: JSON.stringify({ products: rows }),
      });
      await markSaved();
      setNotice(
        `Import complete: ${result.created} added, ${result.updated} updated${result.errors.length ? `, ${result.errors.length} needs attention` : ""}.`,
      );
      if (result.errors.length)
        console.warn("Product import row errors", result.errors);
    } catch (error) {
      setDatabaseState("connected");
      setNotice(`Import failed: ${error.message}`);
    } finally {
      setImporting(false);
      event.target.value = "";
    }
  };
  const downloadTemplate = () => {
    const csv =
      'category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes\nautomatic_operator,Example manufacturer,OP-100,Example operator,"{""operator_class"":""low_energy""}",Manufacturer data sheet,https://example.com/review-before-use,research_lead,Replace example values with sourced product data\n';
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "door-hardware-products-template.csv";
    link.click();
    URL.revokeObjectURL(url);
  };
  const importEvidenceBundle = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setImporting(true);
    markSaving();
    try {
      const bundle = JSON.parse(await file.text());
      const result = await api("/api/evidence/import", {
        method: "POST",
        body: JSON.stringify(bundle),
      });
      await markSaved();
      const created = Object.values(result.created || {}).reduce(
        (sum, count) => sum + count,
        0,
      );
      const updated = Object.values(result.updated || {}).reduce(
        (sum, count) => sum + count,
        0,
      );
      const errors = result.errors || [];
      const detail = errors.length
        ? ` ${errors.length} row${errors.length === 1 ? "" : "s"} need attention; first: ${errors[0].section} row ${errors[0].row}: ${errors[0].error}`
        : "";
      setNotice(
        `Evidence import: ${created} added, ${updated} updated.${detail}`,
      );
      if (errors.length) console.warn("Evidence import row errors", errors);
    } catch (error) {
      setDatabaseState("connected");
      setNotice(`Import failed: ${error.message}`);
    } finally {
      setImporting(false);
      event.target.value = "";
    }
  };
  const downloadEvidenceTemplate = () => {
    const template = {
      compatibilityRules: [],
      assertions: [],
      researchNotes: [],
    };
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(template, null, 2)], {
        type: "application/json",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "door-hardware-evidence-template.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const saveAssertion = async (event) => {
    event.preventDefault();
    markSaving();
    try {
      const payload = {
        ...assertionForm,
        conditions: JSON.parse(assertionForm.conditions || "{}"),
      };
      await api(
        assertionForm.id
          ? `/api/assertions/${assertionForm.id}`
          : "/api/assertions",
        {
          method: assertionForm.id ? "PUT" : "POST",
          body: JSON.stringify(payload),
        },
      );
      setShowAssertion(false);
      setAssertionForm(null);
      await markSaved();
      setNotice("Compatibility assertion saved.");
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    }
  };
  const removeAssertion = async (assertion) => {
    if (!window.confirm("Delete this compatibility assertion?")) return;
    markSaving();
    try {
      await api(`/api/assertions/${assertion.id}`, { method: "DELETE" });
      await markSaved();
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    }
  };
  const saveRule = async (event) => {
    event.preventDefault();
    markSaving();
    try {
      await api(
        ruleForm.id
          ? `/api/compatibility-rules/${ruleForm.id}`
          : "/api/compatibility-rules",
        {
          method: ruleForm.id ? "PUT" : "POST",
          body: JSON.stringify(ruleForm),
        },
      );
      setShowRule(false);
      setRuleForm(null);
      await markSaved();
      setNotice("Compatibility rule saved.");
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    }
  };
  const removeRule = async (rule) => {
    if (!window.confirm(`Delete rule “${rule.name}”?`)) return;
    markSaving();
    try {
      await api(`/api/compatibility-rules/${rule.id}`, { method: "DELETE" });
      await markSaved();
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    }
  };
  const runCheck = async () => {
    setChecking(true);
    try {
      setCheckResult(
        await api("/api/compatibility/check", {
          method: "POST",
          body: JSON.stringify({
            product_ids: selectedIds,
            opening: openingContext,
          }),
        }),
      );
    } catch (error) {
      setNotice(error.message);
    } finally {
      setChecking(false);
    }
  };

  const loadExampleAssembly = (scenario) => {
    const exampleProducts = scenario.products.map(
      ([category, manufacturer, model]) =>
        activeProducts.find(
          (product) =>
            product.category === category &&
            product.manufacturer === manufacturer &&
            product.model === model,
        ),
    );
    if (exampleProducts.some((product) => !product)) {
      setNotice(
        "One or more products for this example are not available in the active catalog.",
      );
      return;
    }
    setSelectedIds(exampleProducts.map((product) => String(product.id)));
    setOpening({ ...emptyOpening, ...(scenario.opening || {}) });
    setCheckResult(null);
    setShowExamples(false);
    const testNotice =
      scenario.kind === "unverified"
        ? "Test scenario loaded. Its result is for demonstration only and does not establish compatibility."
        : "Manufacturer-documented example loaded. Select Check assembly to run it.";
    setNotice(testNotice);
  };

  if (!data) {
    return (
      <div className="loading">
        <p>Opening your hardware library…</p>
        {notice && <p className="error-text">{notice}</p>}
      </div>
    );
  }

  const databaseStatus = {
    connecting: "Connecting to SQLite…",
    connected: "SQLite database connected",
    saving: "Saving to SQLite…",
    offline: "SQLite database unavailable",
  }[databaseState];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div>
            <strong>Door Hardware Checker</strong>
            <span>by Pro Security Controls Inc.</span>
          </div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav>
          <NavItem
            active={page === "check"}
            onClick={() => setPage("check")}
            icon={<ClipboardCheck size={18} />}
            label="Compatibility check"
          />
          <NavItem
            active={page === "products"}
            onClick={() => setPage("products")}
            icon={<Library size={18} />}
            label="Product catalog"
            count={activeProducts.length}
          />
          <NavItem
            active={page === "coverage"}
            onClick={() => setPage("coverage")}
            icon={<Layers3 size={18} />}
            label="Compatibility coverage"
            count={coverage?.summary?.total}
          />
          <NavItem
            active={page === "rules"}
            onClick={() => setPage("rules")}
            icon={<FilePlus2 size={18} />}
            label="Rules & assertions"
            count={data.compatibilityRules.length + data.assertions.length}
          />
          <NavItem
            active={page === "research"}
            onClick={() => setPage("research")}
            icon={<BookOpenText size={18} />}
            label="Compatibility research"
            count={data.researchNotes.length}
          />
        </nav>
        <div className="sidebar-bottom">
          <div className="system-card">
            <span
              className={`live-dot ${databaseState === "offline" ? "is-offline" : databaseState === "saving" ? "is-saving" : ""}`}
            />
            <div>
              <b>Local database</b>
              <small>SQLite · {databaseState}</small>
            </div>
            {databaseState === "connected" ? (
              <Check size={15} />
            ) : databaseState === "offline" ? (
              <X size={15} />
            ) : (
              <RefreshCw className="spin" size={15} />
            )}
          </div>
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div className="topbar-right">
            <button
              className="theme-toggle"
              type="button"
              onClick={() =>
                setThemeMode((mode) =>
                  mode === "auto"
                    ? activeTheme === "dark"
                      ? "light"
                      : "dark"
                    : "auto",
                )
              }
              aria-label={themeLabel}
            >
              <FontAwesomeIcon
                icon={
                  themeMode === "auto"
                    ? isNight
                      ? faSun
                      : faMoon
                    : activeTheme === "dark"
                      ? faMoon
                      : faSun
                }
              />
            </button>
            <span className="sync-status">
              <span
                className={`live-dot ${databaseState === "offline" ? "is-offline" : databaseState === "saving" ? "is-saving" : ""}`}
              />
              {databaseStatus}
            </span>
          </div>
        </header>
        {notice && (
          <button className="toast" onClick={() => setNotice("")}>
            {notice}
            <X size={15} />
          </button>
        )}

        {page === "check" && (
          <section className="content model-check-page">
            <div className="page-heading">
              <div>
                <h1>Check a hardware assembly</h1>
                <p>
                  Select exact product models. The checker reports which
                  interactions are documented and which still need review.
                </p>
              </div>
            </div>
            <div className="model-check-grid">
              <div className="form-panel assembly-panel">
                <div className="section-heading">
                  <div className="section-icon">
                    <ClipboardCheck size={18} />
                  </div>
                  <div>
                    <h2>Products in this opening</h2>
                    <p>Add the components you want to check together.</p>
                  </div>
                  <button
                    className="button button-primary assembly-check-button"
                    disabled={
                      checking ||
                      (selectedIds.length < 2 &&
                        !(
                          selectedIds.length === 1 &&
                          Object.values(opening).some(Boolean)
                        ))
                    }
                    onClick={runCheck}
                  >
                    {checking ? (
                      <RefreshCw className="spin" size={16} />
                    ) : (
                      <ClipboardCheck size={16} />
                    )}
                    {checking
                      ? "Checking"
                      : selectedIds.length < 2
                        ? "Check opening"
                        : "Check assembly"}
                  </button>
                </div>
                <OpeningDetails
                  opening={opening}
                  setOpening={setOpening}
                  preview={openingPreview}
                  onExample={() => setShowExamples(true)}
                />
                <HardwarePicker
                  groups={hardwareGroups}
                  categories={categories}
                  products={activeProducts}
                  selectedIds={selectedIds}
                  onSelect={(id) => {
                    setSelectedIds((ids) =>
                      ids.includes(id) ? ids : [...ids, id],
                    );
                    setCheckResult(null);
                  }}
                  onAddProduct={() => setPage("products")}
                />
                <div className="form-footer">
                  <span>
                    <CircleHelp size={14} />
                    Opening details are checked against selected products.
                  </span>
                </div>
              </div>
              <div className="result-panel assembly-result">
                <section className="selected-products-section">
                  <div className="selected-products-heading">
                    <div>
                      <h2>Selected products</h2>
                      <p>Components included in this check.</p>
                    </div>
                    <span className="step-chip">
                      {selectedProducts.length} SELECTED
                    </span>
                  </div>
                  <div className="assembly-products">
                    {selectedProducts.map((product) => (
                      <div className="assembly-product" key={product.id}>
                        <div>
                          <b>{displayName(product)}</b>
                          <span>
                            {categories[product.category] || product.category} ·{" "}
                            <StatusPill status={product.evidence_status} />
                          </span>
                        </div>
                        <button
                          className="icon-button"
                          aria-label={`Remove ${displayName(product)}`}
                          onClick={() => {
                            setSelectedIds((ids) =>
                              ids.filter((id) => Number(id) !== product.id),
                            );
                            setCheckResult(null);
                          }}
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                    {selectedProducts.length === 0 && (
                      <div className="empty-selection">
                        No products selected yet. Choose models from the catalog
                        on the left.
                      </div>
                    )}
                  </div>
                </section>
                <section className="assembly-report-section">
                  {!checkResult ? (
                    <div className="empty-report">
                      <div className="result-kicker">ASSEMBLY REPORT</div>
                      <h3>Ready when you are</h3>
                      <p>
                        Add two products for pair checks, or select one product
                        and enter opening details to check fit.
                      </p>
                      <div className="rule-stat">
                        <span className="stat-icon">
                          <ShieldCheck size={17} />
                        </span>
                        <span>
                          <b>
                            {coverage?.summary?.total || 0} applicable pair
                            checks
                          </b>
                          <small>Generated from component roles</small>
                        </span>
                      </div>
                    </div>
                  ) : (
                    <CheckResult
                      result={checkResult}
                      onCoverage={() => setPage("coverage")}
                    />
                  )}
                </section>
              </div>
            </div>
            <div className="footnote">
              <ShieldCheck size={15} />
              <span>
                Pairwise results do not prove a multi-device assembly. A
                complete assembly assertion or field test is required for
                systems with three or more products.
              </span>
            </div>
          </section>
        )}

        {page === "products" && (
          <ProductCatalog
            products={visibleProducts}
            allProducts={activeProducts}
            categories={categories}
            statuses={data.evidenceStatuses}
            search={search}
            setSearch={setSearch}
            onAdd={() => {
              setProductForm({ ...emptyProduct });
              setShowProduct(true);
            }}
            onEdit={(product) => {
              setProductForm({
                ...product,
                specifications: JSON.stringify(product.specifications, null, 2),
              });
              setShowProduct(true);
            }}
            onRemove={removeProduct}
            onImport={importProducts}
            importing={importing}
            importInput={importInput}
            onTemplate={downloadTemplate}
          />
        )}

        {page === "coverage" && (
          <CoveragePage
            coverage={coverage}
            categories={categories}
            onRefresh={() =>
              loadCoverage().catch((error) => setNotice(error.message))
            }
            onAssert={(row) => {
              const prior = data.assertions.find(
                (assertion) =>
                  assertion.product_ids.length === 2 &&
                  assertion.product_ids.includes(row.product_a.id) &&
                  assertion.product_ids.includes(row.product_b.id),
              );
              setAssertionForm(
                prior
                  ? {
                      ...prior,
                      conditions: JSON.stringify(prior.conditions, null, 2),
                    }
                  : {
                      ...emptyAssertion,
                      product_ids: [row.product_a.id, row.product_b.id],
                    },
              );
              setShowAssertion(true);
            }}
          />
        )}

        {page === "rules" && (
          <RulesPage
            rules={data.compatibilityRules}
            assertions={data.assertions}
            products={activeProducts}
            categories={categories}
            onAddRule={() => {
              setRuleForm({ ...emptyRule });
              setShowRule(true);
            }}
            onEditRule={(rule) => {
              setRuleForm({ ...rule });
              setShowRule(true);
            }}
            onRemoveRule={removeRule}
            onAddAssertion={() => {
              setAssertionForm({ ...emptyAssertion });
              setShowAssertion(true);
            }}
            onEditAssertion={(assertion) => {
              setAssertionForm({
                ...assertion,
                conditions: JSON.stringify(assertion.conditions, null, 2),
              });
              setShowAssertion(true);
            }}
            onRemoveAssertion={removeAssertion}
            onImportBundle={() => evidenceImportInput.current?.click()}
            onDownloadTemplate={downloadEvidenceTemplate}
            importing={importing}
          />
        )}

        {page === "research" && (
          <ResearchPage
            notes={data.researchNotes}
            onImportBundle={() => evidenceImportInput.current?.click()}
            onDownloadTemplate={downloadEvidenceTemplate}
            importing={importing}
          />
        )}
      </main>

      <input
        ref={evidenceImportInput}
        type="file"
        accept=".json,application/json"
        hidden
        onChange={importEvidenceBundle}
      />

      {showExamples && (
        <Modal
          title="Load a test example"
          subtitle="Choose a documented pairing or a clearly marked demo scenario."
          onClose={() => setShowExamples(false)}
        >
          <div className="example-warning">
            <CircleHelp size={17} />
            <span>
              Test-only scenarios can show unverified or incompatible results.
              They do not add approvals or change the database.
            </span>
          </div>
          <div className="example-list">
            {exampleScenarios.map((scenario) => {
              const available = scenario.products.every(
                ([category, manufacturer, model]) =>
                  activeProducts.some(
                    (product) =>
                      product.category === category &&
                      product.manufacturer === manufacturer &&
                      product.model === model,
                  ),
              );
              return (
                <article className="example-card" key={scenario.id}>
                  <div className="example-card-copy">
                    <div>
                      <h3>{scenario.title}</h3>
                      <span
                        className={`example-badge example-${scenario.kind}`}
                      >
                        {scenario.expected}
                      </span>
                    </div>
                    <p>{scenario.description}</p>
                  </div>
                  <button
                    className="button button-quiet"
                    type="button"
                    disabled={!available}
                    onClick={() => loadExampleAssembly(scenario)}
                  >
                    {available ? "Load" : "Unavailable"}
                  </button>
                </article>
              );
            })}
          </div>
        </Modal>
      )}
      {showProduct && productForm && (
        <Modal
          title={productForm.id ? "Edit product model" : "Add product model"}
          subtitle="Store a product once with its specs and source."
          onClose={() => setShowProduct(false)}
        >
          <ProductForm
            form={productForm}
            setForm={setProductForm}
            categories={categories}
            statuses={data.evidenceStatuses}
            onSubmit={saveProduct}
          />
        </Modal>
      )}
      {showRule && ruleForm && (
        <Modal
          title={
            ruleForm.id
              ? "Edit reusable rule"
              : "Add reusable compatibility rule"
          }
          subtitle="A reusable rule evaluates a specific interface or specification."
          onClose={() => setShowRule(false)}
        >
          <RuleForm
            form={ruleForm}
            setForm={setRuleForm}
            categories={categories}
            statuses={data.evidenceStatuses}
            onSubmit={saveRule}
          />
        </Modal>
      )}
      {showAssertion && assertionForm && (
        <Modal
          title={
            assertionForm.id
              ? "Edit compatibility assertion"
              : "Add compatibility assertion"
          }
          subtitle="Record a sourced pair or complete multi-device combination."
          onClose={() => setShowAssertion(false)}
        >
          <AssertionForm
            form={assertionForm}
            setForm={setAssertionForm}
            products={activeProducts}
            statuses={data.evidenceStatuses}
            onSubmit={saveAssertion}
          />
        </Modal>
      )}
    </div>
  );
}

function HardwarePicker({
  groups,
  categories,
  products,
  selectedIds,
  onSelect,
  onAddProduct,
}) {
  return (
    <div className="hardware-picker">
      <div className="hardware-picker-heading">
        <div>
          <b>Add hardware by type</b>
          <span>
            Choose exact models from the catalog. Add a model there if its list
            is empty.
          </span>
        </div>
        <button className="text-link" type="button" onClick={onAddProduct}>
          <Plus size={13} />
          Add to catalog
        </button>
      </div>
      <div className="hardware-picker-grid">
        {groups.map((group) => {
          const selectedInGroup = [...selectedIds]
            .reverse()
            .map((id) =>
              products.find((product) => String(product.id) === String(id)),
            )
            .find(
              (product) =>
                product && group.categories.includes(product.category),
            );
          const options = group.categories.flatMap((category) =>
            products.filter(
              (product) =>
                product.category === category &&
                (!selectedIds.includes(String(product.id)) ||
                  product.id === selectedInGroup?.id),
            ),
          );
          return (
            <label className="field" key={group.label}>
              <span>{group.label}</span>
              <div className="select-wrap">
                <select
                  value={selectedInGroup ? String(selectedInGroup.id) : ""}
                  onChange={(event) => {
                    if (event.target.value)
                      onSelect(String(event.target.value));
                  }}
                >
                  <option value="">
                    {options.length
                      ? "Select from catalog"
                      : "No models in catalog yet"}
                  </option>
                  {group.categories.map((category) => {
                    const categoryProducts = options.filter(
                      (product) => product.category === category,
                    );
                    return categoryProducts.length ? (
                      <optgroup
                        key={category}
                        label={categories[category] || category}
                      >
                        {categoryProducts.map((product) => (
                          <option key={product.id} value={product.id}>
                            {displayName(product)}
                          </option>
                        ))}
                      </optgroup>
                    ) : null;
                  })}
                </select>
                <ChevronDown size={15} />
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}

function OpeningDetails({ opening, setOpening, preview, onExample }) {
  const update = (key, value) =>
    setOpening((current) => ({ ...current, [key]: value }));
  return (
    <details className="opening-details" open>
      <summary>
        <b>Opening details</b>
        <span>Used to check the selected products against this door</span>
        <button
          className="button button-quiet opening-example-button"
          type="button"
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            onExample();
          }}
        >
          Examples
        </button>
      </summary>
      <div className="opening-fields">
        <Field label="Door material">
          <Select
            value={opening.door_material}
            onChange={(value) => update("door_material", value)}
            options={[
              ["", "Not specified"],
              ["wood", "Wood"],
              ["metal", "Metal"],
              ["aluminum", "Aluminum"],
              ["glass", "Glass"],
              ["other", "Other"],
            ]}
          />
        </Field>
        <Field label="Frame material">
          <Select
            value={opening.frame_material}
            onChange={(value) => update("frame_material", value)}
            options={[
              ["", "Not specified"],
              ["steel", "Steel"],
              ["wood", "Wood"],
              ["aluminum", "Aluminum"],
              ["glass", "Glass"],
              ["other", "Other"],
            ]}
          />
        </Field>
        <Field label="Door configuration">
          <Select
            value={opening.configuration}
            onChange={(value) => update("configuration", value)}
            options={[
              ["", "Not specified"],
              ["single", "Single"],
              ["pair", "Pair"],
            ]}
          />
        </Field>
        <Field label="Handing">
          <Select
            value={opening.handing}
            onChange={(value) => update("handing", value)}
            options={[
              ["", "Not specified"],
              ["left", "Left hand"],
              ["right", "Right hand"],
              ["left_reverse", "Left hand reverse"],
              ["right_reverse", "Right hand reverse"],
            ]}
          />
        </Field>
        <Field label="Swing direction">
          <Select
            value={opening.swing_direction}
            onChange={(value) => update("swing_direction", value)}
            options={[
              ["", "Not specified"],
              ["inswing", "Inswing"],
              ["outswing", "Outswing"],
              ["double_egress", "Double egress"],
            ]}
          />
        </Field>
        <Field label="Location">
          <Select
            value={opening.location}
            onChange={(value) => update("location", value)}
            options={[
              ["", "Not specified"],
              ["interior", "Interior"],
              ["exterior", "Exterior"],
            ]}
          />
        </Field>
        <Field label="Fire rated">
          <Select
            value={opening.fire_rated}
            onChange={(value) => update("fire_rated", value)}
            options={[
              ["", "Not specified"],
              ["yes", "Yes"],
              ["no", "No"],
            ]}
          />
        </Field>
        <Field label="Door width (in)">
          <input
            type="number"
            min="0"
            step="0.1"
            value={opening.width_in}
            onChange={(event) => update("width_in", event.target.value)}
            placeholder="Not specified"
          />
        </Field>
        <Field label="Door height (in)">
          <input
            type="number"
            min="0"
            step="0.1"
            value={opening.height_in}
            onChange={(event) => update("height_in", event.target.value)}
            placeholder="Not specified"
          />
        </Field>
        <Field label="Door weight (lb)">
          <input
            type="number"
            min="0"
            step="0.1"
            value={opening.weight_lb}
            onChange={(event) => update("weight_lb", event.target.value)}
            placeholder="Not specified"
          />
        </Field>
        <Field label="Frame reveal depth (mm)">
          <input
            type="number"
            min="0"
            step="1"
            value={opening.reveal_depth_mm}
            onChange={(event) => update("reveal_depth_mm", event.target.value)}
            placeholder="Not specified"
          />
        </Field>
      </div>
      <div
        className={`opening-fit-preview ${preview ? `status-${preview.status}` : ""}`}
      >
        {preview ? (
          <>
            <div className="opening-fit-heading">
              <StatusPill status={preview.status} />
              <b>{preview.message}</b>
            </div>
            {preview.findings?.map((finding, index) => (
              <div
                className="opening-fit-finding"
                key={`${finding.product_a?.id || index}-${finding.product_a?.model || "opening"}`}
              >
                {finding.product_a && (
                  <strong>{displayName(finding.product_a)}</strong>
                )}
                <span>{finding.rationale}</span>
              </div>
            ))}
          </>
        ) : (
          <span>
            Enter opening details to see how they apply to the selected
            products. This review updates as you edit.
          </span>
        )}
      </div>
    </details>
  );
}

function NavItem({ active, onClick, icon, label, count }) {
  return (
    <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick}>
      {icon}
      <span>{label}</span>
      {count != null && <span className="nav-count">{count}</span>}
    </button>
  );
}

function Modal({ title, subtitle, onClose, children }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="rule-modal model-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-head">
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={19} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ProductForm({ form, setForm, categories, statuses, onSubmit }) {
  const update = (key, value) =>
    setForm((current) => ({ ...current, [key]: value }));
  return (
    <form className="model-form" onSubmit={onSubmit}>
      <div className="modal-fields">
        <Field label="Component category">
          <Select
            value={form.category}
            onChange={(value) => update("category", value)}
            options={Object.entries(categories).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Manufacturer">
          <input
            required
            value={form.manufacturer}
            onChange={(event) => update("manufacturer", event.target.value)}
            placeholder="e.g. Manufacturer name"
          />
        </Field>
        <Field label="Model / SKU">
          <input
            required
            value={form.model}
            onChange={(event) => update("model", event.target.value)}
            placeholder="Exact model identifier"
          />
        </Field>
        <Field label="Display name">
          <input
            value={form.name}
            onChange={(event) => update("name", event.target.value)}
            placeholder="Defaults to the model"
          />
        </Field>
        <Field label="Evidence status">
          <Select
            value={form.evidence_status}
            onChange={(value) => update("evidence_status", value)}
            options={Object.entries(statuses).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Source title">
          <input
            value={form.source_title}
            onChange={(event) => update("source_title", event.target.value)}
            placeholder="Manufacturer data sheet"
          />
        </Field>
        <Field label="Source URL" wide>
          <input
            type="url"
            value={form.source_url}
            required={form.evidence_status !== "research_lead"}
            onChange={(event) => update("source_url", event.target.value)}
            placeholder="https://…"
          />
        </Field>
        <Field label="Specifications (JSON)" wide>
          <textarea
            className="json-input"
            value={form.specifications}
            onChange={(event) => update("specifications", event.target.value)}
            placeholder={
              '{"input_voltage":"24V DC","output_type":"dry_contact"}'
            }
          />
        </Field>
        <Field label="Notes" wide>
          <textarea
            value={form.notes}
            onChange={(event) => update("notes", event.target.value)}
            placeholder="Additional product details"
          />
        </Field>
      </div>
      <div className="modal-actions">
        <button className="button button-primary" type="submit">
          <Check size={16} />
          Save product
        </button>
      </div>
    </form>
  );
}

function RuleForm({ form, setForm, categories, statuses, onSubmit }) {
  const update = (key, value) =>
    setForm((current) => ({ ...current, [key]: value }));
  const outcomes = [
    ["compatible", "Compatible"],
    ["incompatible", "Incompatible"],
    ["conditional", "Conditional"],
  ];
  return (
    <form className="model-form" onSubmit={onSubmit}>
      <div className="modal-fields">
        <Field label="Rule name" wide>
          <input
            required
            value={form.name}
            onChange={(event) => update("name", event.target.value)}
            placeholder="e.g. Operator accepts dry-contact activation"
          />
        </Field>
        <Field label="Component A">
          <Select
            value={form.category_a}
            onChange={(value) => update("category_a", value)}
            options={Object.entries(categories).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Component B">
          <Select
            value={form.category_b}
            onChange={(value) => update("category_b", value)}
            options={Object.entries(categories).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Specification on A">
          <input
            required
            value={form.spec_a}
            onChange={(event) => update("spec_a", event.target.value)}
            placeholder="e.g. activation_input"
          />
        </Field>
        <Field label="Comparison">
          <Select
            value={form.comparison}
            onChange={(value) => update("comparison", value)}
            options={[
              ["equals", "Equals"],
              ["not_equals", "Does not equal"],
              ["less_or_equal", "Less than or equal"],
              ["greater_or_equal", "Greater than or equal"],
              ["contains", "Contains"],
            ]}
          />
        </Field>
        <Field label="Specification on B">
          <input
            required
            value={form.spec_b}
            onChange={(event) => update("spec_b", event.target.value)}
            placeholder="e.g. signal_type"
          />
        </Field>
        <Field label="When the comparison passes">
          <Select
            value={form.pass_outcome}
            onChange={(value) => update("pass_outcome", value)}
            options={outcomes}
          />
        </Field>
        <Field label="When it fails">
          <Select
            value={form.fail_outcome}
            onChange={(value) => update("fail_outcome", value)}
            options={outcomes}
          />
        </Field>
        <Field label="Evidence status">
          <Select
            value={form.evidence_status}
            onChange={(value) => update("evidence_status", value)}
            options={Object.entries(statuses).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Source title">
          <input
            value={form.source_title}
            onChange={(event) => update("source_title", event.target.value)}
          />
        </Field>
        <Field label="Source URL" wide>
          <input
            type="url"
            value={form.source_url}
            required={form.evidence_status !== "research_lead"}
            onChange={(event) => update("source_url", event.target.value)}
            placeholder="https://…"
          />
        </Field>
        <Field label="Rationale" wide>
          <textarea
            required
            value={form.rationale}
            onChange={(event) => update("rationale", event.target.value)}
            placeholder="What does this check establish?"
          />
        </Field>
      </div>
      <div className="modal-actions">
        <button className="button button-primary" type="submit">
          <Check size={16} />
          Save rule
        </button>
      </div>
    </form>
  );
}

function AssertionForm({ form, setForm, products, statuses, onSubmit }) {
  const update = (key, value) =>
    setForm((current) => ({ ...current, [key]: value }));
  const toggleProduct = (id) =>
    setForm((current) => ({
      ...current,
      product_ids: current.product_ids.includes(id)
        ? current.product_ids.filter((value) => value !== id)
        : [...current.product_ids, id],
    }));
  return (
    <form className="model-form" onSubmit={onSubmit}>
      <div className="field">
        <span>Products in this assertion</span>
        <div className="assertion-product-list">
          {products.map((product) => (
            <label key={product.id}>
              <input
                type="checkbox"
                checked={form.product_ids.includes(product.id)}
                onChange={() => toggleProduct(product.id)}
              />
              <span>
                {displayName(product)} <small>· {product.category_label}</small>
              </span>
            </label>
          ))}
        </div>
      </div>
      <div className="modal-fields assertion-fields">
        <Field label="Outcome">
          <Select
            value={form.outcome}
            onChange={(value) => update("outcome", value)}
            options={[
              ["compatible", "Compatible"],
              ["incompatible", "Incompatible"],
              ["conditional", "Conditional"],
            ]}
          />
        </Field>
        <Field label="Evidence status">
          <Select
            value={form.evidence_status}
            onChange={(value) => update("evidence_status", value)}
            options={Object.entries(statuses).map(([value, label]) => [
              value,
              label,
            ])}
          />
        </Field>
        <Field label="Source title">
          <input
            value={form.source_title}
            onChange={(event) => update("source_title", event.target.value)}
          />
        </Field>
        <Field label="Source URL" wide>
          <input
            type="url"
            value={form.source_url}
            required={form.evidence_status !== "research_lead"}
            onChange={(event) => update("source_url", event.target.value)}
            placeholder="https://…"
          />
        </Field>
        <Field label="Conditions (JSON)" wide>
          <textarea
            className="json-input"
            value={form.conditions}
            onChange={(event) => update("conditions", event.target.value)}
            placeholder="{}"
          />
        </Field>
        <Field label="Rationale" wide>
          <textarea
            required
            value={form.rationale}
            onChange={(event) => update("rationale", event.target.value)}
            placeholder="Describe the tested or documented interaction"
          />
        </Field>
      </div>
      <div className="modal-actions">
        <button className="button button-primary" type="submit">
          <Check size={16} />
          Save assertion
        </button>
      </div>
    </form>
  );
}

function Field({ label, wide, children }) {
  return (
    <label className={`field ${wide ? "field-wide" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function Select({ value, onChange, options }) {
  return (
    <div className="select-wrap">
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, label]) => (
          <option key={optionValue} value={optionValue}>
            {label}
          </option>
        ))}
      </select>
      <ChevronDown size={15} />
    </div>
  );
}

function ProductCatalog({
  products,
  allProducts,
  categories,
  statuses,
  search,
  setSearch,
  onAdd,
  onEdit,
  onRemove,
  onImport,
  importing,
  importInput,
  onTemplate,
}) {
  const grouped = useMemo(
    () =>
      Object.entries(categories)
        .map(([key, label]) => [
          key,
          label,
          allProducts.filter((product) => product.category === key).length,
        ])
        .filter(([, , count]) => count),
    [allProducts, categories],
  );
  return (
    <section className="content model-page">
      <div className="page-heading">
        <div>
          <h1>Product catalog</h1>
          <p>
            Enter each exact product model once, with its specifications and
            evidence source.
          </p>
        </div>
        <span className="total-pill">{allProducts.length} MODELS</span>
      </div>
      <div className="catalog-actions">
        <button className="button button-primary" onClick={onAdd}>
          <Plus size={16} />
          Add product
        </button>
        <button
          className="button button-quiet"
          onClick={() => importInput.current?.click()}
          disabled={importing}
        >
          <Upload size={15} />
          {importing ? "Importing…" : "Import CSV"}
        </button>
        <button className="text-link" onClick={onTemplate}>
          Download CSV template <ArrowUpRight size={14} />
        </button>
        <input
          ref={importInput}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={onImport}
        />
      </div>
      <div className="category-chips">
        {grouped.map(([key, label, count]) => (
          <span key={key}>
            {label}
            <b>{count}</b>
          </span>
        ))}
      </div>
      <div className="catalog-panel">
        <div className="catalog-toolbar">
          <div>
            <h2>Models</h2>
            <p>Research leads are not treated as verified products.</p>
          </div>
          <div className="searchbox">
            <Search size={15} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search models"
            />
          </div>
        </div>
        <div className="product-table-wrap">
          <table className="product-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Evidence</th>
                <th>Source</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td>
                    <b>{displayName(product)}</b>
                    <small>{product.name}</small>
                  </td>
                  <td>{categories[product.category] || product.category}</td>
                  <td>
                    <StatusPill status={product.evidence_status} />
                  </td>
                  <td>
                    {product.source_url ? (
                      <a
                        className="source-link"
                        href={product.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {product.source_title || "View source"}{" "}
                        <ArrowUpRight size={12} />
                      </a>
                    ) : (
                      <span className="muted">No source</span>
                    )}
                  </td>
                  <td className="table-actions">
                    <button
                      className="icon-button"
                      aria-label="Edit product"
                      onClick={() => onEdit(product)}
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      className="icon-button danger-hover"
                      aria-label="Archive product"
                      onClick={() => onRemove(product)}
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {products.length === 0 && (
            <div className="no-items">No product models match this search.</div>
          )}
        </div>
      </div>
    </section>
  );
}

function CoveragePage({ coverage, categories, onRefresh, onAssert }) {
  return (
    <section className="content model-page">
      <div className="page-heading">
        <div>
          <h1>Compatibility coverage</h1>
          <p>
            Relevant component pairs are generated from system roles. Missing
            evidence stays visible as unverified.
          </p>
        </div>
        <button className="button button-quiet" onClick={onRefresh}>
          <RefreshCw size={15} />
          Refresh coverage
        </button>
      </div>
      <div className="coverage-summary">
        {[
          "total",
          "compatible",
          "incompatible",
          "conditional",
          "unverified",
        ].map((key) => (
          <div className={`coverage-stat coverage-${key}`} key={key}>
            <small>
              {key === "total" ? "CANDIDATE PAIRS" : key.toUpperCase()}
            </small>
            <b>{coverage?.summary?.[key] ?? "—"}</b>
          </div>
        ))}
      </div>
      <div className="coverage-note">
        <CircleHelp size={16} />
        <span>
          Only declared interaction categories are enumerated; unrelated
          products aren’t crossed together. Add product models to expand
          relevant coverage.
        </span>
      </div>
      <div className="catalog-panel coverage-panel">
        <div className="catalog-toolbar">
          <div>
            <h2>Applicable product pairs</h2>
            <p>
              {coverage?.summary?.assessed || 0} of{" "}
              {coverage?.summary?.total || 0} have a sourced outcome.
            </p>
          </div>
        </div>
        <div className="product-table-wrap">
          <table className="product-table coverage-table">
            <thead>
              <tr>
                <th>Component A</th>
                <th>Component B</th>
                <th>Result</th>
                <th>Evidence / finding</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(coverage?.rows || []).map((row) => (
                <tr key={`${row.product_a.id}-${row.product_b.id}`}>
                  <td>
                    <b>{displayName(row.product_a)}</b>
                    <small>{categories[row.product_a.category]}</small>
                  </td>
                  <td>
                    <b>{displayName(row.product_b)}</b>
                    <small>{categories[row.product_b.category]}</small>
                  </td>
                  <td>
                    <StatusPill status={row.status} />
                  </td>
                  <td>
                    <span>
                      {row.rationale ||
                        "No sourced assertion or applicable rule."}
                    </span>
                    {row.source_url && (
                      <a
                        className="source-link"
                        href={row.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Source <ArrowUpRight size={12} />
                      </a>
                    )}
                  </td>
                  <td>
                    <button
                      className="button button-small"
                      onClick={() => onAssert(row)}
                    >
                      Record outcome
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!coverage?.rows?.length && (
            <div className="no-items">
              No applicable pairs yet. Add products in interacting categories to
              generate the coverage list.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function RulesPage({
  rules,
  assertions,
  products,
  categories,
  onAddRule,
  onEditRule,
  onRemoveRule,
  onAddAssertion,
  onEditAssertion,
  onRemoveAssertion,
  onImportBundle,
  onDownloadTemplate,
  importing,
}) {
  return (
    <section className="content model-page">
      <div className="page-heading">
        <div>
          <h1>Rules & assertions</h1>
          <p>
            Reusable specification checks and sourced exceptions for specific
            products or complete kits.
          </p>
        </div>
        <div className="page-heading-actions">
          <button
            className="button button-quiet"
            onClick={onImportBundle}
            disabled={importing}
          >
            <Upload size={15} />
            {importing ? "Importing…" : "Import JSON"}
          </button>
          <button className="text-link" onClick={onDownloadTemplate}>
            Download template <ArrowUpRight size={14} />
          </button>
        </div>
      </div>
      <div className="rules-toolbar">
        <button className="button button-primary" onClick={onAddRule}>
          <Plus size={16} />
          Add reusable rule
        </button>
        <button className="button button-quiet" onClick={onAddAssertion}>
          <FilePlus2 size={16} />
          Add product combination
        </button>
      </div>
      <div className="rule-banner">
        <div className="banner-icon">
          <ShieldCheck size={18} />
        </div>
        <div>
          <b>Only sourced rules contribute a verified result.</b>
          <span>
            Research leads remain visible for review but cannot mark a
            combination compatible.
          </span>
        </div>
      </div>
      <div className="model-subheading">
        <div>
          <h2>Reusable rules</h2>
          <p>Apply one interface rule across matching component categories.</p>
        </div>
        <span className="total-pill">{rules.length}</span>
      </div>
      <div className="model-record-list">
        {rules.map((rule) => (
          <article className="model-record" key={rule.id}>
            <div className="model-record-top">
              <div>
                <h3>{rule.name}</h3>
                <p>
                  {categories[rule.category_a]} · {rule.spec_a}{" "}
                  {rule.comparison.replaceAll("_", " ")} {rule.spec_b} ·{" "}
                  {categories[rule.category_b]}
                </p>
              </div>
              <StatusPill status={rule.evidence_status} />
              <button
                className="icon-button"
                aria-label="Edit rule"
                onClick={() => onEditRule(rule)}
              >
                <Pencil size={15} />
              </button>
              <button
                className="icon-button danger-hover"
                aria-label="Delete rule"
                onClick={() => onRemoveRule(rule)}
              >
                <Trash2 size={15} />
              </button>
            </div>
            <div className="model-record-detail">
              Pass: {rule.pass_outcome} · Fail: {rule.fail_outcome}
              {rule.rationale ? ` · ${rule.rationale}` : ""}
            </div>
            {rule.source_url && (
              <a
                className="source-link"
                href={rule.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {rule.source_title || "Source"} <ArrowUpRight size={12} />
              </a>
            )}
          </article>
        ))}
        {rules.length === 0 && (
          <div className="no-items">
            No reusable rules yet. Add a sourced rule when products share a
            repeatable interface check.
          </div>
        )}
      </div>
      <div className="model-subheading assertion-heading">
        <div>
          <h2>Specific combinations</h2>
          <p>
            Pair or multi-device records that can’t be safely reduced to one
            generic rule.
          </p>
        </div>
        <span className="total-pill">{assertions.length}</span>
      </div>
      <div className="model-record-list">
        {assertions.map((assertion) => {
          const names = assertion.product_ids
            .map((id) => products.find((product) => product.id === id))
            .filter(Boolean)
            .map(displayName);
          return (
            <article className="model-record" key={assertion.id}>
              <div className="model-record-top">
                <div>
                  <h3>{names.join(" + ") || "Archived product combination"}</h3>
                  <p>
                    <StatusPill status={assertion.outcome} />{" "}
                    <span className="evidence-inline">·</span>{" "}
                    <StatusPill status={assertion.evidence_status} />
                  </p>
                </div>
                <button
                  className="icon-button"
                  aria-label="Edit assertion"
                  onClick={() => onEditAssertion(assertion)}
                >
                  <Pencil size={15} />
                </button>
                <button
                  className="icon-button danger-hover"
                  aria-label="Delete assertion"
                  onClick={() => onRemoveAssertion(assertion)}
                >
                  <Trash2 size={15} />
                </button>
              </div>
              {assertion.rationale && (
                <div className="model-record-detail">{assertion.rationale}</div>
              )}
              {assertion.source_url && (
                <a
                  className="source-link"
                  href={assertion.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {assertion.source_title || "Source"}{" "}
                  <ArrowUpRight size={12} />
                </a>
              )}
            </article>
          );
        })}
        {assertions.length === 0 && (
          <div className="no-items">No product-specific assertions yet.</div>
        )}
      </div>
    </section>
  );
}

function ResearchPage({
  notes,
  onImportBundle,
  onDownloadTemplate,
  importing,
}) {
  return (
    <section className="content research-page">
      <div className="page-heading">
        <div>
          <h1>Compatibility research</h1>
          <p>
            Source-backed leads that guide product modeling. These are not
            compatibility decisions.
          </p>
        </div>
        <div className="page-heading-actions">
          <span className="total-pill">{notes.length} SOURCE NOTES</span>
          <button
            className="button button-quiet"
            onClick={onImportBundle}
            disabled={importing}
          >
            <Upload size={15} />
            {importing ? "Importing…" : "Import JSON"}
          </button>
          <button className="text-link" onClick={onDownloadTemplate}>
            Download template <ArrowUpRight size={14} />
          </button>
        </div>
      </div>
      <div className="research-banner">
        <div className="banner-icon">
          <CircleHelp size={18} />
        </div>
        <div>
          <b>Research lead only · not an approval</b>
          <span>
            Use manufacturer documentation and field verification before marking
            a combination compatible.
          </span>
        </div>
      </div>
      <div className="research-list">
        {notes.map((note) => (
          <article className="research-card" key={note.id}>
            <div className="research-card-heading">
              <div>
                <h2>{note.topic}</h2>
                <span className="research-status">
                  {note.evidence_status === "documentation_needed"
                    ? "DOCUMENTATION NEEDED"
                    : "UNVERIFIED RESEARCH LEAD"}
                </span>
              </div>
              <a
                className="source-link"
                href={note.source_url}
                target="_blank"
                rel="noreferrer"
              >
                View source <ArrowUpRight size={14} />
              </a>
            </div>
            <div className="research-components">{note.related_components}</div>
            <p>{note.guidance}</p>
            <a
              className="research-source-title"
              href={note.source_url}
              target="_blank"
              rel="noreferrer"
            >
              {note.source_title}
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

function CheckResult({ result, onCoverage }) {
  const labels = {
    compatible: "Compatible",
    incompatible: "Incompatible",
    conditional: "Conditional",
    unverified: "Not yet verified",
  };
  return (
    <div className={`assembly-result-content status-${result.status}`}>
      <div className="result-symbol">
        {result.status === "compatible" ? (
          <Check size={24} />
        ) : result.status === "incompatible" ? (
          <X size={24} />
        ) : (
          <CircleHelp size={24} />
        )}
      </div>
      <div className="result-kicker">ASSEMBLY REPORT</div>
      <h3>{labels[result.status]}</h3>
      <p>{result.message || result.assertion?.rationale}</p>
      {result.findings?.map((finding, index) => (
        <div
          className="finding-card"
          key={`${finding.product_a?.id || "assembly"}-${finding.product_b?.id || index}`}
        >
          <div className="finding-title">
            <StatusPill status={finding.status} />
            {finding.product_a && (
              <b>
                {displayName(finding.product_a)}
                {finding.product_b
                  ? ` + ${displayName(finding.product_b)}`
                  : " · opening fit"}
              </b>
            )}
          </div>
          <p>{finding.rationale}</p>
          {finding.source_url && (
            <a
              className="source-link"
              href={finding.source_url}
              target="_blank"
              rel="noreferrer"
            >
              {finding.source_title || "Evidence source"}{" "}
              <ArrowUpRight size={12} />
            </a>
          )}
        </div>
      ))}
      <button className="text-link" onClick={onCoverage}>
        Open coverage view <ArrowUpRight size={14} />
      </button>
    </div>
  );
}

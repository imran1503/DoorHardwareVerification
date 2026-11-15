import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMoon, faSun } from "@fortawesome/free-solid-svg-icons";
import {
  Activity,
  ArrowUpRight,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  DoorOpen,
  BookOpenText,
  FilePlus2,
  Layers3,
  Library,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import "./styles.css";

const FIELD_KEYS = [
  "door_material",
  "frame_material",
  "swing",
  "door_type",
  "door_location",
  "fire_rated",
  "strike",
  "operator",
  "automatic_operator",
  "activation_device",
  "lock_interface",
  "power_architecture",
  "safety_device",
  "existing_hardware",
  "proposed_hardware",
  "voltage",
  "controller",
  "door_contact",
  "request_to_exit",
];
const FIELD_GROUPS = [
  {
    title: "Door & frame",
    description: "Opening construction and handing",
    fields: [
      "door_material",
      "frame_material",
      "swing",
      "door_type",
      "door_location",
      "fire_rated",
    ],
  },
  {
    title: "Locking hardware",
    description: "Existing and proposed lock components",
    fields: ["strike", "existing_hardware", "proposed_hardware", "lock_interface"],
  },
  {
    title: "Automatic door operator (ADO) & controls",
    description: "Operator, activation, power, and safety devices",
    fields: [
      "automatic_operator",
      "operator",
      "activation_device",
      "controller",
      "voltage",
      "power_architecture",
      "safety_device",
      "door_contact",
      "request_to_exit",
    ],
  },
];
const FIXED_OPTIONS = {
  swing: ["Left", "Right", "Left Reverse", "Right Reverse", "None"],
  door_type: ["Single", "Double"],
  fire_rated: ["Yes", "No"],
  door_contact: ["Yes", "No", "Not required"],
  request_to_exit: ["Yes", "No", "Not required"],
};
const FIELD_LABELS = {
  automatic_operator: "Automatic operator model",
  activation_device: "Activation device",
  lock_interface: "Lock interface",
  power_architecture: "Power arrangement",
  safety_device: "Safety device",
  operator: "Operator handing / ADO type",
};
const CATEGORY_LABELS = {
  automatic_operator: "Automatic operator model",
  activation_device: "Operator activation device",
  lock_interface: "Operator lock interface",
  power_architecture: "Power arrangement",
  safety_device: "Operator safety device",
};
const EMPTY = Object.fromEntries(FIELD_KEYS.map((k) => [k, ""]));
const request = async (url, options = {}) => {
  let response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch (error) {
    error.isNetworkError = true;
    throw error;
  }
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Something went wrong");
  return body;
};

function App() {
  const [data, setData] = useState(null),
    [page, setPage] = useState("verify"),
    [selection, setSelection] = useState(EMPTY);
  const [databaseState, setDatabaseState] = useState("connecting");
  const [themeMode, setThemeMode] = useState(() => {
    const savedMode = window.localStorage.getItem("door-hardware-theme");
    return ["auto", "light", "dark"].includes(savedMode) ? savedMode : "auto";
  });
  const [localTime, setLocalTime] = useState(() => new Date());
  const [result, setResult] = useState(null),
    [checking, setChecking] = useState(false),
    [query, setQuery] = useState("");
  const [notice, setNotice] = useState(""),
    [itemForm, setItemForm] = useState({
      category: "door_material",
      name: "",
      notes: "",
    });
  const [ruleForm, setRuleForm] = useState(null),
    [showRule, setShowRule] = useState(false);
  const isNight = localTime.getHours() >= 18 || localTime.getHours() < 6;
  const activeTheme =
    themeMode === "auto" ? (isNight ? "dark" : "light") : themeMode;
  const nextTheme = isNight ? "Light" : "Dark";
  const nextThemeTime = isNight ? "6 AM" : "6 PM";
  const themeTitle =
    themeMode === "auto"
      ? `Automatic theme · switches to ${nextTheme.toLowerCase()} at ${nextThemeTime} local time. Click to override.`
      : `${activeTheme} theme selected · click to resume automatic time-based theme.`;
  const toggleTheme = () =>
    setThemeMode((mode) =>
      mode === "auto" ? (activeTheme === "dark" ? "light" : "dark") : "auto",
    );
  useEffect(() => {
    const clockInterval = window.setInterval(() => setLocalTime(new Date()), 60000);
    return () => window.clearInterval(clockInterval);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = activeTheme;
    window.localStorage.setItem("door-hardware-theme", themeMode);
  }, [activeTheme, themeMode]);
  const refresh = async () => {
    try {
      const nextData = await request("/api/bootstrap");
      setData({ ...nextData, researchNotes: nextData.researchNotes || [] });
      setDatabaseState((state) =>
        state === "saving" ? "saving" : "connected",
      );
    } catch (error) {
      setDatabaseState(error.isNetworkError ? "offline" : "connected");
      throw error;
    }
  };
  useEffect(() => {
    refresh().catch((e) => setNotice(e.message));
    const checkConnection = async () => {
      try {
        await request("/api/health");
        setDatabaseState((state) =>
          state === "saving" ? "saving" : "connected",
        );
      } catch {
        setDatabaseState("offline");
      }
    };
    const interval = window.setInterval(checkConnection, 15000);
    return () => window.clearInterval(interval);
  }, []);
  const markWriteStarted = () => setDatabaseState("saving");
  const markWriteFailed = (error) =>
    setDatabaseState(error.isNetworkError ? "offline" : "connected");
  const databaseStatusText = {
    connecting: "Connecting to SQLite…",
    connected: "SQLite database connected",
    saving: "Saving to SQLite…",
    offline: "SQLite database unavailable",
  }[databaseState];
  const itemCounts = useMemo(
    () =>
      Object.fromEntries(
        Object.keys({ ...CATEGORY_LABELS, ...(data?.categories || {}) }).map((c) => [
          c,
          data?.items.filter((i) => i.category === c).length || 0,
        ]),
      ),
    [data],
  );
  const options = (key) =>
    key in FIXED_OPTIONS
      ? FIXED_OPTIONS[key]
      : data?.items.filter((i) => i.category === key).map((i) => i.name) || [];
  const check = async () => {
    setChecking(true);
    setResult(null);
    try {
      setResult(
        await request("/api/check", {
          method: "POST",
          body: JSON.stringify(selection),
        }),
      );
    } catch (e) {
      setNotice(e.message);
    } finally {
      setChecking(false);
    }
  };
  const addItem = async (e) => {
    e.preventDefault();
    markWriteStarted();
    try {
      const editing = Boolean(itemForm.id);
      await request(editing ? `/api/items/${itemForm.id}` : "/api/items", {
        method: editing ? "PUT" : "POST",
        body: JSON.stringify(itemForm),
      });
      setItemForm({ category: "door_material", name: "", notes: "" });
      await refresh();
      setNotice(editing ? "Catalog item updated." : "Catalog item added.");
    } catch (e) {
      markWriteFailed(e);
      setNotice(e.message);
    }
  };
  const removeItem = async (id) => {
    if (
      !window.confirm(
        "Remove this catalog item? Existing rules that use it will remain for review.",
      )
    )
      return;
    markWriteStarted();
    try {
      await request(`/api/items/${id}`, { method: "DELETE" });
      await refresh();
    } catch (e) {
      markWriteFailed(e);
      setNotice(e.message);
    }
  };
  const saveRule = async (e) => {
    e.preventDefault();
    markWriteStarted();
    try {
      const method = ruleForm.id ? "PUT" : "POST";
      const url = ruleForm.id ? `/api/rules/${ruleForm.id}` : "/api/rules";
      await request(url, { method, body: JSON.stringify(ruleForm) });
      setShowRule(false);
      setRuleForm(null);
      await refresh();
      setNotice("Compatibility rule saved.");
    } catch (e) {
      markWriteFailed(e);
      setNotice(e.message);
    }
  };
  const removeRule = async (id) => {
    if (!window.confirm("Delete this compatibility rule?")) return;
    markWriteStarted();
    try {
      await request(`/api/rules/${id}`, { method: "DELETE" });
      await refresh();
    } catch (e) {
      markWriteFailed(e);
      setNotice(e.message);
    }
  };
  const categoryField = (key) =>
    FIELD_LABELS[key] ||
    data?.fields[key] ||
    key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  const categoryOptions = { ...CATEGORY_LABELS, ...(data?.categories || {}) };
  const categoryLabel = (key) =>
    categoryOptions[key] ||
    FIELD_LABELS[key] ||
    key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
  const filled = FIELD_KEYS.filter((k) => selection[k]).length;
  const shownItems = (data?.items || []).filter((i) =>
    `${i.name} ${categoryLabel(i.category)}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  );
  if (!data)
    return (
      <div className="loading">
        <p>Opening your hardware library…</p>
        {notice && <p className="error-text">{notice}</p>}
      </div>
    );
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
          <button
            className={`nav-item ${page === "verify" ? "active" : ""}`}
            onClick={() => setPage("verify")}
          >
            <ClipboardCheck size={18} />
            <span>Compatibility check</span>
            <ArrowUpRight className="nav-arrow" size={15} />
          </button>
          <button
            className={`nav-item ${page === "library" ? "active" : ""}`}
            onClick={() => setPage("library")}
          >
            <Library size={18} />
            <span>Hardware library</span>
            <span className="nav-count">{data.items.length}</span>
          </button>
          <button
            className={`nav-item ${page === "rules" ? "active" : ""}`}
            onClick={() => setPage("rules")}
          >
            <Layers3 size={18} />
            <span>Compatibility rules</span>
            <span className="nav-count">{data.rules.length}</span>
          </button>
          <button
            className={`nav-item ${page === "research" ? "active" : ""}`}
            onClick={() => setPage("research")}
          >
            <BookOpenText size={18} />
            <span>Compatibility research</span>
            <span className="nav-count">{data.researchNotes.length}</span>
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="system-card">
            <span
              className={`live-dot ${databaseState === "offline" ? "is-offline" : databaseState === "saving" ? "is-saving" : ""}`}
            />
            <div>
              <b>Local database</b>
              <small>
                {databaseState === "connected"
                  ? "SQLite · connected"
                  : databaseState === "saving"
                    ? "SQLite · saving changes"
                    : databaseState === "offline"
                      ? "SQLite · unavailable"
                      : "SQLite · connecting"}
              </small>
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
              onClick={toggleTheme}
              aria-label={themeTitle}
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
              {databaseStatusText}
            </span>
          </div>
        </header>
        {notice && (
          <button className="toast" onClick={() => setNotice("")}>
            {notice}
            <X size={15} />
          </button>
        )}
        {page === "verify" && (
          <section className="content">
            <div className="page-heading">
              <div>
                <h1>Will these work together?</h1>
                <p>
                  Describe the opening and hardware. We’ll check it against your
                  verified combinations.
                </p>
              </div>
              <button
                className="button button-quiet"
                onClick={() => {
                  setSelection(EMPTY);
                  setResult(null);
                }}
              >
                <RefreshCw size={15} />
                Reset
              </button>
            </div>
            <div className="verify-grid">
              <div className="form-panel">
                <div className="section-heading">
                  <div className="section-icon">
                    <DoorOpen size={18} />
                  </div>
                  <div>
                    <h2>Door &amp; hardware setup</h2>
                    <p>Enter the details available for this opening.</p>
                  </div>
                  <span className="step-chip">
                    {filled} / {FIELD_KEYS.length} SET
                  </span>
                </div>
                <div className="field-groups">
                  {FIELD_GROUPS.map((group) => (
                    <section className="field-group" key={group.title}>
                      <div className="field-group-heading">
                        <h3>{group.title}</h3>
                        <p>{group.description}</p>
                      </div>
                      <div className="fields-grid">
                        {group.fields.map((key) => (
                          <label className="field" key={key}>
                            <span>
                              {categoryField(key)}
                              {[
                                "door_material",
                                "frame_material",
                                "strike",
                                "operator",
                                "proposed_hardware",
                              ].includes(key) && <i>*</i>}
                            </span>
                            <div className="select-wrap">
                              <select
                                value={selection[key]}
                                onChange={(e) =>
                                  setSelection({
                                    ...selection,
                                    [key]: e.target.value,
                                  })
                                }
                              >
                                <option value="">
                                  Select {categoryField(key).toLowerCase()}
                                </option>
                                {options(key).map((opt) => (
                                  <option key={opt} value={opt}>
                                    {opt}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown size={15} />
                            </div>
                          </label>
                        ))}
                      </div>
                    </section>
                  ))}
                </div>
                <div className="form-footer">
                  <span>
                    <CircleHelp size={14} /> More details can improve match
                    accuracy.
                  </span>
                  <button
                    className="button button-primary"
                    onClick={check}
                    disabled={checking}
                  >
                    {checking ? (
                      <>
                        <RefreshCw className="spin" size={16} />
                        Checking
                      </>
                    ) : (
                      <>
                        Check compatibility <ArrowUpRight size={16} />
                      </>
                    )}
                  </button>
                </div>
              </div>
              <div className="result-panel">
                {!result ? (
                  <div className="empty-result">
                    <div className="result-art">
                      <div className="art-orbit orbit-one" />
                      <div className="art-orbit orbit-two" />
                      <div className="art-center">
                        <Settings2 size={25} />
                      </div>
                      <div className="art-node node-top">
                        <Layers3 size={15} />
                      </div>
                      <div className="art-node node-left">
                        <DoorOpen size={15} />
                      </div>
                      <div className="art-node node-right">
                        <Activity size={15} />
                      </div>
                    </div>
                    <div className="result-kicker">COMPATIBILITY REPORT</div>
                    <h3>Ready when you are</h3>
                    <p>
                      Run a check to see what your library knows about this
                      combination.
                    </p>
                    <div className="rule-stat">
                      <span className="stat-icon">
                        <ShieldCheck size={17} />
                      </span>
                      <span>
                        <b>{data.rules.length} verified combinations</b>
                        <small>In your company library</small>
                      </span>
                      <ArrowUpRight size={15} />
                    </div>
                  </div>
                ) : (
                  <div className={`result-content status-${result.status}`}>
                    <div className="result-symbol">
                      {result.status === "compatible" ? (
                        <Check size={25} />
                      ) : result.status === "review" ? (
                        <CircleHelp size={25} />
                      ) : (
                        <Search size={25} />
                      )}
                    </div>
                    <div className="result-kicker">COMPATIBILITY REPORT</div>
                    <h3>
                      {result.status === "compatible"
                        ? "Combination verified"
                        : result.status === "review"
                          ? "Review required"
                          : "Not yet verified"}
                    </h3>
                    <p>
                      {result.status === "compatible"
                        ? "A matching record was found in your verified library."
                        : result.message}
                    </p>
                    {result.rule && (
                      <div className="matched-rule">
                        <small>MATCHED RULE</small>
                        <b>{result.rule.name}</b>
                        {result.rule.notes && <span>{result.rule.notes}</span>}
                      </div>
                    )}
                    {result.rules &&
                      result.rules.map((r) => (
                        <div className="matched-rule" key={r.id}>
                          <small>RECORD TO REVIEW</small>
                          <b>{r.name}</b>
                        </div>
                      ))}
                    <button
                      className="text-link"
                      onClick={() => setPage("rules")}
                    >
                      Review compatibility rules <ArrowUpRight size={14} />
                    </button>
                  </div>
                )}
              </div>
            </div>
            <div className="footnote">
              <ShieldCheck size={15} />
              <span>
                Results only reflect combinations explicitly recorded in your
                library. Always follow manufacturer instructions and applicable
                codes.
              </span>
              <span className="footnote-mark">
                PRO SECURITY CONTROLS&nbsp; / &nbsp;VERIFICATION
              </span>
            </div>
          </section>
        )}
        {page === "library" && (
          <section className="content library-page">
            <div className="page-heading">
              <div>
                <h1>Hardware library</h1>
                <p>Keep your company’s hardware vocabulary in one place.</p>
              </div>
              <span className="total-pill">{data.items.length} ITEMS</span>
            </div>
            <div className="library-layout">
              <div className="form-panel add-panel">
                <div className="section-heading">
                  <div className="section-icon">
                    {itemForm.id ? <Pencil size={17} /> : <Plus size={18} />}
                  </div>
                  <div>
                    <h2>
                      {itemForm.id ? "Edit catalog item" : "Add catalog item"}
                    </h2>
                    <p>Make an item available in setup checks.</p>
                  </div>
                </div>
                <form onSubmit={addItem} className="add-form">
                  <label className="field">
                    <span>Category</span>
                    <div className="select-wrap">
                      <select
                        value={itemForm.category}
                        onChange={(e) =>
                          setItemForm({ ...itemForm, category: e.target.value })
                        }
                      >
                        {Object.entries(categoryOptions).map(([k, v]) => (
                          <option value={k} key={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                      <ChevronDown size={15} />
                    </div>
                  </label>
                  <label className="field">
                    <span>Item name</span>
                    <input
                      required
                      value={itemForm.name}
                      placeholder="e.g. Electric latch retraction"
                      onChange={(e) =>
                        setItemForm({ ...itemForm, name: e.target.value })
                      }
                    />
                  </label>
                  <label className="field">
                    <span>
                      Notes <em>OPTIONAL</em>
                    </span>
                    <textarea
                      value={itemForm.notes}
                      placeholder="Brand, model, or details"
                      onChange={(e) =>
                        setItemForm({ ...itemForm, notes: e.target.value })
                      }
                    />
                  </label>
                  <div className="form-actions">
                    <button className="button button-primary" type="submit">
                      {itemForm.id ? <Check size={16} /> : <Plus size={16} />}
                      {itemForm.id ? "Save changes" : "Add to library"}
                    </button>
                    {itemForm.id && (
                      <button
                        className="button button-quiet"
                        type="button"
                        onClick={() =>
                          setItemForm({
                            category: "door_material",
                            name: "",
                            notes: "",
                          })
                        }
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </form>
              </div>
              <div className="catalog-panel">
                <div className="catalog-toolbar">
                  <div>
                    <h2>Catalog</h2>
                    <p>Items used in hardware checks and rules.</p>
                  </div>
                  <div className="searchbox">
                    <Search size={15} />
                    <input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Search items"
                    />
                  </div>
                </div>
                <div className="category-chips">
                  {Object.entries(categoryOptions).map(([k, v]) => (
                    <span key={k}>
                      {v}
                      <b>{itemCounts[k] || 0}</b>
                    </span>
                  ))}
                </div>
                <div className="item-list">
                  {shownItems.map((item) => (
                    <div className="item-row" key={item.id}>
                      <div className="item-symbol">
                        <Layers3 size={16} />
                      </div>
                      <div className="item-info">
                        <b>{item.name}</b>
                        <span>
                          {categoryLabel(item.category)}
                          {item.notes ? ` · ${item.notes}` : ""}
                        </span>
                      </div>
                      <button
                        className="icon-button"
                        title="Edit item"
                        onClick={() => setItemForm({ ...item })}
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        className="icon-button danger-hover"
                        title="Remove item"
                        onClick={() => removeItem(item.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                  {shownItems.length === 0 && (
                    <div className="no-items">No items match your search.</div>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}
        {page === "rules" && (
          <section className="content rules-page">
            <div className="page-heading">
              <div>
                <h1>Compatibility rules</h1>
                <p>
                  Document combinations your team has confirmed in the field.
                </p>
              </div>
              <button
                className="button button-primary"
                onClick={() => {
                  setRuleForm({
                    name: "",
                    requirements: { ...EMPTY },
                    notes: "",
                  });
                  setShowRule(true);
                }}
              >
                <FilePlus2 size={16} />
                Add verified rule
              </button>
            </div>
            <div className="rule-banner">
              <div className="banner-icon">
                <ShieldCheck size={18} />
              </div>
              <div>
                <b>Every record strengthens future checks.</b>
                <span>
                  Checks use the most specific matching rule. If nothing
                  matches, the result stays unverified.
                </span>
              </div>
              <span className="total-pill">{data.rules.length} RULES</span>
            </div>
            <div className="rules-list">
              {data.rules.map((rule, n) => (
                <article className="rule-card" key={rule.id}>
                  <div className="rule-card-top">
                    <div className="rule-number">
                      {String(data.rules.length - n).padStart(2, "0")}
                    </div>
                    <div className="rule-title">
                      <h3>{rule.name}</h3>
                      <span>
                        <span className="live-dot" /> VERIFIED RECORD{" "}
                        <span className="tiny-divider">·</span>{" "}
                        {
                          Object.values(rule.requirements).filter(Boolean)
                            .length
                        }{" "}
                        CONDITIONS
                      </span>
                    </div>
                    <button
                      className="button button-small"
                      onClick={() => {
                        setRuleForm({
                          ...rule,
                          requirements: { ...EMPTY, ...rule.requirements },
                        });
                        setShowRule(true);
                      }}
                    >
                      Edit rule
                    </button>
                    <button
                      className="icon-button danger-hover"
                      title="Delete rule"
                      onClick={() => removeRule(rule.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="rule-tags">
                    {Object.entries(rule.requirements)
                      .filter(([, v]) => v)
                      .map(([k, v]) => (
                        <span className="rule-tag" key={k}>
                          <small>{categoryField(k)}</small>
                          {v}
                        </span>
                      ))}
                  </div>
                  {rule.notes && <div className="rule-note">{rule.notes}</div>}
                </article>
              ))}
              {data.rules.length === 0 && (
                <div className="no-items">
                  No rules yet. Add one once your team has confirmed a
                  combination.
                </div>
              )}
            </div>
          </section>
        )}
        {page === "research" && (
          <section className="content research-page">
            <div className="page-heading">
              <div>
                <h1>Compatibility research</h1>
                <p>
                  Source-backed leads to guide product research. These notes are
                  not verified compatibility decisions.
                </p>
              </div>
              <span className="total-pill">
                {data.researchNotes.length} SOURCE NOTES
              </span>
            </div>
            <div className="research-banner">
              <div className="banner-icon">
                <CircleHelp size={18} />
              </div>
              <div>
                <b>Research lead only · not an approval</b>
                <span>
                  Use exact manufacturer documentation and field verification
                  before marking a combination compatible.
                </span>
              </div>
            </div>
            <div className="research-list">
              {data.researchNotes.map((note) => (
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
                  <div className="research-components">
                    {note.related_components}
                  </div>
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
        )}
      </main>
      {showRule && (
        <div className="modal-backdrop" onClick={() => setShowRule(false)}>
          <div className="rule-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <div>
                <span className="eyebrow">RULE EDITOR</span>
                <h2>
                  {ruleForm.id ? "Edit verified rule" : "Add verified rule"}
                </h2>
                <p>Set the combination your team has confirmed.</p>
              </div>
              <button
                className="icon-button"
                onClick={() => setShowRule(false)}
              >
                <X size={19} />
              </button>
            </div>
            <form onSubmit={saveRule}>
              <label className="field">
                <span>Rule name</span>
                <input
                  required
                  value={ruleForm.name}
                  placeholder="e.g. Lobby entry · wood door"
                  onChange={(e) =>
                    setRuleForm({ ...ruleForm, name: e.target.value })
                  }
                />
              </label>
              <div className="modal-fields">
                {FIELD_KEYS.map((key) => (
                  <label className="field" key={key}>
                    <span>{categoryField(key)}</span>
                    <div className="select-wrap">
                      <select
                        value={ruleForm.requirements[key] || ""}
                        onChange={(e) =>
                          setRuleForm({
                            ...ruleForm,
                            requirements: {
                              ...ruleForm.requirements,
                              [key]: e.target.value,
                            },
                          })
                        }
                      >
                        <option value="">Any / unspecified</option>
                        {options(key).map((opt) => (
                          <option key={opt}>{opt}</option>
                        ))}
                      </select>
                      <ChevronDown size={15} />
                    </div>
                  </label>
                ))}
              </div>
              <label className="field">
                <span>
                  Field notes <em>OPTIONAL</em>
                </span>
                <textarea
                  value={ruleForm.notes}
                  placeholder="Installation notes, source, or conditions"
                  onChange={(e) =>
                    setRuleForm({ ...ruleForm, notes: e.target.value })
                  }
                />
              </label>
              <div className="modal-actions">
                <button
                  className="button button-quiet"
                  type="button"
                  onClick={() => setShowRule(false)}
                >
                  Cancel
                </button>
                <button className="button button-primary" type="submit">
                  <Check size={16} />
                  Save verified rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);

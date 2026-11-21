import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faMoon, faSun } from "@fortawesome/free-solid-svg-icons";
import {
  ArrowUpRight,
  ArrowLeft,
  ArrowRight,
  Building2,
  BookOpenText,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Download,
  ExternalLink,
  FileText,
  FilePlus2,
  Home,
  Layers3,
  Library,
  Maximize2,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
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
  conditions: {},
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
    id: "wc17-six-model-tuple",
    title: "Six-model WC17 control + power assembly",
    description:
      "Loads the exact six-model CX-WC17SLVR tuple with Camden's specified CX-PS13 supply and CX-TRX-4024 transformer.",
    expected: "Documented compatible",
    kind: "compatible",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC17SLVR"],
      ["controller", "Camden Controls", "CX-33"],
      ["activation_device", "Camden Controls", "CM-8536VR"],
      ["activation_device", "Camden Controls", "CM-221"],
      ["power_supply", "Camden Controls", "CX-PS13"],
      ["power_supply", "Camden Controls", "CX-TRX-4024"],
    ],
  },
  {
    id: "wc16-six-device-tuple",
    title: "Six-model restroom kit assembly",
    description:
      "Tests the documented CX-WC16-PS-M1 setup with CX-33, strike, and three activation devices.",
    expected: "Documented compatible tuple",
    kind: "compatible",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC16-PS-M1"],
      ["controller", "Camden Controls", "CX-33"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
      ["activation_device", "Camden Controls", "CM-331/42WS-SGLR"],
      ["activation_device", "Camden Controls", "CM-325/42WS"],
      ["activation_device", "Camden Controls", "CM-331/43S-SGLR"],
    ],
  },
  {
    id: "wc16-nine-device-emergency-tuple",
    title: "Nine-model restroom + emergency call assembly",
    description:
      "Tests the documented CX-WC16-PS-M1 emergency-call configuration with its relay, strike, switches, call system, and annunciators.",
    expected: "Documented compatible tuple",
    kind: "compatible",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC16-PS-M1"],
      ["controller", "Camden Controls", "60-40E035"],
      ["emergency_call", "Camden Controls", "CX-WEC10-K2"],
      ["alarm", "Camden Controls", "CM-AF141SO"],
      ["alarm", "Camden Controls", "CM-AF540SO"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
      ["activation_device", "Camden Controls", "CM-331/42WS-SGLR"],
      ["activation_device", "Camden Controls", "CM-325/42WS"],
      ["activation_device", "Camden Controls", "CM-331/43S-SGLR"],
    ],
  },
  {
    id: "wc17-operator-extension",
    title: "Five-model restroom kit + operator",
    description:
      "The documented CX-WC17SLVR tuple with its specified power chain, plus an LCN 9540 operator. The added operator interaction is not established by the kit manual.",
    expected: "Test only · added interaction unverified",
    kind: "unverified",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC17SLVR"],
      ["controller", "Camden Controls", "CX-33"],
      ["activation_device", "Camden Controls", "CM-8536VR"],
      ["activation_device", "Camden Controls", "CM-221"],
      ["power_supply", "Camden Controls", "CX-PS13"],
      ["power_supply", "Camden Controls", "CX-TRX-4024"],
      ["automatic_operator", "LCN", "9540"],
    ],
  },
  {
    id: "wc16-operator-extension",
    title: "Seven-model restroom kit + operator",
    description:
      "A documented six-model CX-WC16-PS-M1 tuple plus an LCN 9540 operator to show how an unverified extra component affects the estimate.",
    expected: "Test only · added interaction unverified",
    kind: "unverified",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC16-PS-M1"],
      ["controller", "Camden Controls", "CX-33"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
      ["activation_device", "Camden Controls", "CM-331/42WS-SGLR"],
      ["activation_device", "Camden Controls", "CM-325/42WS"],
      ["activation_device", "Camden Controls", "CM-331/43S-SGLR"],
      ["automatic_operator", "LCN", "9540"],
    ],
  },
  {
    id: "wc16-contact-extension",
    title: "Ten-model emergency-call system + door contact",
    description:
      "A documented nine-model restroom and emergency-call tuple plus a CX-MDA contact. The extra contact is a test-only, unverified addition.",
    expected: "Test only · added interaction unverified",
    kind: "unverified",
    products: [
      ["washroom_control", "Camden Controls", "CX-WC16-PS-M1"],
      ["controller", "Camden Controls", "60-40E035"],
      ["emergency_call", "Camden Controls", "CX-WEC10-K2"],
      ["alarm", "Camden Controls", "CM-AF141SO"],
      ["alarm", "Camden Controls", "CM-AF540SO"],
      ["electric_strike", "Camden Controls", "CX-ED1799L-8"],
      ["activation_device", "Camden Controls", "CM-331/42WS-SGLR"],
      ["activation_device", "Camden Controls", "CM-325/42WS"],
      ["activation_device", "Camden Controls", "CM-331/43S-SGLR"],
      ["door_contact", "Camden Controls", "CX-MDA"],
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
    label: "Power supplies",
    categories: ["power_supply"],
  },
  {
    label: "Controls & washroom",
    categories: [
      "controller",
      "access_control",
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

const appPages = new Set(["home", "check", "projects", "products", "coverage", "rules", "research"]);
function readAppRoute() {
  const path = window.location.hash.replace(/^#\/?/, "").split("?")[0];
  const [candidate, projectId] = path.split("/");
  const page = appPages.has(candidate) ? candidate : "home";
  return { page, projectId: page === "projects" && /^\d+$/.test(projectId || "") ? Number(projectId) : null };
}

export default function ModelApp() {
  const [data, setData] = useState(null);
  const [coverage, setCoverage] = useState(null);
  const [page, setPageState] = useState(() => readAppRoute().page);
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
  const [exampleEstimates, setExampleEstimates] = useState({});
  const [selectedIds, setSelectedIds] = useState([]);
  const [opening, setOpening] = useState(emptyOpening);
  const [openingPreview, setOpeningPreview] = useState(null);
  const [checkResult, setCheckResult] = useState(null);
  const [reportExpanded, setReportExpanded] = useState(false);
  const [reportPanelVisible, setReportPanelVisible] = useState(false);
  const reportDialogRef = useRef(null);
  const reportTriggerRef = useRef(null);
  const reportWasExpanded = useRef(false);
  const [checking, setChecking] = useState(false);
  const [importing, setImporting] = useState(false);
  const [projects, setProjects] = useState([]);
  const [projectsLoaded, setProjectsLoaded] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true);
  const [deletingProjectId, setDeletingProjectId] = useState(null);
  const [confirmDeleteProjectId, setConfirmDeleteProjectId] = useState(null);
  const [refreshingProjects, setRefreshingProjects] = useState(false);
  const [projectsRefreshedAt, setProjectsRefreshedAt] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [projectRun, setProjectRun] = useState(null);
  const [selectedDoorId, setSelectedDoorId] = useState(null);
  const [doorSearch, setDoorSearch] = useState("");
  const [hardwareSetSearch, setHardwareSetSearch] = useState("");
  const [hardwareSetsExpanded, setHardwareSetsExpanded] = useState(false);
  const [projectBusy, setProjectBusy] = useState(false);
  const [scheduleFile, setScheduleFile] = useState(null);
  const [projectForm, setProjectForm] = useState({ name: "", project_code: "", revision_label: "" });
  const [matchQueries, setMatchQueries] = useState({});
  const [editingMatchItemId, setEditingMatchItemId] = useState(null);
  const [manualDoorForm, setManualDoorForm] = useState(null);
  const [doorNumberForm, setDoorNumberForm] = useState(null);
  const [manualSetForm, setManualSetForm] = useState(null);
  const [manualItemForm, setManualItemForm] = useState(null);
  const [sourcePageText, setSourcePageText] = useState(null);
  const [refreshingCatalog, setRefreshingCatalog] = useState(false);
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
  const loadCoverage = useCallback(async (options = {}) => {
    const params = new URLSearchParams({
      page: String(options.page || 1),
      page_size: "50",
      status: options.status || "applicable",
      q: options.query || "",
    });
    try {
      const result = await api(`/api/coverage?${params}`);
      setCoverage(result);
    } catch (error) {
      setNotice(error.message);
    }
  }, []);
  const loadProjects = async () => {
    const result = await api("/api/projects");
    setProjects(result.projects || []);
    setProjectsLoaded(true);
  };
  const refreshProjects = async () => {
    setRefreshingProjects(true);
    try {
      await loadProjects();
      setProjectsRefreshedAt(new Date());
      setNotice("Project list refreshed.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setRefreshingProjects(false);
    }
  };
  const loadProject = async (projectId) => {
    const result = await api(`/api/projects/${projectId}`);
    setProjectData(result);
    setSelectedDoorId((current) =>
      result.doors.some((door) => door.id === current)
        ? current
        : result.doors[0]?.id || null,
    );
    setProjectRun(null);
    setSourcePageText(null);
  };
  const setPage = (nextPage) => {
    setPageState(nextPage);
    if (appPages.has(nextPage)) {
      const nextHash = `#/${nextPage}`;
      if (window.location.hash !== nextHash) window.history.pushState(null, "", nextHash);
    }
  };
  const openProject = async (projectId) => {
    await loadProject(projectId);
    const nextHash = `#/projects/${projectId}`;
    if (window.location.hash !== nextHash) window.history.pushState(null, "", nextHash);
    setPageState("projects");
  };
  const deleteProject = async (project) => {
    setDeletingProjectId(project.id);
    try {
      await api(`/api/projects/${project.id}`, { method: "DELETE" });
      if (projectData?.project.id === project.id) setProjectData(null);
      setProjectRun(null);
      setConfirmDeleteProjectId(null);
      await loadProjects();
      setNotice(`Deleted project “${project.name}”. You can now import the schedule again.`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setDeletingProjectId(null);
    }
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
    const syncRoute = () => {
      const route = readAppRoute();
      setPageState(route.page);
      if (route.page === "projects" && route.projectId) {
        loadProject(route.projectId).catch((error) => setNotice(error.message));
      } else {
        setProjectData(null);
        setProjectRun(null);
        setSourcePageText(null);
      }
    };
    window.addEventListener("hashchange", syncRoute);
    window.addEventListener("popstate", syncRoute);
    if (!window.location.hash) window.history.replaceState(null, "", "#/home");
    const initialRoute = readAppRoute();
    if (initialRoute.page === "projects" && initialRoute.projectId) {
      loadProject(initialRoute.projectId).catch((error) => setNotice(error.message));
    }
    return () => {
      window.removeEventListener("hashchange", syncRoute);
      window.removeEventListener("popstate", syncRoute);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = activeTheme;
    window.localStorage.setItem("door-hardware-theme", themeMode);
  }, [activeTheme, themeMode]);

  useEffect(() => {
    if (page === "coverage" || (page === "home" && projectsLoaded && projects.length > 0))
      loadCoverage().catch((error) => setNotice(error.message));
  }, [page, data?.products?.length, projectsLoaded, projects.length, loadCoverage]);

  useEffect(() => {
    if (page === "projects" || page === "home") loadProjects().catch((error) => setNotice(error.message));
  }, [page]);

  useEffect(() => {
    if (!reportExpanded) {
      if (reportWasExpanded.current && page === "check")
        reportTriggerRef.current?.focus();
      reportWasExpanded.current = false;
      return undefined;
    }
    reportWasExpanded.current = true;
    const dialog = reportDialogRef.current;
    dialog?.focus();
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setReportExpanded(false);
        return;
      }
      if (event.key !== "Tab" || !dialog) return;
      const focusable = dialog.querySelectorAll(
        'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [reportExpanded, page]);

  const categories = data?.productCategories || {};
  const productList = data?.products || [];
  const activeProducts = productList.filter((product) => product.active);
  const evidenceSources = useMemo(() => {
    const records = [
      ...productList,
      ...(data?.assertions || []),
      ...(data?.compatibilityRules || []),
      ...(data?.researchNotes || []),
    ];
    const unique = new Map();
    records.forEach((record) => {
      if (record?.source_url) {
        unique.set(record.source_url, {
          source_title: record.source_title || record.title || record.source_url,
          source_url: record.source_url,
        });
      }
    });
    return [...unique.values()].sort((a, b) =>
      a.source_title.localeCompare(b.source_title),
    );
  }, [productList, data?.assertions, data?.compatibilityRules, data?.researchNotes]);
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
    if (!showExamples || !data?.products) return undefined;

    let current = true;
    const scenarios = exampleScenarios.map((scenario) => {
      const products = scenario.products.map(([category, manufacturer, model]) =>
        activeProducts.find(
          (product) =>
            product.category === category &&
            product.manufacturer === manufacturer &&
            product.model === model,
        ),
      );
      return { scenario, products };
    });

    setExampleEstimates(
      Object.fromEntries(scenarios.map(({ scenario }) => [scenario.id, { loading: true }])),
    );

    Promise.all(
      scenarios.map(async ({ scenario, products }) => {
        if (products.some((product) => !product))
          return [scenario.id, { error: "Products unavailable" }];
        const openingDetails = Object.fromEntries(
          Object.entries(scenario.opening || {}).map(([key, value]) => [
            key,
            ["width_in", "height_in", "weight_lb", "reveal_depth_mm"].includes(key)
              ? Number(value)
              : value,
          ]),
        );
        try {
          const result = await api("/api/compatibility/check", {
            method: "POST",
            body: JSON.stringify({
              product_ids: products.map((product) => product.id),
              ...(Object.keys(openingDetails).length && { opening: openingDetails }),
            }),
          });
          return [scenario.id, { estimate: result.estimate }];
        } catch (error) {
          return [scenario.id, { error: error.message }];
        }
      }),
    ).then((entries) => {
      if (current) setExampleEstimates(Object.fromEntries(entries));
    });

    return () => {
      current = false;
    };
  }, [showExamples, data?.products]);

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
  const refreshLiveCatalog = async () => {
    setRefreshingCatalog(true);
    try {
      const result = await api("/api/catalog/refresh", { method: "POST" });
      await markSaved();
      const pagesWithListings = result.sources.filter((source) => source.status === "ok").length;
      setNotice(
        `Catalog refresh complete: ${result.products_added} added, ${result.products_refreshed} refreshed. ${pagesWithListings} of ${result.sources.length} pages returned listings; all remain unverified research leads.`,
      );
    } catch (error) {
      setDatabaseState("connected");
      setNotice(error.message);
    } finally {
      setRefreshingCatalog(false);
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
        conditions: assertionForm.conditions || {},
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
  const clearCheckResult = () => {
    setCheckResult(null);
    setReportExpanded(false);
  };
  const openSubsetAssertion = (productIds) => {
    const ids = [...productIds].sort((a, b) => a - b);
    const prior = (data?.assertions || []).find(
      (assertion) =>
        assertion.product_ids.length === ids.length &&
        [...assertion.product_ids].sort((a, b) => a - b).every((id, index) => id === ids[index]),
    );
    setAssertionForm(
      prior
        ? { ...prior, conditions: prior.conditions || {} }
        : { ...emptyAssertion, product_ids: ids },
    );
    setShowAssertion(true);
  };
  const runCheck = async () => {
    setChecking(true);
    try {
      const result = await api("/api/compatibility/check", {
        method: "POST",
        body: JSON.stringify({
          product_ids: selectedIds,
          opening: openingContext,
        }),
      });
      setCheckResult(result);
      setReportPanelVisible(true);
      setReportExpanded(true);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setChecking(false);
    }
  };

  const uploadSchedule = async (event) => {
    event.preventDefault();
    const fileInput = event.currentTarget.querySelector('input[type="file"]');
    if (!scheduleFile || !projectForm.name.trim()) {
      setNotice("Enter a project name and choose a hardware-schedule PDF.");
      return;
    }
    setProjectBusy(true);
    setDatabaseState("saving");
    try {
      const bytes = new Uint8Array(await scheduleFile.arrayBuffer());
      let binary = "";
      const chunkSize = 0x8000;
      for (let index = 0; index < bytes.length; index += chunkSize)
        binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
      const result = await api("/api/projects/import-schedule", {
        method: "POST",
        body: JSON.stringify({
          ...projectForm,
          filename: scheduleFile.name,
          file_base64: window.btoa(binary),
        }),
      });
      await loadProjects();
      await openProject(result.project_id);
      await loadData();
      setProjectForm({ name: "", project_code: "", revision_label: "" });
      setScheduleFile(null);
      setNotice(`Imported ${result.counts.pages} pages: ${result.counts.doors} door rows, ${result.counts.sets} sets, ${result.counts.items} items. Review flagged rows before checking.`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setProjectBusy(false);
      setDatabaseState("connected");
      if (fileInput) fileInput.value = "";
    }
  };
  const saveScheduleMatch = async (itemId, productId, reviewStatus = "confirmed") => {
    try {
      await api("/api/scheduled-items/matches", {
        method: "POST",
        body: JSON.stringify({ scheduled_item_id: itemId, product_id: productId, review_status: reviewStatus }),
      });
      await loadProject(projectData.project.id);
      setEditingMatchItemId(null);
      setNotice(reviewStatus === "confirmed"
        ? "Catalog match confirmed for this schedule line."
        : "Confirmation removed. The catalog match remains an unconfirmed suggestion.");
    } catch (error) {
      setNotice(error.message);
    }
  };
  const addManualDoor = async (event) => {
    event.preventDefault();
    try {
      await api("/api/projects/doors", {
        method: "POST",
        body: JSON.stringify({ project_id: projectData.project.id, ...manualDoorForm }),
      });
      await loadProject(projectData.project.id);
      setManualDoorForm(null);
    } catch (error) {
      setNotice(error.message);
    }
  };
  const saveDoorNumber = async (event) => {
    event.preventDefault();
    if (!doorNumberForm || !projectData) return;
    try {
      await api(`/api/scheduled-doors/${doorNumberForm.id}`, {
        method: "PUT",
        body: JSON.stringify({
          door_number: doorNumberForm.door_number,
          door_number_status: doorNumberForm.door_number_status,
        }),
      });
      await loadProject(projectData.project.id);
      setDoorNumberForm(null);
      setNotice("Door number review saved.");
    } catch (error) {
      setNotice(error.message);
    }
  };
  const addManualSet = async (event) => {
    event.preventDefault();
    try {
      await api("/api/projects/sets", {
        method: "POST",
        body: JSON.stringify({ project_id: projectData.project.id, ...manualSetForm }),
      });
      await loadProject(projectData.project.id);
      setManualSetForm(null);
    } catch (error) {
      setNotice(error.message);
    }
  };
  const addManualItem = async (event) => {
    event.preventDefault();
    try {
      await api(`/api/hardware-sets/${manualItemForm.hardware_set_id}/items`, {
        method: "POST",
        body: JSON.stringify(manualItemForm),
      });
      await loadProject(projectData.project.id);
      setManualItemForm(null);
    } catch (error) {
      setNotice(error.message);
    }
  };
  const showSourcePage = async (pageNumber) => {
    const revision = projectData.revisions.find((item) => item.id === projectData.revision_id);
    if (!revision || !pageNumber) return;
    try {
      const result = await api(`/api/schedule-revisions/${revision.id}/pages?page=${pageNumber}`);
      setSourcePageText(result);
    } catch (error) {
      setNotice(error.message);
    }
  };
  const runProjectVerification = async () => {
    if (!projectData) return;
    setProjectBusy(true);
    try {
      const created = await api(`/api/projects/${projectData.project.id}/verify`, {
        method: "POST",
        body: JSON.stringify({ run_name: `Review ${new Date().toLocaleString()}` }),
      });
      const report = await api(`/api/verification-runs/${created.run_id}`);
      await loadProject(projectData.project.id);
      setProjectRun(report);
      setNotice("Door verification run saved to this project.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setProjectBusy(false);
    }
  };
  const loadProjectRun = async (runId) => {
    try {
      const result = await api(`/api/verification-runs/${runId}`);
      setProjectRun(result);
    } catch (error) {
      setNotice(error.message);
    }
  };
  const exportProjectRun = (format) => {
    if (!projectRun) return;
    let blob, extension;
    if (format === "json") {
      blob = new Blob([JSON.stringify(projectRun, null, 2)], { type: "application/json" });
      extension = "json";
    } else {
      const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
      const rows = [["Door", "Hardware set", "Status", "Message", "Scheduled PDF page", "Products", "Findings", "Evidence URLs"]];
      projectRun.doors.forEach((door) => {
        const result = door.result || {};
        rows.push([
          door.door_number,
          door.heading_number,
          result.status,
          result.message,
          door.source_page,
          (result.products || []).map((product) => displayName(product)).join("; "),
          (result.findings || []).map((finding) => finding.rationale).join(" | "),
          (result.findings || []).map((finding) => finding.source_url).filter(Boolean).join("; "),
        ]);
      });
      blob = new Blob([rows.map((row) => row.map(quote).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
      extension = "csv";
    }
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${projectData.project.project_code || projectData.project.name.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "")}-verification-run-${projectRun.run.id}.${extension}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const searchProductCompatibility = (product) => {
    const exactModel = `"${displayName(product)}"`;
    const query = `${exactModel} ("compatible with" OR "works with" OR compatibility OR interoperability OR wiring) ("minimum door width" OR "maximum door width" OR "door width" OR "door height" OR "maximum weight" OR "door thickness" OR "door material" OR "frame material" OR voltage OR mounting OR interface) manufacturer specifications datasheet`;
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
    window.open(searchUrl, "_blank", "noopener,noreferrer");
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
    clearCheckResult();
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
  const totalScheduledDoors = projects.reduce((total, project) => total + Number(project.door_count || 0), 0);
  const totalRevisions = projects.reduce((total, project) => total + Number(project.revision_count || 0), 0);
  const latestProject = projects[0] || null;
  const projectDoors = projectData?.doors || [];
  const visibleProjectDoors = projectDoors.filter((door) =>
    `${door.door_number} ${door.heading_number} ${door.description}`.toLowerCase().includes(doorSearch.toLowerCase()),
  );
  const knownProjectDoors = visibleProjectDoors.filter((door) => door.door_number_status !== "unknown");
  const unknownProjectDoors = visibleProjectDoors.filter((door) => door.door_number_status === "unknown");
  const visibleHardwareSets = [...(projectData?.sets || [])]
    .filter((set) => `${set.set_code} ${set.description || ""}`.toLowerCase().includes(hardwareSetSearch.trim().toLowerCase()))
    .sort((a, b) => a.set_code.localeCompare(b.set_code, undefined, { numeric: true, sensitivity: "base" }));
  const selectedProjectDoor = visibleProjectDoors.find((door) => door.id === selectedDoorId) || visibleProjectDoors[0] || null;
  const selectedDoorIndex = visibleProjectDoors.findIndex((door) => door.id === selectedProjectDoor?.id);
  const selectedRunDoor = projectRun?.doors?.find((door) => door.scheduled_door_id === selectedProjectDoor?.id);
  const latestRevision = projectData?.revisions?.find((revision) => revision.id === projectData.revision_id);
  const renderProjectDoorRow = (door) => {
    const runDoor = projectRun?.doors?.find((result) => result.scheduled_door_id === door.id);
    const selected = selectedProjectDoor?.id === door.id;
    const doorLabel = door.door_number_status === "unknown" ? "Unknown door number" : door.door_number;
    return <button key={door.id} className={`door-list-item ${selected ? "active" : ""} ${door.door_number_status === "unknown" ? "door-list-item-unknown" : ""}`} onClick={() => { setSelectedDoorId(door.id); setSourcePageText(null); setDoorNumberForm(null); }}>
      <strong>{doorLabel}</strong>
      <span className="door-list-status">{runDoor ? <StatusPill status={runDoor.result.status} /> : <span className="status-pending">{door.door_number_status === "unknown" ? "Unknown ID" : "Review"}</span>}</span>
      <small>{door.heading_number ? `Set ${door.heading_number}` : "Set not assigned"}{door.description ? ` · ${door.description}` : " · Description not parsed"}</small>
    </button>;
  };

  return (
    <div className={`app-shell${sidebarCollapsed ? " sidebar-collapsed" : ""}`}>
      <aside className="sidebar">
        <div className="brand">
          <div>
            <strong>Door Hardware Checker</strong>
            <span>by Pro Security Controls Inc.</span>
          </div>
          <strong className="brand-mark" aria-hidden="true">DHC</strong>
        </div>
        <button
          className="sidebar-toggle"
          type="button"
          aria-label={sidebarCollapsed ? "Expand navigation" : "Collapse navigation"}
          title={sidebarCollapsed ? "Expand navigation" : "Collapse navigation"}
          onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
        >
          {sidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
        </button>
        <nav>
          <NavItem
            active={page === "home"}
            onClick={() => { setProjectData(null); setProjectRun(null); setPage("home"); }}
            icon={<Home size={18} />}
            label="Home"
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "projects"}
            onClick={() => { setProjectData(null); setProjectRun(null); setPage("projects"); }}
            icon={<Building2 size={18} />}
            label="Projects"
            count={projects.length || undefined}
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "check"}
            onClick={() => setPage("check")}
            icon={<ClipboardCheck size={18} />}
            label="Compatibility check"
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "products"}
            onClick={() => setPage("products")}
            icon={<Library size={18} />}
            label="Product catalog"
            count={activeProducts.length}
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "coverage"}
            onClick={() => setPage("coverage")}
            icon={<Layers3 size={18} />}
            label="Compatibility coverage"
            count={coverage?.summary?.total}
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "rules"}
            onClick={() => setPage("rules")}
            icon={<FilePlus2 size={18} />}
            label="Rules & assertions"
            count={data.compatibilityRules.length + data.assertions.length}
            collapsed={sidebarCollapsed}
          />
          <NavItem
            active={page === "research"}
            onClick={() => setPage("research")}
            icon={<BookOpenText size={18} />}
            label="Compatibility research"
            count={data.researchNotes.length}
            collapsed={sidebarCollapsed}
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

        {page === "home" && (
          <section className="content home-page">
            <div className="home-heading">
              <h1>{projectsLoaded && projects.length === 0 ? "Welcome to Door Hardware Checker" : localTime.getHours() < 12 ? "Good morning" : localTime.getHours() < 18 ? "Good afternoon" : "Good evening"}</h1>
              <p>{projectsLoaded && projects.length === 0 ? "Bring in a schedule to start reviewing your door hardware." : "Your door hardware workspace at a glance."}</p>
            </div>
            <div className="home-hero">
              {latestProject ? (
                <>
                  <div>
                    <span className="home-eyebrow">PICK UP WHERE YOU LEFT OFF</span>
                    <h2>{latestProject.name}</h2>
                    <p>{latestProject.project_code || "No project code"} · {latestProject.revision_count} schedule revision{latestProject.revision_count === 1 ? "" : "s"} · {latestProject.door_count} scheduled doors</p>
                  </div>
                  <button className="button button-primary" onClick={() => openProject(latestProject.id).catch((error) => setNotice(error.message))}>Continue project <ArrowRight size={16} /></button>
                </>
              ) : (
                <>
                  <div>
                    <span className="home-eyebrow">GET STARTED</span>
                    <h2>{projectsLoaded ? "Start with a door schedule" : "Loading your projects…"}</h2>
                    <p>{projectsLoaded ? "Import a schedule to create your first project and review its hardware." : "Checking your local project workspace."}</p>
                  </div>
                  {projectsLoaded && <button className="button button-primary" onClick={() => setPage("projects")}><Upload size={15} /> Import schedule</button>}
                </>
              )}
            </div>
            {projectsLoaded && projects.length > 0 && <>
              <div className="home-metrics">
                <div className="home-metric"><span>Door rows across revisions</span><b>{totalScheduledDoors}</b></div>
                <div className="home-metric"><span>Schedule revisions</span><b>{totalRevisions}</b></div>
              </div>
              <div className="home-columns">
                <div className="home-projects">
                  <div className="home-section-heading"><h2>Recent projects</h2><button className="text-link-button" onClick={() => setPage("projects")}>All projects <ArrowUpRight size={14} /></button></div>
                  <div className="home-project-list">
                    {projects.slice(0, 3).map((project) => (
                      <button className="home-project-row" key={project.id} onClick={() => openProject(project.id).catch((error) => setNotice(error.message))}>
                        <span className="home-project-info"><b>{project.name}</b><small>{project.project_code || "No project code"} · {project.revision_count} revision{project.revision_count === 1 ? "" : "s"}</small></span>
                        <span className="home-project-doors"><b>{project.door_count}</b><small>doors</small></span>
                        <ArrowUpRight size={16} />
                      </button>
                    ))}
                  </div>
                </div>
                <aside className="home-side-panel">
                  <div className="home-section-heading"><h2>Coverage snapshot</h2></div>
                  <p>Product interactions represented in the catalog.</p>
                  <div className="home-coverage-numbers">
                    <div><b>{coverage?.summary?.assessed ?? "—"}</b><span>assessed</span></div>
                    <div><b>{coverage?.summary?.unverified ?? "—"}</b><span>unverified</span></div>
                  </div>
                  <button className="button button-quiet" onClick={() => setPage("coverage")}>View compatibility coverage <ArrowRight size={15} /></button>
                  <button className="home-quick-action" onClick={() => setPage("check")}><ClipboardCheck size={16} /><span><b>Quick compatibility check</b><small>Check exact product models</small></span><ArrowUpRight size={15} /></button>
                </aside>
              </div>
            </>}
            {projectsLoaded && projects.length === 0 && (
              <div className="home-first-run">
                <div className="home-first-run-heading">
                  <span className="home-eyebrow">YOUR FIRST PROJECT</span>
                  <h2>What happens next</h2>
                </div>
                <div className="home-first-run-steps">
                  <div><span>01</span><b>Import the schedule</b><p>Upload the door hardware schedule as a PDF.</p></div>
                  <div><span>02</span><b>Review the extraction</b><p>Check the doors and scheduled products the app identifies.</p></div>
                  <div><span>03</span><b>Run door checks</b><p>Match exact products and review documented compatibility.</p></div>
                </div>
                <button className="home-quick-action home-first-run-quick-check" onClick={() => setPage("check")}><ClipboardCheck size={16} /><span><b>Need to check products without a schedule?</b><small>Run a quick compatibility check by exact model.</small></span><ArrowRight size={15} /></button>
              </div>
            )}
          </section>
        )}

        {page === "check" && (
          <section className={`content model-check-page${reportPanelVisible ? "" : " report-panel-hidden"}`}>
            <div className="page-heading">
              <div>
                <h1>Verify Hardware Compatibility</h1>
                <p>
                  Select exact product models. The checker reports which
                  interactions are documented and which still need review.
                </p>
              </div>
              {!reportPanelVisible && (
                <button
                  className="button button-quiet report-show-button"
                  onClick={() => setReportPanelVisible(true)}
                >
                  <PanelRightOpen size={16} />
                  Show report panel
                </button>
              )}
            </div>
            <div className={`model-check-grid${reportPanelVisible ? "" : " report-hidden"}`}>
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
                    ref={reportTriggerRef}
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
                    clearCheckResult();
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
              {reportPanelVisible && <div className="result-panel assembly-result">
                <section className="selected-products-section">
                  <div className="selected-products-heading">
                    <div>
                      <h2>Selected products</h2>
                      <p>Components included in this check.</p>
                    </div>
                    <div className="report-sidebar-actions">
                      <span className="step-chip">
                        {selectedProducts.length} SELECTED
                      </span>
                      <button
                        className="button button-small"
                        onClick={() => checkResult && setReportExpanded(true)}
                        disabled={!checkResult}
                      >
                        <Maximize2 size={14} />
                        Expand report
                      </button>
                      <button
                        className="button button-small"
                        onClick={() => setReportPanelVisible(false)}
                        aria-label="Hide report sidebar"
                      >
                        <PanelRightClose size={14} />
                        Hide panel
                      </button>
                    </div>
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
                            clearCheckResult();
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
                      <h2 className="assembly-report-heading">Assembly report</h2>
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
                      onAssertSubset={openSubsetAssertion}
                    />
                  )}
                </section>
              </div>}
            </div>
            <div className="footnote">
              <ShieldCheck size={15} />
              <span>
                Two-product checks use the pair evaluator. Larger assemblies
                use exact subset assertions and show missing subsets as
                evidence gaps, alongside opening-fit and shared-power checks.
                Verify wiring and operating mode against the manufacturer
                documentation.
              </span>
            </div>
            {reportExpanded && checkResult && (
              <div className="assembly-report-backdrop">
                <section
                  className="assembly-report-dialog"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="assembly-report-title"
                  tabIndex={-1}
                  ref={reportDialogRef}
                >
                  <header className="assembly-report-dialog-header">
                    <div>
                      <h2 id="assembly-report-title" className="assembly-report-title">Assembly report</h2>
                      <p className="assembly-report-subtitle">Compatibility review</p>
                    </div>
                    <button
                      className="button button-quiet"
                      onClick={() => setReportExpanded(false)}
                    >
                      <ChevronDown size={16} />
                      Collapse to sidebar
                    </button>
                  </header>
                  <div className="assembly-report-dialog-body">
                    <div className="report-products-summary">
                      <strong>Products in this check</strong>
                      <div>
                        {selectedProducts.map((product) => (
                          <span key={product.id}>{displayName(product)}</span>
                        ))}
                      </div>
                    </div>
                    <CheckResult
                      result={checkResult}
                      expanded
                      onAssertSubset={openSubsetAssertion}
                      onCoverage={() => {
                        setReportExpanded(false);
                        setPage("coverage");
                      }}
                    />
                  </div>
                </section>
              </div>
            )}
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
            onRefreshLive={refreshLiveCatalog}
            refreshingCatalog={refreshingCatalog}
            onSearchCompatibility={searchProductCompatibility}
          />
        )}

        {page === "coverage" && (
          <CoveragePage
            coverage={coverage}
            categories={categories}
            onRefresh={loadCoverage}
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
                      conditions: prior.conditions || {},
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
                conditions: assertion.conditions || {},
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

        {page === "projects" && !projectData && (
          <section className="content projects-page">
            <div className="page-heading">
              <div>
                <span className="eyebrow">SITE WORKSPACE</span>
                <h1>Projects</h1>
                <p>Import a hardware schedule, review extracted doors and items, then save a sourced verification run for the site.</p>
              </div>
            </div>
            <div className="projects-home-grid">
              <form className="project-import-card" onSubmit={uploadSchedule}>
                <div className="project-card-heading">
                  <div className="section-icon"><Upload size={18} /></div>
                  <div><h2>Import hardware schedule</h2><p>Start with any selectable-text PDF. Extracted rows stay in review until checked against the source.</p></div>
                </div>
                <div className="project-form-grid">
                  <Field label="Project name" wide>
                    <input required value={projectForm.name} onChange={(event) => setProjectForm({ ...projectForm, name: event.target.value })} placeholder="Project or site name" />
                  </Field>
                  <Field label="Project code">
                    <input value={projectForm.project_code} onChange={(event) => setProjectForm({ ...projectForm, project_code: event.target.value })} placeholder="Optional" />
                  </Field>
                  <Field label="Schedule revision">
                    <input value={projectForm.revision_label} onChange={(event) => setProjectForm({ ...projectForm, revision_label: event.target.value })} placeholder="e.g. A1" />
                  </Field>
                  <Field label="Hardware schedule PDF" wide>
                    <input type="file" accept="application/pdf,.pdf" onChange={(event) => {
                      const file = event.target.files?.[0] || null;
                      setScheduleFile(file);
                      if (file && !projectForm.name) setProjectForm((current) => ({ ...current, name: file.name.replace(/\.pdf$/i, "") }));
                    }} />
                  </Field>
                </div>
                <div className="project-import-note"><CircleHelp size={16} /><span>The importer keeps the original PDF privately in local app storage. Text extraction is heuristic; scanned pages, ambiguous fields, and unmatched products are flagged for review.</span></div>
                <div className="project-form-actions">
                  <button className="button button-primary" type="submit" disabled={projectBusy || !scheduleFile}>
                    <Upload size={16} /> {projectBusy ? "Importing schedule…" : "Import schedule"}
                  </button>
                  {scheduleFile && <span className="muted-small">{scheduleFile.name} · {(scheduleFile.size / 1024 / 1024).toFixed(1)} MB</span>}
                </div>
              </form>
              <div className="project-list-panel">
                <div className="project-card-heading"><div><h2>Existing projects</h2><p>{projects.length} project{projects.length === 1 ? "" : "s"} · locally stored{projectsRefreshedAt ? ` · refreshed ${projectsRefreshedAt.toLocaleTimeString()}` : ""}</p></div><button className="button button-quiet" disabled={refreshingProjects} onClick={refreshProjects}><RefreshCw size={15} className={refreshingProjects ? "is-spinning" : ""} /> {refreshingProjects ? "Refreshing…" : "Refresh"}</button></div>
                {projects.length ? <div className="project-list">{projects.map((project) => (
                  <div className="project-list-row" key={project.id}>
                    <button className="project-list-main" onClick={() => openProject(project.id).catch((error) => setNotice(error.message))}>
                      <div><strong>{project.name}</strong><span>{project.project_code || "No project code"} · {project.revision_count} schedule revision{project.revision_count === 1 ? "" : "s"}</span></div>
                      <div className="project-list-count"><b>{project.door_count}</b><small>doors</small></div><ArrowUpRight size={17} />
                    </button>
                    <button className="icon-button project-delete-button" title={`Delete ${project.name}`} aria-label={`Delete project ${project.name}`} disabled={deletingProjectId === project.id} onClick={() => setConfirmDeleteProjectId((current) => current === project.id ? null : project.id)}>
                      <Trash2 size={15} />
                    </button>
                    {confirmDeleteProjectId === project.id && <div className="project-delete-confirm" role="alertdialog" aria-label={`Confirm deleting ${project.name}`}>
                      <div><strong>Delete this project?</strong><span>Schedule data and saved runs will be removed. The product catalog stays. This cannot be undone.</span></div>
                      <button className="button button-quiet" disabled={deletingProjectId === project.id} onClick={() => setConfirmDeleteProjectId(null)}>Cancel</button>
                      <button className="button project-delete-confirm-button" disabled={deletingProjectId === project.id} onClick={() => deleteProject(project)}>{deletingProjectId === project.id ? "Deleting…" : "Delete project"}</button>
                    </div>}
                  </div>
                ))}</div> : <div className="project-empty"><Building2 size={22} /><span>No projects yet. Import a schedule to create the first project.</span></div>}
              </div>
            </div>
          </section>
        )}

        {page === "projects" && projectData && (
          <section className="content projects-page project-detail-page">
            <div className="project-detail-heading">
              <div>
                <button className="button button-quiet project-back" onClick={() => { setProjectData(null); setProjectRun(null); setSourcePageText(null); setPage("projects"); loadProjects().catch(() => {}); }}><ArrowLeft size={15} /> All projects</button>
                <h1>{projectData.project.name}</h1>
                <p>{projectData.project.project_code || "No project code"} · {latestRevision?.revision_label || "No revision label"} · {latestRevision?.source_title}</p>
              </div>
              <div className="project-toolbar-actions">
                {latestRevision && <button className="button button-quiet" onClick={() => window.open(`/api/schedule-sources/${latestRevision.evidence_source_id}/file`, "_blank", "noopener,noreferrer")}><FileText size={16} /> Original PDF</button>}
                <button className="button button-primary" onClick={runProjectVerification} disabled={projectBusy || !projectDoors.length}><ShieldCheck size={16} /> {projectBusy ? "Checking doors…" : "Run all door checks"}</button>
              </div>
            </div>
            <div className="project-summary-strip">
              <div><span>DOORS</span><b>{projectDoors.length}</b></div>
              <div><span>HARDWARE SETS</span><b>{projectData.sets.length}</b></div>
              <div><span>REVIEW FLAGS</span><b className={projectData.issues.length ? "text-warning" : ""}>{projectData.issues.filter((issue) => issue.review_status === "open").length}</b></div>
              <div><span>SAVED RUNS</span><b>{projectData.runs.length}</b></div>
              {projectRun && <div className="project-export-actions"><button className="button button-quiet" onClick={() => exportProjectRun("csv")}><Download size={15} /> CSV</button><button className="button button-quiet" onClick={() => exportProjectRun("json")}><Download size={15} /> JSON</button></div>}
            </div>
            {projectData.issues.length > 0 && <details className="project-issues" open={projectData.issues.some((issue) => issue.severity === "blocking")}>
              <summary><CircleHelp size={15} /> Import review flags <span>{projectData.issues.length}</span></summary>
              <div className="project-issue-list">{projectData.issues.map((issue) => <div key={issue.id} className={`project-issue severity-${issue.severity}`}><span>{issue.severity}</span><div><b>{issue.message}</b>{issue.source_page && <button className="text-link-button" onClick={() => showSourcePage(issue.source_page)}>PDF page {issue.source_page}</button>}</div></div>)}</div>
            </details>}
            <div className="project-workspace-grid">
              <aside className="door-browser">
                <div className="door-browser-heading"><div><h2>Doors</h2><span>{visibleProjectDoors.length} shown · {projectDoors.length} total · {unknownProjectDoors.length} unknown number{unknownProjectDoors.length === 1 ? "" : "s"}</span></div><button className="icon-button" title="Add door" onClick={() => setManualDoorForm({ door_number: "", door_number_status: "known", heading_number: "", description: "", hand: "" })}><Plus size={17} /></button></div>
                <label className="door-search"><Search size={16} /><input value={doorSearch} onChange={(event) => setDoorSearch(event.target.value)} placeholder="Search door number or set" /></label>
                {manualDoorForm && <form className="manual-record-form" onSubmit={addManualDoor}>
                  <label className="unknown-number-toggle"><input type="checkbox" checked={manualDoorForm.door_number_status === "unknown"} onChange={(event) => setManualDoorForm({ ...manualDoorForm, door_number_status: event.target.checked ? "unknown" : "known" })} /><span>Door number unknown</span></label>
                  <input required={manualDoorForm.door_number_status !== "unknown"} disabled={manualDoorForm.door_number_status === "unknown"} placeholder="Door number" value={manualDoorForm.door_number} onChange={(event) => setManualDoorForm({ ...manualDoorForm, door_number: event.target.value })} />
                  <input placeholder="Description" value={manualDoorForm.description} onChange={(event) => setManualDoorForm({ ...manualDoorForm, description: event.target.value })} />
                  <select value={manualDoorForm.heading_number} onChange={(event) => setManualDoorForm({ ...manualDoorForm, heading_number: event.target.value })}><option value="">No set assigned</option>{projectData.sets.map((set) => <option key={set.id} value={set.set_code}>{set.set_code} · {set.description}</option>)}</select>
                  <div><button className="button button-primary" type="submit">Save door</button><button className="button button-quiet" type="button" onClick={() => setManualDoorForm(null)}>Cancel</button></div>
                </form>}
                <div className="door-list">
                  {knownProjectDoors.length > 0 && <div className="door-list-group-label">DOOR NUMBERS FOUND <span>{knownProjectDoors.length}</span></div>}
                  {knownProjectDoors.map(renderProjectDoorRow)}
                  {unknownProjectDoors.length > 0 && <details className="unknown-door-group" open={selectedProjectDoor?.door_number_status === "unknown"}>
                    <summary>Unknown door numbers <span>{unknownProjectDoors.length}</span></summary>
                    <div>{unknownProjectDoors.map(renderProjectDoorRow)}</div>
                  </details>}
                  {!visibleProjectDoors.length && <div className="project-empty compact">No matching doors.</div>}
                </div>
              </aside>
              <div className="door-review-panel">
                {selectedProjectDoor ? <>
                  <div className="door-review-heading">
                    <div><span className="eyebrow">DOOR {selectedDoorIndex + 1} OF {visibleProjectDoors.length}</span><h2>{selectedProjectDoor.door_number_status === "unknown" ? "Unknown door number" : selectedProjectDoor.door_number}</h2><p>{selectedProjectDoor.description || "Door details need review"}</p></div>
                    <div className="door-stepper"><button className="icon-button" disabled={selectedDoorIndex <= 0} aria-label="Previous door" onClick={() => setSelectedDoorId(visibleProjectDoors[selectedDoorIndex - 1]?.id)}><ArrowLeft size={17} /></button><button className="icon-button" disabled={selectedDoorIndex < 0 || selectedDoorIndex >= visibleProjectDoors.length - 1} aria-label="Next door" onClick={() => setSelectedDoorId(visibleProjectDoors[selectedDoorIndex + 1]?.id)}><ArrowRight size={17} /></button></div>
                  </div>
                  <div className="door-facts-row"><span>SET <b>{selectedProjectDoor.heading_number || "Unassigned"}</b></span><span>HAND <b>{selectedProjectDoor.hand || "Not parsed"}</b></span><span>PDF PAGE <b>{selectedProjectDoor.source_page || "—"}</b></span><button className="text-link-button" onClick={() => showSourcePage(selectedProjectDoor.source_page)}>View extracted page text</button><button className="text-link-button" onClick={() => setDoorNumberForm({ id: selectedProjectDoor.id, door_number: selectedProjectDoor.door_number_status === "unknown" ? "" : selectedProjectDoor.door_number, door_number_status: selectedProjectDoor.door_number_status || "known" })}>{selectedProjectDoor.door_number_status === "unknown" ? "Set door number" : "Edit door number"}</button></div>
                  {doorNumberForm?.id === selectedProjectDoor.id && <form className="manual-record-form door-number-form" onSubmit={saveDoorNumber}>
                    <label className="unknown-number-toggle"><input type="checkbox" checked={doorNumberForm.door_number_status === "unknown"} onChange={(event) => setDoorNumberForm({ ...doorNumberForm, door_number_status: event.target.checked ? "unknown" : "known" })} /><span>Door number unknown</span></label>
                    <input required={doorNumberForm.door_number_status !== "unknown"} disabled={doorNumberForm.door_number_status === "unknown"} placeholder="Enter the number shown in the schedule" value={doorNumberForm.door_number} onChange={(event) => setDoorNumberForm({ ...doorNumberForm, door_number: event.target.value })} />
                    <div><button className="button button-primary" type="submit">Save number status</button><button className="button button-quiet" type="button" onClick={() => setDoorNumberForm(null)}>Cancel</button></div>
                  </form>}
                  {sourcePageText && <div className="source-text-panel"><div><b>Extracted text · PDF page {sourcePageText.page_number}</b><button className="icon-button" onClick={() => setSourcePageText(null)} aria-label="Close source text"><X size={15} /></button></div><pre>{sourcePageText.text || "No selectable text on this page."}</pre></div>}
                  {selectedRunDoor && <div className={`door-run-result status-${selectedRunDoor.result.status}`}><div className="door-run-title"><StatusPill status={selectedRunDoor.result.status} /><b>{selectedRunDoor.result.message}</b></div>{selectedRunDoor.result.estimate?.score != null && <small>Assessment {selectedRunDoor.result.estimate.score}% · confidence {selectedRunDoor.result.estimate.confidence}% · {selectedRunDoor.result.estimate.checks_in_average} checks in estimate</small>}{selectedRunDoor.result.findings?.map((finding, index) => <div className="door-run-finding" key={`${index}-${finding.source_url || finding.rationale}`}><StatusPill status={finding.status} /><span>{finding.rationale}</span>{finding.source_url && <a href={finding.source_url} target="_blank" rel="noreferrer">{finding.source_title || "Evidence source"} <ExternalLink size={12} /></a>}</div>)}</div>}
                  <h3 className="door-items-heading">Scheduled hardware</h3>
                  {selectedProjectDoor.assignments.length ? selectedProjectDoor.assignments.map((assignment) => <section className="door-set-section" key={assignment.id}><div className="door-set-heading"><div><b>Set {assignment.set_code}</b><span>{assignment.set_description || "Hardware set"} · PDF pages {assignment.source_start_page || "?"}–{assignment.source_end_page || "?"}</span></div><span>{assignment.items.length} scheduled items</span></div>
                    {assignment.items.length ? assignment.items.map((item) => {
                      const confirmed = item.matches.find((match) => match.review_status === "confirmed");
                      const query = matchQueries[item.id] || "";
                      const matches = query ? activeProducts.filter((product) => `${displayName(product)} ${product.name} ${product.category_label}`.toLowerCase().includes(query.toLowerCase())).slice(0, 5) : [];
                      return <article className="scheduled-line-card" key={item.id}><div className="scheduled-line-main"><div><span className="scheduled-line-quantity">{item.quantity_for_heading ?? "—"} {item.units}</span>{item.sku && <span className="scheduled-line-sku">SKU {item.sku}</span>}</div><p>{item.product_text || item.description_text}</p><small>Source PDF page {item.source_page}</small></div><div className="scheduled-line-match">{confirmed && editingMatchItemId !== item.id ? <div className="confirmed-match"><Check size={15} /><div><b>{displayName(confirmed.product)}</b><small>Confirmed catalog match</small></div><div className="confirmed-match-actions"><button className="text-link-button" onClick={() => { setEditingMatchItemId(item.id); setMatchQueries({ ...matchQueries, [item.id]: "" }); }}>Change</button><button className="text-link-button" onClick={() => saveScheduleMatch(item.id, confirmed.product_id, "candidate")}>Undo</button></div></div> : <>
                        {item.matches.filter((match) => match.review_status !== "rejected" && match.review_status !== "confirmed").map((match) => <button className="candidate-match" key={match.id} onClick={() => saveScheduleMatch(item.id, match.product_id)}><span>Suggested match · verify</span><b>{displayName(match.product)}</b><small>Confirm this catalog match</small></button>)}
                        <label className="catalog-match-search"><Search size={14} /><input value={query} onChange={(event) => setMatchQueries({ ...matchQueries, [item.id]: event.target.value })} placeholder="Search catalog by model" /></label>
                        {matches.map((product) => <button className="catalog-match-option" key={product.id} onClick={() => saveScheduleMatch(item.id, product.id)}>{displayName(product)} <span>Confirm</span></button>)}
                        {confirmed && editingMatchItemId === item.id && <button className="text-link-button catalog-match-cancel" onClick={() => setEditingMatchItemId(null)}>Keep current match</button>}
                      </>}</div></article>;
                    }) : <p className="muted-small empty-items">No item rows were parsed. Use Add item under Hardware sets after verifying the source page.</p>}
                  </section>) : <div className="project-empty"><span>No hardware set is assigned to this door. Review the schedule page or add the assignment manually.</span></div>}
                </> : <div className="project-empty door-empty"><FileText size={25} /><h2>No door rows recognized</h2><p>Use the source pages and review controls to add doors and hardware sets manually. The original PDF remains attached to this revision.</p><button className="button button-primary" onClick={() => setManualDoorForm({ door_number: "", door_number_status: "known", heading_number: "", description: "", hand: "" })}><Plus size={15} /> Add first door</button></div>}
              </div>
            </div>
            <section className="hardware-set-manager">
              <div className="hardware-set-heading"><div><div className="hardware-set-title-row"><h2>Hardware sets</h2><button className="icon-button hardware-set-help" type="button" title="Use this section to find a schedule set, add a missing set, or add a hardware item to an existing set. Doors assigned to a set share its scheduled items." aria-label="Help: what hardware sets are for"><CircleHelp size={15} /></button></div><span>{projectData.sets.length} sets · {projectData.sets.reduce((total, set) => total + set.items.length, 0)} scheduled items</span></div><div className="hardware-set-actions"><button className="button button-quiet" onClick={() => { setHardwareSetsExpanded(true); setManualSetForm({ set_code: "", description: "" }); }}><Plus size={15} /> Add set</button><button className="button button-quiet hardware-set-toggle" aria-expanded={hardwareSetsExpanded} aria-controls="hardware-set-content" onClick={() => setHardwareSetsExpanded((expanded) => !expanded)}><ChevronDown size={15} /> {hardwareSetsExpanded ? "Hide sets" : "Show sets"}</button></div></div>
              <div id="hardware-set-content" className="hardware-set-content" hidden={!hardwareSetsExpanded}>
                {manualSetForm && <form className="manual-record-form hardware-set-create-form" onSubmit={addManualSet}><input required placeholder="Set code" value={manualSetForm.set_code} onChange={(event) => setManualSetForm({ ...manualSetForm, set_code: event.target.value })} /><input placeholder="Description" value={manualSetForm.description} onChange={(event) => setManualSetForm({ ...manualSetForm, description: event.target.value })} /><div><button className="button button-primary" type="submit">Save set</button><button className="button button-quiet" type="button" onClick={() => setManualSetForm(null)}>Cancel</button></div></form>}
                <label className="hardware-set-search"><Search size={15} /><input value={hardwareSetSearch} onChange={(event) => setHardwareSetSearch(event.target.value)} placeholder="Search hardware sets" /></label>
                {visibleHardwareSets.length ? <div className="hardware-set-grid">{visibleHardwareSets.map((set) => <article className="set-manager-card" key={set.id}><div className="set-manager-card-heading"><div><b>Set {set.set_code}</b><span>{set.items.length} item{set.items.length === 1 ? "" : "s"}</span></div><button className="button button-quiet" onClick={() => setManualItemForm({ hardware_set_id: set.id, product_text: "", sku: "", quantity: 1, units: "EA", source_page: set.source_start_page || 1 })}><Plus size={14} /> Add item</button></div><p>{set.description || `PDF pages ${set.source_start_page || "?"}–${set.source_end_page || "?"}`}</p>{manualItemForm?.hardware_set_id === set.id && <form className="manual-record-form set-item-form" onSubmit={addManualItem}><input required placeholder="Scheduled item text/model" value={manualItemForm.product_text} onChange={(event) => setManualItemForm({ ...manualItemForm, product_text: event.target.value })} /><div><input type="number" min="0.01" step="any" aria-label="Quantity" value={manualItemForm.quantity} onChange={(event) => setManualItemForm({ ...manualItemForm, quantity: Number(event.target.value) })} /><input placeholder="SKU (optional)" value={manualItemForm.sku} onChange={(event) => setManualItemForm({ ...manualItemForm, sku: event.target.value })} /></div><div><button className="button button-primary" type="submit">Save item</button><button className="button button-quiet" type="button" onClick={() => setManualItemForm(null)}>Cancel</button></div></form>}</article>)}</div> : <div className="project-empty compact">No hardware sets match that search.</div>}
              </div>
            </section>
            {projectData.runs.length > 0 && <section className="project-run-history"><div className="run-history-heading"><div><h2>Verification log</h2><p>Saved, reproducible results for this schedule revision.</p></div><span>{projectData.runs.length} saved run{projectData.runs.length === 1 ? "" : "s"}</span></div><div className="run-history-list">{projectData.runs.map((run) => <button key={run.id} className={`run-history-card ${projectRun?.run.id === run.id ? "active" : ""}`} onClick={() => loadProjectRun(run.id)}><span className="run-history-main"><b>{run.run_name || `Run ${run.id}`}</b><small>{new Date(run.created_at).toLocaleString()} · {run.summary?.door_count || 0} doors checked</small></span><span className="run-history-statuses">{Object.entries(run.summary?.status_counts || {}).map(([status, count]) => <em className={`run-count status-${status}`} key={status}><b>{count}</b> {status.replaceAll("_", " ")}</em>)}</span></button>)}</div></section>}
          </section>
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
              const preview = exampleEstimates[scenario.id];
              const estimate = preview?.estimate;
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
                    <div className="example-estimate" aria-live="polite">
                      {preview?.loading ? (
                        <span>Calculating assessment and confidence…</span>
                      ) : estimate?.score != null ? (
                        <>
                          <strong>Assembly score: {estimate.score}%</strong>
                          <span>Confidence in assessment: {estimate.confidence}%</span>
                          {estimate.checks_in_average != null && (
                            <span>{estimate.checks_in_average} checks averaged</span>
                          )}
                        </>
                      ) : preview?.error ? (
                        <span>Estimate unavailable: {preview.error}</span>
                      ) : (
                        <span>Assessment confidence unavailable.</span>
                      )}
                    </div>
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
            sources={evidenceSources}
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

function NavItem({ active, onClick, icon, label, count, collapsed = false }) {
  return (
    <button className={`nav-item ${active ? "active" : ""}`} onClick={onClick} title={collapsed ? label : undefined} aria-label={label}>
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
              '{"power_requirements":{"accepted_voltages":["12VDC"],"current_a":0.3},"power_output":{"voltage":"24VAC","max_current_a":1.5,"documented_load_types":["electric_strike"]},"relay_output":{"type":"dry_contact"}}'
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

function AssertionForm({ form, setForm, products, sources, statuses, onSubmit }) {
  const [slots, setSlots] = useState(() => [
    ...(form.product_ids || []),
    ...Array(Math.max(0, 2 - (form.product_ids || []).length)).fill(null),
  ]);
  const [queries, setQueries] = useState({});
  const [sourceQuery, setSourceQuery] = useState("");
  const [conditionRows, setConditionRows] = useState(() =>
    Object.entries(form.conditions || {}).map(([key, value]) => [key, String(value)]),
  );
  useEffect(() => {
    const selected = form.product_ids || [];
    setSlots((current) => {
      const next = [...selected, ...Array(Math.max(0, 2 - selected.length)).fill(null)];
      return next.length < current.length ? next : next.slice(0, current.length);
    });
  }, [form.id, form.product_ids]);
  useEffect(() => {
    setConditionRows(
      Object.entries(form.conditions || {}).map(([key, value]) => [key, String(value)]),
    );
  }, [form.id]);
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const updateConditions = (rows) => {
    setConditionRows(rows);
    const conditions = {};
    rows.forEach(([key, value]) => {
      const name = key.trim();
      if (!name || value === "") return;
      const normalized = value.trim();
      conditions[name] = normalized === "true"
        ? true
        : normalized === "false"
          ? false
          : normalized !== "" && Number.isFinite(Number(normalized))
            ? Number(normalized)
            : value;
    });
    update("conditions", conditions);
  };
  const selectProduct = (index, id) => {
    const next = [...slots];
    next[index] = id;
    setSlots(next);
    setQueries((current) => ({ ...current, [index]: "" }));
    update("product_ids", next.filter(Boolean));
  };
  const removeSlot = (index) => {
    const next = slots.filter((_, slotIndex) => slotIndex !== index);
    setSlots(next);
    setQueries({});
    update("product_ids", next.filter(Boolean));
  };
  const matchedSources = sources.filter((source) =>
    `${source.source_title} ${source.source_url}`.toLowerCase().includes(sourceQuery.toLowerCase()),
  ).slice(0, 6);
  return (
    <form className="model-form" onSubmit={onSubmit}>
      <div className="field">
        <span>Products in this assertion</span>
        <div className="assertion-product-picker">
          {slots.map((id, index) => {
            const selected = products.find((product) => product.id === id);
            const query = queries[index] || "";
            const matches = query.trim()
              ? products.filter((product) =>
                  !slots.includes(product.id) &&
                  `${displayName(product)} ${product.name} ${product.category_label || product.category}`
                    .toLowerCase().includes(query.toLowerCase()),
                ).slice(0, 7)
              : [];
            return (
              <div className="assertion-product-slot" key={index}>
                <label htmlFor={`assertion-product-${index}`}>Item {index + 1}</label>
                {selected ? (
                  <div className="assertion-selected-product">
                    <span><b>{displayName(selected)}</b><small>{selected.category_label || selected.category}</small></span>
                    <button type="button" className="icon-button" aria-label={`Remove ${displayName(selected)}`} onClick={() => selectProduct(index, null)}><X size={15} /></button>
                  </div>
                ) : (
                  <div className="assertion-search-wrap">
                    <Search size={15} />
                    <input
                      id={`assertion-product-${index}`}
                      value={query}
                      onChange={(event) => setQueries((current) => ({ ...current, [index]: event.target.value }))}
                      placeholder="Search by manufacturer or model"
                      autoComplete="off"
                    />
                    {matches.length > 0 && (
                      <div className="assertion-search-results">
                        {matches.map((product) => (
                          <button key={product.id} type="button" onClick={() => selectProduct(index, product.id)}>
                            <b>{displayName(product)}</b><small>{product.category_label || product.category}</small>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {index >= 2 && <button type="button" className="text-button assertion-remove-slot" onClick={() => removeSlot(index)}>Remove item</button>}
              </div>
            );
          })}
        </div>
        <button type="button" className="text-button assertion-add-item" onClick={() => setSlots((current) => [...current, null])}><Plus size={15} /> Add another item</button>
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
        <Field label="Find an evidence source" wide>
          <div className="assertion-source-picker">
            <div className="assertion-search-wrap"><Search size={15} /><input value={sourceQuery} onChange={(event) => setSourceQuery(event.target.value)} placeholder="Search saved manuals and sources" autoComplete="off" /></div>
            {sourceQuery && matchedSources.length > 0 && <div className="assertion-search-results assertion-source-results">{matchedSources.map((source) => <button type="button" key={source.source_url} onClick={() => { update("source_title", source.source_title); update("source_url", source.source_url); setSourceQuery(""); }}><b>{source.source_title}</b><small>{source.source_url}</small></button>)}</div>}
            {form.source_title && <small className="assertion-source-selected">Selected: {form.source_title}</small>}
          </div>
        </Field>
        <details className="assertion-manual-source field-wide">
          <summary>Or enter a source link</summary>
          <div className="modal-fields assertion-fields">
            <Field label="Source title"><input value={form.source_title} onChange={(event) => update("source_title", event.target.value)} /></Field>
            <Field label="Source link" wide><input type="url" value={form.source_url} required={form.evidence_status !== "research_lead"} onChange={(event) => update("source_url", event.target.value)} placeholder="Paste a manufacturer manual or product page link" /></Field>
          </div>
        </details>
        <div className="field field-wide">
          <span>Conditions (optional)</span>
          <small>Describe when this result applies, such as operating mode or voltage.</small>
          <div className="assertion-condition-rows">
            {conditionRows.map(([key, value], index) => <div className="assertion-condition-row" key={index}><input aria-label="Condition name" value={key} onChange={(event) => { const next = [...conditionRows]; next[index] = [event.target.value, value]; updateConditions(next); }} placeholder="Condition (for example, operating mode)" /><input aria-label="Condition value" value={value} onChange={(event) => { const next = [...conditionRows]; next[index] = [key, event.target.value]; updateConditions(next); }} placeholder="Value (for example, mode 7)" /><button type="button" className="icon-button" aria-label="Remove condition" onClick={() => updateConditions(conditionRows.filter((_, row) => row !== index))}><X size={15} /></button></div>)}
          </div>
          <button type="button" className="text-button assertion-add-item" onClick={() => updateConditions([...conditionRows, ["", ""]])}><Plus size={15} /> Add condition</button>
        </div>
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
  onRefreshLive,
  refreshingCatalog,
  onSearchCompatibility,
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
        <button
          className="button button-quiet"
          onClick={onRefreshLive}
          disabled={refreshingCatalog || importing}
        >
          <RefreshCw className={refreshingCatalog ? "spin" : ""} size={15} />
          {refreshingCatalog ? "Refreshing catalogs…" : "Refresh live catalogs"}
        </button>
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
      <p className="catalog-refresh-note">
        Use <b>Find compatibility &amp; limits</b> on a product row to search for pairings and published fit limits such as door width, height, weight, materials, voltage, and mounting. Results are research leads, not approvals.
      </p>
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
                      className="button button-small product-search-button"
                      aria-label={`Search what works with ${displayName(product)}`}
                      onClick={() => onSearchCompatibility(product)}
                    >
                      <Search size={13} />
                      Find compatibility &amp; limits
                    </button>
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
  const [filter, setFilter] = useState("applicable");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      onRefresh({ page, status: filter, query });
    }, query ? 250 : 0);
    return () => window.clearTimeout(timer);
  }, [page, filter, query]);

  const updateFilter = (value) => {
    setFilter(value);
    setPage(1);
  };
  const updateQuery = (value) => {
    setQuery(value);
    setPage(1);
  };
  return (
    <section className="content model-page">
      <div className="page-heading">
        <div>
          <h1>Compatibility coverage</h1>
          <p>
            Pair estimates use recorded compatibility, specification matches,
            and cautious manufacturer or product-family signals. Confidence
            shows how strongly the available evidence supports the assessment;
            it is not a probability that the combination will work.
          </p>
        </div>
        <button className="button button-quiet" onClick={() => onRefresh({ page, status: filter, query })}>
          <RefreshCw size={15} />
          Refresh coverage
        </button>
      </div>
      <div className="coverage-summary">
        {[
          ["total", "ALL PRODUCT PAIRS"],
          ["applicable", "INTERACTING PAIRS"],
          ["average_compatibility_score", "AVG. ADJUSTED SCORE"],
          ["average_confidence", "AVG. CONFIDENCE IN ASSESSMENT"],
          ["compatible", "SOURCED COMPATIBLE"],
          ["incompatible", "SOURCED CONFLICTS"],
          ["conditional", "CONDITIONAL"],
          ["unverified", "UNVERIFIED"],
          ["not_applicable", "NO DECLARED INTERACTION"],
        ].map(([key, label]) => (
          <div className={`coverage-stat coverage-${key}`} key={key}>
            <small>{label}</small>
            <b>
              {coverage?.summary?.[key] == null
                ? "—"
                : ["average_compatibility_score", "average_confidence"].includes(key)
                  ? `${coverage.summary[key]}%`
                  : coverage.summary[key]}
            </b>
          </div>
        ))}
      </div>
      <div className="coverage-note">
        <CircleHelp size={16} />
        <span>
          Weak signals can move an estimate slightly from neutral (50), with
          the reason shown for each pair. Manufacturer match alone is only a
          small signal, not proof of compatibility. Non-interacting pairs are
          excluded from assembly verdicts, and strong sourced conflicts
          override a favorable average.
        </span>
      </div>
      <div className="catalog-panel coverage-panel">
        <div className="catalog-toolbar">
          <div>
            <h2>Applicable product pairs</h2>
            <p>
              {coverage?.summary?.applicable || 0} interacting pairs ·{" "}
              {coverage?.total_filtered ?? 0} shown in this result set
            </p>
          </div>
          <div className="coverage-filters">
            <label className="sr-only" htmlFor="coverage-search">Search product pairs</label>
            <input
              id="coverage-search"
              className="text-input"
              value={query}
              onChange={(event) => updateQuery(event.target.value)}
              placeholder="Search products or manufacturers"
            />
            <select
              className="select-input"
              value={filter}
              onChange={(event) => updateFilter(event.target.value)}
              aria-label="Filter compatibility pairs"
            >
              <option value="applicable">Interacting pairs</option>
              <option value="compatible">Sourced compatible</option>
              <option value="incompatible">Sourced incompatible</option>
              <option value="conditional">Conditional</option>
              <option value="unverified">Unverified</option>
              <option value="not_applicable">No declared interaction</option>
              <option value="all">All pairs</option>
            </select>
          </div>
        </div>
        <div className="product-table-wrap">
          <table className="product-table coverage-table">
            <thead>
              <tr>
                <th>Component A</th>
                <th>Component B</th>
                <th>Result</th>
                <th>Assessment / confidence</th>
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
                    <small>{row.estimate_label}</small>
                  </td>
                  <td>
                    {row.adjusted_score == null ? "—" : `${row.adjusted_score}%`}
                    <small>{row.confidence_score == null ? "Excluded from average" : `${row.confidence_score}% confidence in assessment`}</small>
                  </td>
                  <td>
                    <span>
                      {row.rationale ||
                        "No sourced assertion or applicable rule."}
                    </span>
                    {row.assembly_evidence?.map((evidence, index) => (
                      <div className="coverage-assembly-evidence" key={`${evidence.source_url}-${index}`}>
                        <strong>Related tuple evidence · {evidence.products.map((product) => product.model).join(" + ")}</strong>
                        <small>
                          Tuple-level documentation; this source does not independently approve the displayed pair.
                        </small>
                        {evidence.source_url && (
                          <a
                            className="source-link"
                            href={evidence.source_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {evidence.source_title || "Open assembly source"} <ArrowUpRight size={12} />
                          </a>
                        )}
                      </div>
                    ))}
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
              No pairs match this filter. Add products to expand the compatibility inventory.
            </div>
          )}
        </div>
        <div className="coverage-pagination">
          <span>Page {coverage?.page || page} of {coverage?.pages || 1}</span>
          <div>
            <button className="button button-small" disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>Previous</button>
            <button className="button button-small" disabled={page >= (coverage?.pages || 1)} onClick={() => setPage((current) => current + 1)}>Next</button>
          </div>
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

function CheckResult({ result, onCoverage, onAssertSubset, expanded = false }) {
  const assessmentRef = useRef(null);
  const [assessmentJumpVisible, setAssessmentJumpVisible] = useState(true);
  const findings = result.findings || [];
  const subsetChecks = Array.isArray(result.subset_checks) ? result.subset_checks : [];
  const subsetChecksBySize = subsetChecks.reduce((groups, check) => {
    (groups[check.subset_size] ||= []).push(check);
    return groups;
  }, {});
  const exactSubsetCount = subsetChecks.filter((check) => check.has_exact_assertion).length;
  const conflictFindings = findings.filter(
    (finding) => finding.status === "incompatible",
  );
  const failingFindings = findings
    .filter((finding) => ["conditional", "unverified"].includes(finding.status))
    .sort((left, right) => {
      const priority = { conditional: 0, unverified: 1 };
      return priority[left.status] - priority[right.status];
    });
  const workingFindings = findings.filter((finding) => finding.status === "compatible");
  const needsAssessmentShortcut =
    expanded && result.estimate?.score != null &&
    conflictFindings.length + failingFindings.length >= 5;
  useEffect(() => {
    if (!needsAssessmentShortcut) {
      setAssessmentJumpVisible(true);
      return undefined;
    }

    const assessment = assessmentRef.current;
    const scroller = assessment?.closest(".assembly-report-dialog-body");
    if (!assessment || !scroller) return undefined;

    const updateVisibility = () => {
      const assessmentTop =
        assessment.getBoundingClientRect().top -
        scroller.getBoundingClientRect().top +
        scroller.scrollTop;
      const restingPosition = scroller.clientHeight * 0.72;
      setAssessmentJumpVisible(scroller.scrollTop < assessmentTop - restingPosition);
    };

    updateVisibility();
    scroller.addEventListener("scroll", updateVisibility, { passive: true });
    window.addEventListener("resize", updateVisibility);
    return () => {
      scroller.removeEventListener("scroll", updateVisibility);
      window.removeEventListener("resize", updateVisibility);
    };
  }, [needsAssessmentShortcut]);
  const scrollToAssessment = () =>
    assessmentRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  const renderEvidenceSources = (finding) => {
    const candidates = [
      ...(Array.isArray(finding.sources) ? finding.sources : []),
      ...(finding.source_url
        ? [{ source_title: finding.source_title, source_url: finding.source_url }]
        : []),
    ];
    const sources = [...new Map(
      candidates
        .filter((source) => source?.source_url)
        .map((source) => [source.source_url, source]),
    ).values()];
    if (!sources.length) return null;
    return (
      <div className="finding-evidence">
        <strong>Evidence sources</strong>
        <div className="finding-evidence-links">
          {sources.map((source) => (
            <a
              className="source-link"
              href={source.source_url}
              target="_blank"
              rel="noreferrer"
              key={source.source_url}
            >
              {source.source_title || "Open source document"} <ArrowUpRight size={12} />
            </a>
          ))}
        </div>
      </div>
    );
  };
  const renderFindingCard = (finding, index) => (
    <div
      className="finding-card"
      key={`${finding.finding_type || finding.status}-${finding.product_a?.id || "assembly"}-${finding.product_b?.id || index}`}
    >
      <div className="finding-title">
        <StatusPill status={finding.status} />
        {finding.product_a && (
          <b>
            {displayName(finding.product_a)}
            {finding.product_b
              ? ` + ${displayName(finding.product_b)}`
              : finding.finding_type === "power_path"
                ? " · power path"
                : " · opening fit"}
          </b>
        )}
      </div>
      <p>{finding.rationale}</p>
      {renderEvidenceSources(finding)}
    </div>
  );
  const labels = {
    compatible: "Compatible",
    incompatible: "Incompatible",
    conditional: "Conditional",
    unverified: "Not yet verified",
    likely_compatible: "Likely compatible · estimate",
    likely_incompatible: "Likely incompatible · estimate",
  };
  return (
    <div className={`assembly-result-content status-${result.status}`}>
      <h2 className="assembly-result-heading">Assembly report</h2>
      <h3>{labels[result.status] || "Not yet verified"}</h3>
      {conflictFindings.length > 0 && (
        <section className="conflict-reasons" aria-labelledby="conflict-reasons-title">
          <h4 id="conflict-reasons-title">Why it doesn’t work</h4>
          {conflictFindings.map((finding, index) => {
            const products = finding.product_ids
              ?.map((id) => result.products?.find((product) => product.id === id))
              .filter(Boolean);
            const title = finding.product_a
              ? `${displayName(finding.product_a)}${finding.product_b ? ` + ${displayName(finding.product_b)}` : ""}`
              : products?.length
                ? products.map(displayName).join(" + ")
                : finding.finding_type === "power_path"
                  ? "Power path"
                  : "Assembly conflict";
            return (
              <div className="conflict-reason" key={`conflict-${index}`}>
                <strong>{title}</strong>
                <p>{finding.rationale}</p>
                {renderEvidenceSources(finding)}
              </div>
            );
          })}
        </section>
      )}
      {result.status === "incompatible" && (
        <div className="conflict-override-note" role="note">
          A well-supported documented conflict overrides the average score, even if other checks are favorable.
        </div>
      )}
      {findings.length === 0 && (
        <p>{result.message || result.assertion?.rationale}</p>
      )}
      {failingFindings.length > 0 && (
        <section className="report-findings">
          <h4>{conflictFindings.length ? "Other items to resolve" : "What’s failing or needs attention"}</h4>
          {failingFindings.map((finding, index) => (
            <React.Fragment key={`finding-with-jump-${finding.product_a?.id || "item"}-${finding.product_b?.id || index}`}>
              {renderFindingCard(finding, index)}
              {needsAssessmentShortcut && index === Math.min(3, failingFindings.length - 1) && (
                <button
                    className={`assessment-jump assessment-jump-secondary${assessmentJumpVisible ? " is-visible" : " is-hidden"}`}
                  type="button"
                  onClick={scrollToAssessment}
                  aria-label="Scroll to assembly assessment"
                >
                  <ChevronDown size={24} aria-hidden="true" />
                </button>
              )}
            </React.Fragment>
          ))}
        </section>
      )}
      {result.estimate?.score != null && (
        <div className="assembly-estimate" ref={assessmentRef}>
          <div className="assembly-estimate-head">
            <div><small className="estimate-title">Assembly assessment</small><strong>{result.estimate.score}%</strong></div>
            <div>
              <small>CONFIDENCE IN ASSESSMENT</small>
              <strong>{result.estimate.confidence}%</strong>
            </div>
          </div>
          <div className="estimate-meter" aria-label={`Compatibility estimate ${result.estimate.score} percent`}>
            <span style={{ width: `${result.estimate.score}%` }} />
          </div>
          <p>
            {result.estimate.checks_in_average} assessment factors averaged
            {result.estimate.applicable_pairs > 0 && ` · ${result.estimate.applicable_pairs} applicable product pairs`}
            {subsetChecks.length > 0 && ` · ${subsetChecks.length} combinations listed (${exactSubsetCount} with exact assertions, ${subsetChecks.length - exactSubsetCount} without an exact record)`}
          </p>
          <small>{result.estimate.method}</small>
        </div>
      )}
      {workingFindings.length > 0 && (
        <section className="report-findings report-working-findings">
          <h4>Why it works</h4>
          {workingFindings.map(renderFindingCard)}
          {subsetChecks.length > 0 && (
            <details className="subset-check-breakdown">
              <summary>
                <strong>Combination breakdown</strong>
                <span>{subsetChecks.length} groups of 2+ selected models</span>
              </summary>
              <p>
                Every subset of two or more selected models is listed. A result appears only when an exact assertion exists for that subset; a missing assertion is an evidence gap, not proof of incompatibility. Pair rules and inferred pair signals are not used inside a multi-model assembly.
              </p>
              {Object.entries(subsetChecksBySize).map(([size, checks]) => (
                <section className="subset-check-group" key={size}>
                  <h4>
                    <span>{size}-model groups</span>
                    <small>{checks.length}</small>
                  </h4>
                  <div className="subset-check-list">
                    {checks.map((check) => (
                      <article className="subset-check-card" key={check.product_ids.join("-")}>
                        <div className="subset-check-title">
                          <StatusPill status={check.status} />
                        </div>
                        <div className="subset-check-products">
                          {check.products.map((product) => (
                            <span key={product.id}>{product.model}</span>
                          ))}
                        </div>
                        <p>{check.rationale}</p>
                        {check.has_exact_assertion && (
                          <small>
                            Assertion {check.assertion_id} · {check.evidence_status.replaceAll("_", " ")}
                          </small>
                        )}
                        {renderEvidenceSources(check)}
                        <button
                          className="button button-small"
                          type="button"
                          onClick={() => onAssertSubset?.(check.product_ids)}
                        >
                          {check.has_exact_assertion ? "Edit subset assertion" : "Record subset outcome"}
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
              ))}
            </details>
          )}
        </section>
      )}
      <button className="text-link" onClick={onCoverage}>
        Open coverage view <ArrowUpRight size={14} />
      </button>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import * as motion from "motion/react-client";
import Navbar from "@/components/Navbar";
import SafetyScoreCard from "@/components/SafetyScoreCard";
import PKMetricsCard from "@/components/PKMetricsCard";
import RiskCard from "@/components/RiskCard";
import PKChart from "@/components/PKChart";
import OrganMap from "@/components/OrganMap";
import PathwayCard from "@/components/PathwayCard";
import type { Drug } from "@/lib/drugData";
import {
  checkBackendHealth,
  CompoundPreset,
  fetchCompounds,
  fetchPrediction,
  fetchSummary,
  mapPredictionToDrug,
} from "@/lib/backendApi";

type Page = "input" | "results" | "science";

const defaultPresets = ["Tylenol", "Ibuprofen", "Thalidomide", "Aspirin", "Metformin"];
const box = {
  width: 62,
  height: 62,
  backgroundColor: "#f5f5f5",
  borderRadius: 5,
};


const analysisPipelineSteps = [
  { id: "structure", label: "Molecular structure", detail: "SMILES validation & RDKit features" },
  { id: "admet",     label: "ADMET screening",     detail: "Absorption, distribution, metabolism" },
  { id: "pk",        label: "PK simulation",        detail: "One-compartment oral curve" },
  { id: "safety",    label: "Safety synthesis",     detail: "Risk tiles & composite score" },
] as const;

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("input");
  const [selectedDrugLabel, setSelectedDrugLabel] = useState("Tylenol");
  const [selectedPreset, setSelectedPreset] = useState<string | null>("Tylenol");
  const [inputValue, setInputValue] = useState("");
  const [dose, setDose] = useState(1.0);
  const [drug, setDrug] = useState<Drug | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [presets, setPresets] = useState<string[]>(defaultPresets);
  const [compoundLookup, setCompoundLookup] = useState<Record<string, CompoundPreset>>({});
  const [summaryText, setSummaryText] = useState<string | null>(null);

  const effectiveScore = useMemo(() => {
    if (!drug) return 0;
    let score = drug.score;
    if (dose > 2) score = Math.max(5, score - (dose - 2) * 15);
    else if (dose > 1) score = Math.max(10, score - (dose - 1) * 8);
    return Math.round(score);
  }, [dose, drug]);

  useEffect(() => {
    let isMounted = true;

    async function loadBackendContext() {
      const healthy = await checkBackendHealth();
      if (!isMounted) return;
      setApiOnline(healthy);
      if (!healthy) return;

      try {
        const compounds = await fetchCompounds();
        if (!isMounted || compounds.length === 0) return;

        const nextLookup = compounds.reduce<Record<string, CompoundPreset>>((acc, item) => {
          acc[item.name] = item;
          return acc;
        }, {});

        setCompoundLookup(nextLookup);
        setPresets(compounds.slice(0, 5).map((item) => item.name));
      } catch {
        setApiOnline(false);
      }
    }

    void loadBackendContext();
    return () => { isMounted = false; };
  }, []);

  function resolveCompoundPreset(value: string): CompoundPreset | undefined {
    const exact = compoundLookup[value];
    if (exact) return exact;
    return Object.values(compoundLookup).find((item) => {
      if (item.name.toLowerCase() === value.toLowerCase()) return true;
      return item.aliases?.some((alias) => alias.toLowerCase() === value.toLowerCase());
    });
  }

  function looksLikeSmiles(value: string): boolean {
    return /[=#[\]()]/.test(value) || /[A-Z][a-z]?\d?/.test(value);
  }

  function selectPreset(name: string) {
    setSelectedPreset(name);
    setSelectedDrugLabel(name);
    setInputValue(name);
    setDose(1.0);
    setErrorMessage(null);
  }

  async function analyzeDrug(nameOverride?: string) {
    const val = (nameOverride ?? inputValue).trim();
    if (!val) return;

    setIsAnalyzing(true);
    setErrorMessage(null);
    setCurrentPage("results");
    window.scrollTo(0, 0);

    const compound = resolveCompoundPreset(val);
    const smilesInput = looksLikeSmiles(val);
    const requestPayload = {
      drug_name: compound?.name ?? (smilesInput ? "" : val),
      smiles: compound ? "" : smilesInput ? val : "",
      compound_id: compound?.id,
      dose_mg: Math.max(1, dose * 100),
      route: "oral",
    };

    try {
      const prediction = await fetchPrediction(requestPayload);
      const mappedDrug = mapPredictionToDrug(prediction);
      setDrug(mappedDrug);
      setSelectedDrugLabel(mappedDrug.name);
      setSelectedPreset(compound?.name ?? null);

      const summary = await fetchSummary(requestPayload);
      setSummaryText(summary);

      setCurrentPage("results");
      window.scrollTo(0, 0);
    } catch (err) {
      console.error("Prediction failed:", err);
      setErrorMessage("Backend prediction failed. Please check your connection and try again.");
      setCurrentPage("input");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handlePresetAnalyze(name: string) {
    selectPreset(name);
    await analyzeDrug(name);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") void analyzeDrug();
  }

  return (
    <>
      <Navbar currentPage={currentPage} onPageChange={setCurrentPage} hasResults={Boolean(drug)} />
      <div className="glow-orb-2" />

      <main>
        {/* ===================== INPUT PAGE ===================== */}
        {currentPage === "input" && (
          <>
            <div className="hero">
              <div className="hero-label">Pre-clinical drug safety simulation</div>
              <h1>
                Test any drug <span>before</span>
                <br />
                it reaches a patient.
              </h1>
              <p className="hero-sub">
                Enter a drug name or SMILES string. PharmaSim predicts how it moves
                through the body, where it accumulates, and whether it&apos;s safe
                before any lab testing.
              </p>

              <div className="input-row">
                <div className="drug-input-wrap">
                  <input
                    type="text"
                    className="drug-input"
                    placeholder="e.g. Tylenol, CC(=O)Nc1ccc(O)cc1..."
                    autoComplete="off"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                  />
                </div>
                <button
                  className="analyze-btn"
                  onClick={() => void analyzeDrug()}
                  disabled={isAnalyzing}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                  {isAnalyzing ? "Analyzing..." : "Analyze"}
                </button>
              </div>

              {errorMessage && (
                <p style={{ marginTop: "10px", color: "var(--amber)", fontSize: "12px" }}>
                  {errorMessage}
                </p>
              )}

              <div className="preset-drugs">
                <span className="preset-label">PRESETS:</span>
                {presets.map((name) => (
                  <div
                    key={name}
                    className={`preset-chip${selectedPreset === name ? " active" : ""}`}
                    onClick={() => void handlePresetAnalyze(name)}
                  >
                    {name}
                  </div>
                ))}
              </div>
            </div>

            <div className="status-bar">
              <div className="status-item">
                <div className="status-dot" style={{ background: apiOnline ? "var(--green)" : "var(--red)" }} />
                API {apiOnline ? "connected" : "offline"}
              </div>
              <div className="status-item">
                <div className="status-dot" style={{ background: "var(--green)" }} />
                ADMET model ready
              </div>
              <div className="status-item">
                <div className="status-dot" style={{ background: "var(--accent)" }} />
                PK engine online
              </div>
            </div>
          </>
        )}

        {/* ===================== RESULTS PAGE ===================== */}
        {currentPage === "results" && (
          <>
            {isAnalyzing ? (
              <div className="analysis-inline-shell" role="status" aria-live="polite" aria-label="Running analysis">
                <div className="results-header">
                  <p className="results-eyebrow">Safety Analysis</p>
                  <h2 className="results-title">Analyzing...</h2>
                  <p className="results-subtitle">Running prediction models on the backend.</p>
                </div>
                <div className="analysis-inline-card analysis-main-card">
                  <div className="analysis-hero-row">
                    <motion.div
                      animate={{
                        scale: [1, 1.15, 1.15, 1, 1],
                        rotate: [0, 0, 180, 180, 0],
                        borderRadius: ["0%", "0%", "50%", "50%", "0%"],
                      }}
                      transition={{
                        duration: 2,
                        ease: "easeInOut",
                        times: [0, 0.2, 0.5, 0.8, 1],
                        repeat: Infinity,
                        repeatDelay: 1,
                      }}
                      style={box}
                      className="analysis-shape"
                      aria-hidden="true"
                    />
                    <div className="analysis-hero-copy">
                      <p className="analysis-eyebrow">PharmaSim compute pipeline</p>
                      <h3 className="analysis-title">Analyzing {inputValue.trim() || "compound"}</h3>
                      <p className="analysis-sub">Running models on the backend—usually a few seconds.</p>
                    </div>
                  </div>
                  <div className="analysis-lines analysis-lines-compact" aria-hidden="true">
                    <span className="analysis-line" />
                    <span className="analysis-line" />
                    <span className="analysis-line" />
                  </div>
                </div>

                <div className="analysis-steps-grid">
                  {analysisPipelineSteps.map((step, i) => (
                    <div key={step.id} className="analysis-step-card" style={{ animationDelay: `${i * 0.08}s` }}>
                      <div className="analysis-step-icon" aria-hidden="true">
                        {step.id === "structure" && (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <circle cx="9" cy="9" r="2.2" /><circle cx="15" cy="7" r="2.2" /><circle cx="13" cy="15" r="2.2" />
                            <path d="M10.8 10.2l2.4-1.8M11.2 13.2l1.2-2.4M13.5 8.8l2 1.8" />
                          </svg>
                        )}
                        {step.id === "admet" && (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <path d="M9 3h6v4H9zM7 21h10v-8H7zM12 7v4" /><path d="M10 17h4" />
                          </svg>
                        )}
                        {step.id === "pk" && (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <path d="M4 18c3-6 5-9 8-9s4 3 8 9" /><circle cx="12" cy="9" r="2" />
                          </svg>
                        )}
                        {step.id === "safety" && (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                            <path d="M12 3l8 4v6c0 5-3.5 9-8 11-4.5-2-8-6-8-11V7z" /><path d="M9 12l2 2 4-4" />
                          </svg>
                        )}
                      </div>
                      <div className="analysis-step-body">
                        <div className="analysis-step-label">{step.label}</div>
                        <div className="analysis-step-detail">{step.detail}</div>
                      </div>
                      <span className="analysis-step-badge">In progress</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : drug ? (
              <>
                <div className="results-header">
                  <p className="results-eyebrow">Safety Analysis</p>
                  <h2 className="results-title">{drug.name}</h2>
                  <p className="results-subtitle">
                    {effectiveScore >= 70
                      ? "This compound shows a favorable safety profile at standard dosing."
                      : effectiveScore >= 40
                      ? "This compound requires additional monitoring due to moderate risk factors."
                      : "This compound has significant safety concerns that require careful evaluation."}
                  </p>
                </div>
                <div className="dashboard results-dashboard">
                  <SafetyScoreCard
                    drug={drug}
                    dose={dose}
                    effectiveScore={effectiveScore}
                    onDoseChange={setDose}
                    summaryText={null}
                  />
                  <RiskCard drug={drug} />
                </div>
              </>
            ) : null}

            {summaryText && !isAnalyzing && (
              <div className="gemini-summary-wrap">
                <div className="gemini-summary-card gemini-summary-card--compact">
                  <div className="gemini-summary-card-head">
                    <div className="gemini-summary-icon" aria-hidden="true">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                        <path d="M12 3c4.97 0 9 3.58 9 8 0 4.42-4.03 8-9 8-.83 0-1.64-.09-2.41-.26L3 21l1.47-5.11A7.94 7.94 0 0 1 3 11c0-4.42 4.03-8 9-8z" />
                      </svg>
                    </div>
                    <div>
                      <div className="gemini-summary-eyebrow">AI narrative</div>
                      <div className="gemini-summary-heading">Gemini summary</div>
                    </div>
                  </div>
                  <p className="gemini-summary-text">{summaryText}</p>
                </div>
              </div>
            )}

            <div className="page-nav-row">
              <button className="page-nav-btn" onClick={() => setCurrentPage("input")}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
                </svg>
                New Analysis
              </button>
              <button className="page-nav-btn page-nav-primary" onClick={() => { setCurrentPage("science"); window.scrollTo(0, 0); }}>
                View Scientific Details
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14" /><polyline points="12 5 19 12 12 19" />
                </svg>
              </button>
            </div>
          </>
        )}

        {/* ===================== SCIENCE PAGE ===================== */}
        {currentPage === "science" && drug && (
          <>
            <div className="science-page-stack">
              <div className="science-status-card">
                <div className="science-status-card-head">
                  <span className="science-status-card-eyebrow">Live pipeline</span>
                  <span className="science-status-card-title">Engine status</span>
                </div>
                <div className="science-status-pills">
                  <div className="science-status-pill">
                    <div className="status-dot" style={{ background: "var(--green)" }} />
                    RDKit
                  </div>
                  <div className="science-status-pill">
                    <div className="status-dot" style={{ background: "var(--green)" }} />
                    ML model
                  </div>
                  <div className="science-status-pill">
                    <div className="status-dot" style={{ background: "var(--accent)" }} />
                    PK engine
                  </div>
                  <div className="science-status-pill science-status-pill-highlight">
                    <div className="status-dot" style={{ background: "var(--amber)" }} />
                    Compound <strong>{drug.name}</strong>
                  </div>
                </div>
              </div>

              {drug.disclaimer && (
                <div className="science-disclaimer-card" role="note">
                  <div className="science-disclaimer-icon" aria-hidden="true">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
                    </svg>
                  </div>
                  <div>
                    <div className="science-disclaimer-label">Disclaimer</div>
                    <p className="science-disclaimer-text">{drug.disclaimer}</p>
                  </div>
                </div>
              )}

              <div className="science-intro-card">
                <h2 className="science-intro-title">
                  Scientific analysis <span className="science-intro-accent">{drug.name}</span>
                </h2>
                <p className="science-sub">
                  Pharmacokinetic curves, organ distribution, and metabolic pathway breakdown.
                </p>
              </div>
            </div>

            <div className="dashboard science-dashboard science-dashboard-compact">
              <PKMetricsCard drug={drug} />
              <PKChart drug={drug} dose={dose} />
              <OrganMap drug={drug} />
              <PathwayCard drug={drug} drugKey={selectedDrugLabel} />
            </div>

            {summaryText && (
              <div className="gemini-summary-wrap">
                <div className="gemini-summary-card">
                  <div className="gemini-summary-card-head">
                    <div className="gemini-summary-icon" aria-hidden="true">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
                        <path d="M12 3c4.97 0 9 3.58 9 8 0 4.42-4.03 8-9 8-.83 0-1.64-.09-2.41-.26L3 21l1.47-5.11A7.94 7.94 0 0 1 3 11c0-4.42 4.03-8 9-8z" />
                      </svg>
                    </div>
                    <div>
                      <div className="gemini-summary-eyebrow">AI narrative</div>
                      <div className="gemini-summary-heading">Gemini summary</div>
                    </div>
                  </div>
                  <p className="gemini-summary-text">{summaryText}</p>
                </div>
              </div>
            )}

            <div className="page-nav-row">
              <button className="page-nav-btn" onClick={() => { setCurrentPage("results"); window.scrollTo(0, 0); }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
                </svg>
                Back to Safety Score
              </button>
              <button className="page-nav-btn" onClick={() => setCurrentPage("input")}>
                New Analysis
              </button>
            </div>
          </>
        )}
      </main>
    </>
  );
}
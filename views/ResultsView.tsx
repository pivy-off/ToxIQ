"use client";

import * as motion from "motion/react-client";
import SafetyScoreCard from "@/components/SafetyScoreCard";
import RiskCard from "@/components/RiskCard";
import type { AppState, AppAction } from "@/lib/appState";

const box = {
  width: 62,
  height: 62,
  backgroundColor: "#f5f5f5",
  borderRadius: 5,
};

const analysisPipelineSteps = [
  { id: "structure", label: "Molecular structure", detail: "SMILES validation & RDKit features" },
  { id: "admet", label: "ADMET screening", detail: "Absorption, distribution, metabolism" },
  { id: "pk", label: "PK simulation", detail: "One-compartment oral curve" },
  { id: "safety", label: "Safety synthesis", detail: "Risk tiles & composite score" },
] as const;

interface Props {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  effectiveScore: number;
}

export default function ResultsView({ state, dispatch, effectiveScore }: Props) {
  const { drug, isAnalyzing, inputValue, dose, summaryText } = state;

  if (isAnalyzing) {
    return (
      <>
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
                <p className="analysis-eyebrow">ToxIQ compute pipeline</p>
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

        <div className="page-nav-row">
          <button className="page-nav-btn" onClick={() => dispatch({ type: "SET_PAGE", page: "input" })}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
            </svg>
            Cancel
          </button>
        </div>
      </>
    );
  }

  if (!drug) return null;

  return (
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
          onDoseChange={(d) => dispatch({ type: "SET_DOSE", dose: d })}
          summaryText={null}
        />
        <RiskCard drug={drug} />
      </div>

      {summaryText && (
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
        <button className="page-nav-btn" onClick={() => dispatch({ type: "SET_PAGE", page: "input" })}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
          </svg>
          New Analysis
        </button>
        <button
          className="page-nav-btn page-nav-primary"
          onClick={() => { dispatch({ type: "SET_PAGE", page: "science" }); window.scrollTo(0, 0); }}
        >
          View Scientific Details
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14" /><polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>
    </>
  );
}

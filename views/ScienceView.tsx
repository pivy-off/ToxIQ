"use client";

import PKMetricsCard from "@/components/PKMetricsCard";
import PKChart from "@/components/PKChart";
import OrganMap from "@/components/OrganMap";
import PathwayCard from "@/components/PathwayCard";
import type { AppState, AppAction } from "@/lib/appState";

interface Props {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

export default function ScienceView({ state, dispatch }: Props) {
  const { drug, dose, selectedDrugLabel, summaryText } = state;

  if (!drug) return null;

  return (
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
        <button
          className="page-nav-btn"
          onClick={() => { dispatch({ type: "SET_PAGE", page: "results" }); window.scrollTo(0, 0); }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
          </svg>
          Back to Safety Score
        </button>
        <button className="page-nav-btn" onClick={() => dispatch({ type: "SET_PAGE", page: "input" })}>
          New Analysis
        </button>
      </div>
    </>
  );
}

"use client";

import type { AppState, AppAction } from "@/lib/appState";

interface Props {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  onAnalyze: (nameOverride?: string) => void;
}

export default function InputView({ state, dispatch, onAnalyze }: Props) {
  const { inputValue, isAnalyzing, errorMessage, apiOnline, presets, selectedPreset } = state;

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") void onAnalyze();
  }

  function handlePresetClick(name: string) {
    dispatch({ type: "SELECT_PRESET", name });
    void onAnalyze(name);
  }

  return (
    <>
      <div className="hero">
        <div className="hero-label">Pre-clinical drug safety simulation</div>
        <h1>
          Test any drug <span>before</span>
          <br />
          it reaches a patient.
        </h1>
        <p className="hero-sub">
          Enter a drug name or SMILES string. ToxIQ predicts how it moves
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
              onChange={(e) => dispatch({ type: "SET_INPUT", value: e.target.value })}
              onKeyDown={handleKeyDown}
            />
          </div>
          <button
            className="analyze-btn"
            onClick={() => void onAnalyze()}
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
              onClick={() => handlePresetClick(name)}
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
  );
}

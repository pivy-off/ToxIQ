"use client";

import { Drug } from "@/lib/drugData";

interface Props {
  drug: Drug;
  dose: number;
  effectiveScore: number;
  onDoseChange: (dose: number) => void;
  summaryText?: string | null;
}

export default function SafetyScoreCard({
  drug,
  dose,
  effectiveScore,
  onDoseChange,
  summaryText,
}: Props) {
  const circumference = 251;
  const offset = circumference - (effectiveScore / 100) * circumference;
  const color =
    effectiveScore >= 70 ? "#34c759" : effectiveScore >= 40 ? "#ff9500" : "#ff3b30";

  const doseLabel = `${dose.toFixed(1)}\u00D7`;
  const isToxicDose = dose > 5;

  const verdict =
    isToxicDose        ? "TOXIC"       :
    effectiveScore >= 70 ? "SAFE"      :
    effectiveScore >= 40 ? "ACCEPTABLE" : "HIGH RISK";

  const verdictColor =
    isToxicDose          ? "#ff3b30" :
    effectiveScore >= 70 ? "#34c759" :
    effectiveScore >= 40 ? "#ff9500" : "#ff3b30";

  const badgeTxt =
    isToxicDose          ? "Toxic"        :
    effectiveScore >= 70 ? "Trial Ready"  :
    effectiveScore >= 40 ? "Monitor"      : "High Risk";

  const badgeType: "safe" | "warn" | "danger" =
    isToxicDose          ? "danger" :
    effectiveScore >= 70 ? "safe"   :
    effectiveScore >= 40 ? "warn"   : "danger";

  return (
    <div className="card card-safety">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" />
          Safety Score
        </div>
        <div className={`score-tag tag-${badgeType}`}>{badgeTxt}</div>
      </div>
      <div className="card-body">
        <div className="safety-score-display">
          <div className="score-circle">
            <svg viewBox="0 0 100 100">
              <circle className="score-circle-track" cx="50" cy="50" r="40" />
              <circle
                className="score-circle-fill"
                cx="50"
                cy="50"
                r="40"
                style={{
                  stroke: color,
                  strokeDashoffset: offset,
                }}
              />
            </svg>
            <div className="score-number">
              {Math.round(effectiveScore)}
              <span>/100</span>
            </div>
          </div>
          <div className="score-details">
            <div className="score-verdict" style={{ color: verdictColor }}>
              {verdict}
            </div>
            <div className="score-drug-name">{drug.name}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
              {drug.flags.map((flag, i) => (
                <span key={i} className={`score-tag tag-${drug.flagTypes[i]}`}>
                  {flag}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="trial-rec">
          <div className="trial-text">
            <h3
              style={{
                color: isToxicDose ? "var(--red)" : drug.trialColor,
              }}
            >
              {isToxicDose ? "\u26A0 Toxic dose \u2014 Do not proceed" : drug.trialTitle}
            </h3>
            <p>{drug.trialDesc}</p>
          </div>
        </div>

        {summaryText && (
          <div style={{ marginTop: "12px", borderTop: "1px solid var(--line)", paddingTop: "10px" }}>
            <div className="smiles-label">Current summary</div>
            <p style={{ marginTop: "6px", color: "var(--text2)", lineHeight: 1.45 }}>{summaryText}</p>
          </div>
        )}

        <div style={{ marginTop: "14px" }}>
          <div className="smiles-label">SMILES string</div>
          <div className="smiles-display">{drug.smiles}</div>
        </div>
      </div>
      <div className="dose-section">
        <div className="dose-label">
          <span>Dose multiplier</span>
          <span className="dose-value">{doseLabel}</span>
        </div>
        <input
          type="range"
          min={1}
          max={10}
          step={0.5}
          value={dose}
          onChange={(e) => onDoseChange(parseFloat(e.target.value))}
        />
      </div>
    </div>
  );
}

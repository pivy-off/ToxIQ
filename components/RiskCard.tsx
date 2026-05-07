"use client";

import { Drug } from "@/lib/drugData";

const barColors: Record<string, string> = {
  safe: "#5a7a4e",
  warn: "#d4a84b",
  danger: "#c94f3f",
};

interface Props {
  drug: Drug;
}

export default function RiskCard({ drug }: Props) {
  return (
    <div className="card card-risks">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" style={{ background: "var(--amber)" }} />
          Risk Assessment
        </div>
      </div>
      <div className="card-body">
        <div className="risk-list">
          {drug.risks.map((r, i) => (
            <div className="risk-item" key={i}>
              <div
                style={{
                  width: 3,
                  height: 30,
                  background: barColors[r.level],
                  flexShrink: 0,
                  borderRadius: 0,
                }}
              />
              <div className="risk-text">
                <div className="risk-name">{r.name}</div>
                <div className="risk-desc">{r.desc}</div>
              </div>
              <div className={`risk-badge badge-${r.level}`}>{r.badge}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

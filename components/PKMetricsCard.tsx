"use client";

import { Drug } from "@/lib/drugData";

const metricConfig = [
  { key: "absorption" as const, label: "Absorption Rate", unit: "ka (h\u207B\u00B9)" },
  { key: "clearance" as const, label: "Clearance", unit: "L/hr" },
  { key: "vd" as const, label: "Volume of Dist.", unit: "L/kg" },
  { key: "halflife" as const, label: "Half-Life", unit: "hours" },
  { key: "bio" as const, label: "Bioavailability", unit: "%" },
  { key: "protein" as const, label: "Protein Binding", unit: "%" },
];

interface Props {
  drug: Drug;
}

export default function PKMetricsCard({ drug }: Props) {
  return (
    <div className="card card-metrics">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" style={{ background: "var(--purple)" }} />
          PK Parameters
        </div>
        <div style={{ fontSize: "10px", color: "var(--text3)" }}>Predicted</div>
      </div>
      <div className="card-body">
        <div className="metrics-grid">
          {metricConfig.map((m) => (
            <div className="metric-item" key={m.key}>
              <div className="metric-label">{m.label}</div>
              <div className="metric-value">{drug.pk[m.key]}</div>
              <div className="metric-unit">{m.unit}</div>
              <div className="metric-bar">
                <div
                  className="metric-bar-fill"
                  style={{
                    width: `${drug.pkBars[m.key]}%`,
                    background: drug.pkColors[m.key],
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

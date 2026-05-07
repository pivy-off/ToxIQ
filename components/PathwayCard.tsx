"use client";

import { Drug } from "@/lib/drugData";

interface Props {
  drug: Drug;
  drugKey: string;
}

export default function PathwayCard({ drug, drugKey }: Props) {
  return (
    <div className="card card-pathway">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" style={{ background: "var(--green)" }} />
          Drug Mechanism Pathway
        </div>
        <div style={{ fontSize: "10px", color: "var(--text3)" }}>{drugKey}</div>
      </div>
      <div className="card-body">
        <div className="pathway-steps">
          {drug.pathway.map((step, i) => (
            <div className="pathway-step" key={i}>
              <div className={`step-num${i < 3 ? " active" : ""}`}>{i + 1}</div>
              <div className="step-title">{step.title}</div>
              <div className="step-desc">{step.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

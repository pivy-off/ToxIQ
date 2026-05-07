"use client";

import { useState } from "react";
import { Drug } from "@/lib/drugData";

interface Props { drug: Drug; }
type OrganKey = "brain" | "lungs" | "heart" | "liver" | "kidneys";

const ORGANS: { key: OrganKey; label: string; solid: string; icon: string }[] = [
  { key: "brain",   label: "Brain",   solid: "#9b6fc5", icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" },
  { key: "lungs",   label: "Lungs",   solid: "#3d8ba8", icon: "M12 3c-1.1 0-2 .9-2 2v5.5C8.4 11.2 7 12.7 7 14.5 7 16.4 8.6 18 10.5 18c.8 0 1.6-.3 2.2-.8l.3-.3.3.3c.6.5 1.4.8 2.2.8 1.9 0 3.5-1.6 3.5-3.5 0-1.8-1.4-3.3-3-3.9V5c0-1.1-.9-2-2-2z" },
  { key: "heart",   label: "Heart",   solid: "#c2463b", icon: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" },
  { key: "liver",   label: "Liver",   solid: "#c58e23", icon: "M17 8C8 10 5.9 16.17 3.82 19.34 2.96 20.62 4 22 5.5 22c.97 0 1.87-.52 2.35-1.36C9 18 12 17 17 17c3.87 0 7-3.13 7-7s-3.13-7-7-7z" },
  { key: "kidneys", label: "Kidneys", solid: "#4f7252", icon: "M12 2C6.48 2 2 6.48 2 12c0 3.7 2.02 6.93 5 8.66V20c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2v-.34c2.98-1.73 5-4.96 5-8.66 0-5.52-4.48-10-10-10z" },
];

export default function OrganMap({ drug }: Props) {
  const [expanded, setExpanded] = useState<OrganKey | null>(null);
  const p = drug.organPercentages;

  const pct: Record<OrganKey, number> = {
    brain:   Math.round(p?.brain   ?? 11),
    lungs:   Math.round(p?.lungs   ?? 11),
    heart:   Math.round(p?.heart   ??  8),
    liver:   Math.round(p?.liver   ?? 30),
    kidneys: Math.round(p?.kidneys ?? 15),
  };

  function toggle(k: OrganKey) {
    setExpanded(prev => prev === k ? null : k);
  }

  return (
    <div className="card card-body-map">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" style={{ background: "var(--green)" }} />
          Organ Distribution
        </div>
      </div>

      <div className="card-body organ-list-body">
        {ORGANS.map(({ key, label, solid }) => {
          const val = pct[key];
          const open = expanded === key;
          return (
            <div key={key} className={`organ-row${open ? " open" : ""}`}
              onClick={() => toggle(key)}>
              <div className="organ-row-main">
                <div className="organ-row-dot" style={{ background: solid }} />
                <div className="organ-row-info">
                  <div className="organ-row-header">
                    <span className="organ-row-label">{label}</span>
                    <span className="organ-row-pct" style={{ color: solid }}>{val}%</span>
                  </div>
                  <div className="organ-row-track">
                    <div className="organ-row-fill"
                      style={{ width: `${val}%`, background: solid }} />
                  </div>
                </div>
                <svg className={`organ-row-chevron${open ? " rotated" : ""}`}
                  width="12" height="12" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2.2"
                  strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </div>

              {open && (
                <div className="organ-row-detail">
                  {drug.organDetail[key]}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

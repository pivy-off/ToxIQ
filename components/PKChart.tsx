"use client";

import { useEffect, useRef } from "react";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  Tooltip,
  Filler,
} from "chart.js";
import { Drug, generatePK } from "@/lib/drugData";

Chart.register(LineController, LineElement, PointElement, LinearScale, Tooltip, Filler);

interface Props {
  drug: Drug;
  dose: number;
}

export default function PKChart({ drug, dose }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");
    if (!ctx) return;

    const pk =
      drug.pkData && drug.pkData.times.length > 0 && drug.pkData.conc.length > 0
        ? {
            times: drug.pkData.times,
            conc: drug.pkData.conc.map((value) => value * dose),
          }
        : generatePK(drug.pk.absorption, drug.pk.clearance, drug.pk.vd, 1000, dose);
    const maxConc = Math.max(...pk.conc);
    const therapeutic = maxConc * 0.3;
    const toxic = maxConc * 0.75;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, "rgba(0, 113, 227, 0.15)");
    gradient.addColorStop(1, "rgba(0, 113, 227, 0.01)");

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Plasma Concentration",
            data: pk.conc.map((c, i) => ({ x: pk.times[i], y: parseFloat(c.toFixed(3)) })),
            borderColor: "#0071e3",
            backgroundColor: gradient,
            borderWidth: 2.5,
            pointRadius: 0,
            tension: 0.4,
            fill: true,
          },
          {
            label: "Therapeutic min",
            data: [
              { x: 0, y: therapeutic },
              { x: 12, y: therapeutic },
            ],
            borderColor: "rgba(52, 199, 89, 0.5)",
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
          },
          {
            label: "Toxic threshold",
            data: [
              { x: 0, y: toxic },
              { x: 12, y: toxic },
            ],
            borderColor: "rgba(255, 59, 48, 0.5)",
            borderWidth: 1.5,
            borderDash: [6, 4],
            pointRadius: 0,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        parsing: false,
        scales: {
          x: {
            type: "linear",
            title: { display: true, text: "Time (hours)", color: "#86868b", font: { size: 12, weight: 500 } },
            ticks: { color: "#86868b", font: { size: 11 }, stepSize: 2 },
            grid: { color: "rgba(0,0,0,0.04)" },
            border: { display: false },
            min: 0,
            max: 12,
          },
          y: {
            title: {
              display: true,
              text: "Concentration (mg/L)",
              color: "#86868b",
              font: { size: 12, weight: 500 },
            },
            ticks: { color: "#86868b", font: { size: 11 } },
            grid: { color: "rgba(0,0,0,0.04)" },
            border: { display: false },
            min: 0,
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#fff",
            borderColor: "rgba(0,0,0,0.1)",
            borderWidth: 1,
            titleColor: "#86868b",
            bodyColor: "#1d1d1f",
            cornerRadius: 8,
            padding: 12,
            titleFont: { size: 12, weight: 500 },
            bodyFont: { size: 14, weight: 600 },
            callbacks: {
              title: (items) => `t = ${items[0].parsed.x}h`,
              label: (item) => ` ${(item.parsed.y ?? 0).toFixed(3)} mg/L`,
            },
          },
        },
        animation: { duration: 1000, easing: "easeOutQuart" },
      },
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [drug, dose]);

  return (
    <div className="card card-chart">
      <div className="card-header">
        <div className="card-title">
          <div className="card-title-dot" style={{ background: "var(--accent)" }} />
          Concentration vs Time
        </div>
        <div style={{ fontSize: "10px", color: "var(--text3)" }}>
          Plasma curve (PK simulation)
        </div>
      </div>
      <div className="card-body">
        <div className="chart-legend">
          <div className="legend-item">
            <div className="legend-dot" style={{ background: "#0071e3" }} />
            Plasma concentration
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: "#34c759" }} />
            Therapeutic window
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: "#ff3b30" }} />
            Toxic threshold
          </div>
        </div>
        <div className="chart-wrap">
          <canvas ref={canvasRef} />
        </div>
      </div>
    </div>
  );
}

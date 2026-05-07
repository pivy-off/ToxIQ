"use client";

type Page = "input" | "results" | "science";

interface Props {
  currentPage: Page;
  onPageChange: (page: Page) => void;
  hasResults: boolean;
}

export default function Navbar({ currentPage, onPageChange, hasResults }: Props) {
  return (
    <nav>
      <div className="nav-logo" onClick={() => onPageChange("input")} style={{ cursor: "pointer" }}>
        <div className="nav-logo-dot" />
        PharmaSim
      </div>
      <ul className="nav-links">
        <li>
          <a
            href="#"
            className={currentPage === "input" ? "nav-active" : ""}
            onClick={(e) => { e.preventDefault(); onPageChange("input"); }}
          >
            Simulator
          </a>
        </li>
        <li>
          <a
            href="#"
            className={`${currentPage === "results" ? "nav-active" : ""} ${!hasResults ? "nav-disabled" : ""}`}
            onClick={(e) => { e.preventDefault(); if (hasResults) onPageChange("results"); }}
          >
            Safety Score
          </a>
        </li>
        <li>
          <a
            href="#"
            className={`${currentPage === "science" ? "nav-active" : ""} ${!hasResults ? "nav-disabled" : ""}`}
            onClick={(e) => { e.preventDefault(); if (hasResults) onPageChange("science"); }}
          >
            Scientific Details
          </a>
        </li>
      </ul>
      <div className="nav-badge">BETA v0.1</div>
    </nav>
  );
}

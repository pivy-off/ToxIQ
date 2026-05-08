/**
 * Drug data types and interfaces.
 * No hardcoded fallback data - all data comes from the backend API.
 */

export interface PKParams {
  absorption: number;
  clearance: number;
  vd: number;
  halflife: number;
  bio: number;
  protein: number;
}

export interface PKBars {
  absorption: number;
  clearance: number;
  vd: number;
  halflife: number;
  bio: number;
  protein: number;
}

export interface PKColors {
  absorption: string;
  clearance: string;
  vd: string;
  halflife: string;
  bio: string;
  protein: string;
}

export interface Risk {
  name: string;
  desc: string;
  level: "safe" | "warn" | "danger";
  badge: string;
}

export interface PathwayStep {
  title: string;
  desc: string;
}

export interface PKData {
  times: number[];
  conc: number[];
}

export interface OrganDetail {
  brain: string;
  lungs: string;
  heart: string;
  liver: string;
  kidneys: string;
}

export interface Drug {
  name: string;
  smiles: string;
  score: number;
  verdict: string;
  verdictColor: string;
  trialReady: boolean;
  trialTitle: string;
  trialDesc: string;
  trialColor: string;
  trialIcon: string;
  trialBg: string;
  pk: PKParams;
  pkBars: PKBars;
  pkColors: PKColors;
  risks: Risk[];
  flags: string[];
  flagTypes: ("safe" | "warn" | "danger")[];
  badgeTxt: string;
  badgeType: "safe" | "warn" | "danger";
  pathway: PathwayStep[];
  organDetail: OrganDetail;
  pkData?: PKData;
  organPercentages?: Partial<Record<keyof OrganDetail | "bloodstream", number>>;
  disclaimer?: string;
}

export function generatePK(
  ka: number,
  cl: number,
  vd: number,
  dose: number,
  multiplier: number
): PKData {
  const F = 0.85;
  const points = 24;
  const times = Array.from({ length: points }, (_, i) => i * 0.5);
  const realDose = dose * multiplier;
  const ke = cl / (vd * 70);
  const conc = times.map((t) => {
    if (t === 0) return 0;
    return (
      ((F * realDose * ka) / (vd * 70 * (ka - ke))) *
      (Math.exp(-ke * t) - Math.exp(-ka * t))
    );
  });
  return { times, conc };
}

export function createEmptyDrug(): Drug {
  return {
    name: "",
    smiles: "",
    score: 0,
    verdict: "UNKNOWN",
    verdictColor: "var(--text-secondary)",
    trialReady: false,
    trialTitle: "Loading...",
    trialDesc: "Analyzing compound...",
    trialColor: "var(--text-secondary)",
    trialIcon: "...",
    trialBg: "var(--bg-tertiary)",
    pk: { absorption: 0, clearance: 0, vd: 0, halflife: 0, bio: 0, protein: 0 },
    pkBars: { absorption: 0, clearance: 0, vd: 0, halflife: 0, bio: 0, protein: 0 },
    pkColors: {
      absorption: "var(--accent)",
      clearance: "var(--accent)",
      vd: "var(--accent)",
      halflife: "var(--accent)",
      bio: "var(--accent)",
      protein: "var(--accent)",
    },
    risks: [],
    flags: [],
    flagTypes: [],
    badgeTxt: "Loading",
    badgeType: "warn",
    pathway: [],
    organDetail: {
      brain: "",
      lungs: "",
      heart: "",
      liver: "",
      kidneys: "",
    },
  };
}

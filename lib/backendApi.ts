import { Drug, OrganDetail, PathwayStep, Risk } from "@/lib/drugData";

export interface CompoundPreset {
  id: string;
  name: string;
  smiles?: string;
  default_dose_mg?: number;
  aliases?: string[];
}

interface HealthResponse {
  status: string;
}

interface CompoundsResponse {
  compounds: CompoundPreset[];
}

interface SummaryResponse {
  drug_name: string;
  summary: string;
}

interface PredictResponse {
  compound: {
    name: string;
    smiles: string;
    route: string;
    dose_mg: number;
    compound_id?: string | null;
  };
  verdict?: string;
  pk_display?: {
    absorption_ka_per_h?: number;
    clearance_l_per_h?: number;
    volume_distribution_l_per_kg?: number;
    half_life_hours?: number;
    bioavailability_percent?: number;
    protein_binding_percent?: number;
  };
  pk_curve?: {
    time_hours?: number[];
    concentration_mg_per_l?: number[];
  };
  safety_score?: {
    score?: number;
  };
  risk_assessment?: Array<{
    name?: string;
    description?: string;
    level?: "safe" | "warn" | "danger";
    badge?: string;
  }>;
  display_flags?: Array<{
    text?: string;
    level?: "safe" | "warn" | "danger";
  }>;
  trial_recommendation?: {
    trial_ready?: boolean;
    title?: string;
    description?: string;
    badge?: "safe" | "warn" | "danger";
  };
  reaction_pathway?: Array<{
    title?: string;
    description?: string;
  }>;
  organ_distribution?: {
    percentages?: Partial<Record<keyof OrganDetail | "bloodstream", number>>;
    organ_notes?: Partial<Record<keyof OrganDetail, string>>;
  };
  disclaimer?: string;
}

const API_PREFIX = "/api/backend";

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const bodyText = await response.text();
    throw new Error(bodyText || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const health = await requestJson<HealthResponse>("/health");
    return health.status?.toLowerCase?.() === "ok";
  } catch {
    return false;
  }
}

export async function fetchCompounds(): Promise<CompoundPreset[]> {
  const result = await requestJson<CompoundsResponse>("/compounds");
  return result.compounds ?? [];
}

export async function fetchPrediction(payload: {
  drug_name: string;
  smiles?: string;
  route?: string;
  dose_mg?: number;
  compound_id?: string;
}): Promise<PredictResponse> {
  return requestJson<PredictResponse>("/predict/", {
    method: "POST",
    body: JSON.stringify({
      route: payload.route ?? "oral",
      dose_mg: payload.dose_mg ?? 100,
      ...payload,
    }),
  });
}

export async function fetchSummary(payload: {
  drug_name: string;
  smiles?: string;
  route?: string;
  dose_mg?: number;
  compound_id?: string;
}): Promise<string | null> {
  try {
    const result = await requestJson<SummaryResponse>("/summary/", {
      method: "POST",
      body: JSON.stringify({
        route: payload.route ?? "oral",
        dose_mg: payload.dose_mg ?? 100,
        ...payload,
      }),
    });
    return result.summary?.trim() || null;
  } catch {
    return null;
  }
}

function verdictColorForScore(score: number): string {
  if (score >= 70) return "var(--green)";
  if (score >= 40) return "var(--amber)";
  return "var(--red)";
}

function buildPkBars(pk: Drug["pk"]): Drug["pkBars"] {
  return {
    absorption: clamp(Math.round(pk.absorption * 100), 5, 100),
    clearance: clamp(Math.round((pk.clearance / 40) * 100), 5, 100),
    vd: clamp(Math.round((pk.vd / 4) * 100), 5, 100),
    halflife: clamp(Math.round((pk.halflife / 12) * 100), 5, 100),
    bio: clamp(Math.round(pk.bio), 0, 100),
    protein: clamp(Math.round(pk.protein), 0, 100),
  };
}

function defaultRiskRows(): Risk[] {
  return [
    {
      name: "No risk rows returned",
      desc: "Run another prediction to generate model risk details.",
      level: "warn",
      badge: "Unavailable",
    },
  ];
}

function defaultPathway(): PathwayStep[] {
  return [
    { title: "Input", desc: "Submitted molecule for simulation." },
    { title: "Modeling", desc: "Computed PK and toxicity heuristics." },
    { title: "Summary", desc: "Generated safety score and recommendation." },
  ];
}

export function mapPredictionToDrug(prediction: PredictResponse): Drug {
  const score = Math.round(prediction.safety_score?.score ?? 0);
  const pk = {
    absorption: prediction.pk_display?.absorption_ka_per_h ?? 0,
    clearance: prediction.pk_display?.clearance_l_per_h ?? 0,
    vd: prediction.pk_display?.volume_distribution_l_per_kg ?? 0,
    halflife: prediction.pk_display?.half_life_hours ?? 0,
    bio: prediction.pk_display?.bioavailability_percent ?? 0,
    protein: prediction.pk_display?.protein_binding_percent ?? 0,
  };

  const risks: Risk[] =
    prediction.risk_assessment?.map((row) => ({
      name: row.name ?? "Risk",
      desc: row.description ?? "No description provided.",
      level: row.level ?? "warn",
      badge: row.badge ?? "Monitor",
    })) ?? defaultRiskRows();

  const flags = prediction.display_flags ?? [];
  const pathway: PathwayStep[] =
    prediction.reaction_pathway?.map((step) => ({
      title: step.title ?? "Step",
      desc: step.description ?? "",
    })) ?? defaultPathway();

  const trialBadge = prediction.trial_recommendation?.badge ?? "warn";
  const trialReady = Boolean(prediction.trial_recommendation?.trial_ready);

  return {
    name: prediction.compound.name,
    smiles: prediction.compound.smiles,
    score,
    verdict: prediction.verdict ?? (score >= 70 ? "SAFE" : score >= 40 ? "ACCEPTABLE" : "HIGH RISK"),
    verdictColor: verdictColorForScore(score),
    trialReady,
    trialTitle: prediction.trial_recommendation?.title ?? "Recommendation unavailable",
    trialDesc:
      prediction.trial_recommendation?.description ??
      "No trial recommendation was returned by the backend.",
    trialColor:
      trialBadge === "safe"
        ? "var(--green)"
        : trialBadge === "danger"
          ? "var(--red)"
          : "var(--amber)",
    trialIcon: trialReady ? "PASS" : "HOLD",
    trialBg:
      trialBadge === "safe"
        ? "var(--tag-safe-bg)"
        : trialBadge === "danger"
          ? "var(--tag-danger-bg)"
          : "var(--tag-warn-bg)",
    pk,
    pkBars: buildPkBars(pk),
    pkColors: {
      absorption: "var(--green)",
      clearance: "var(--accent)",
      vd: "var(--purple)",
      halflife: "var(--amber)",
      bio: "var(--green)",
      protein: "var(--text3)",
    },
    risks,
    flags: flags.map((f) => f.text ?? "Flag"),
    flagTypes: flags.map((f) => f.level ?? "warn"),
    badgeTxt: trialReady ? "Trial Ready" : "Hold",
    badgeType: trialBadge,
    pathway,
    organDetail: {
      brain:
        prediction.organ_distribution?.organ_notes?.brain ??
        "Estimated brain compartment exposure from the simulation model.",
      lungs:
        prediction.organ_distribution?.organ_notes?.lungs ??
        "Estimated lung compartment exposure from the simulation model.",
      heart:
        prediction.organ_distribution?.organ_notes?.heart ??
        "Estimated heart compartment exposure from the simulation model.",
      liver:
        prediction.organ_distribution?.organ_notes?.liver ??
        "Estimated liver compartment exposure from the simulation model.",
      kidneys:
        prediction.organ_distribution?.organ_notes?.kidneys ??
        "Estimated kidney compartment exposure from the simulation model.",
    },
    pkData: {
      times: prediction.pk_curve?.time_hours ?? [],
      conc: prediction.pk_curve?.concentration_mg_per_l ?? [],
    },
    organPercentages: prediction.organ_distribution?.percentages,
    disclaimer: prediction.disclaimer,
  };
}

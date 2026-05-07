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

export const drugs: Record<string, Drug> = {
  Tylenol: {
    name: "Acetaminophen (Tylenol)",
    smiles: "CC(=O)Nc1ccc(O)cc1",
    score: 80,
    verdict: "SAFE",
    verdictColor: "var(--green)",
    trialReady: true,
    trialTitle: "Recommend for Pre-Clinical Trial",
    trialDesc:
      "PK parameters within therapeutic window. Toxicity risk low at standard dosing. Proceed with animal studies.",
    trialColor: "var(--green)",
    trialIcon: "\u2705",
    trialBg: "var(--tag-safe-bg)",
    pk: { absorption: 0.92, clearance: 18.4, vd: 0.95, halflife: 2.7, bio: 88, protein: 15 },
    pkBars: { absorption: 92, clearance: 55, vd: 40, halflife: 30, bio: 88, protein: 15 },
    pkColors: {
      absorption: "var(--green)",
      clearance: "var(--accent)",
      vd: "var(--purple)",
      halflife: "var(--amber)",
      bio: "var(--green)",
      protein: "var(--text3)",
    },
    risks: [
      { name: "Hepatotoxicity", desc: "Liver damage at high doses", level: "warn", badge: "Dose-Dependent" },
      { name: "Nephrotoxicity", desc: "Kidney stress \u2014 low risk", level: "safe", badge: "Low" },
      { name: "Cardiotoxicity", desc: "No cardiac signal detected", level: "safe", badge: "None" },
      { name: "CNS Penetration", desc: "Mild blood-brain crossing", level: "warn", badge: "Moderate" },
      { name: "Drug Interactions", desc: "Warfarin potentiation possible", level: "warn", badge: "Monitor" },
    ],
    flags: ["Absorption \u2713", "Liver \u26A0", "CNS \u26A0"],
    flagTypes: ["safe", "warn", "warn"],
    badgeTxt: "\u2713 Trial Ready",
    badgeType: "safe",
    pathway: [
      { title: "Oral Ingestion", desc: "Tablet enters GI tract, dissolves in stomach acid" },
      { title: "Gut Absorption", desc: "Absorbed rapidly through small intestine wall" },
      { title: "Bloodstream", desc: "Reaches peak plasma concentration ~45 min" },
      { title: "Brain / CNS", desc: "Inhibits COX enzymes, reduces prostaglandins" },
      { title: "Liver Metabolism", desc: "CYP450 converts to NAPQI, safely conjugated" },
      { title: "Renal Excretion", desc: "Metabolites cleared by kidneys in ~4 hours" },
    ],
    organDetail: {
      brain: "Crosses blood-brain barrier moderately. Inhibits central COX enzymes to produce analgesia and antipyresis. CNS concentration peaks ~60 minutes post-dose.",
      lungs: "Passes through pulmonary circulation. Low accumulation. No significant pulmonary toxicity at standard doses.",
      heart: "No direct cardiac target. Low protein binding means minimal cardiovascular interference.",
      liver: "Primary metabolic site. Acetaminophen is converted to NAPQI here. At standard doses this is safely conjugated. Overdose causes NAPQI accumulation \u2192 hepatotoxicity.",
      kidneys: "Primary excretion route. Glucuronide and sulfate conjugates cleared efficiently. Risk increases with chronic high-dose use.",
    },
  },
  Ibuprofen: {
    name: "Ibuprofen (Advil)",
    smiles: "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    score: 74,
    verdict: "ACCEPTABLE",
    verdictColor: "var(--amber)",
    trialReady: true,
    trialTitle: "Conditional Trial Approval",
    trialDesc:
      "GI risk flagged. Requires gastroprotective co-administration. Monitor renal function in extended trials.",
    trialColor: "var(--amber)",
    trialIcon: "\u26A0\uFE0F",
    trialBg: "var(--tag-warn-bg)",
    pk: { absorption: 0.85, clearance: 10.2, vd: 0.14, halflife: 2.1, bio: 80, protein: 99 },
    pkBars: { absorption: 85, clearance: 30, vd: 10, halflife: 25, bio: 80, protein: 99 },
    pkColors: {
      absorption: "var(--green)",
      clearance: "var(--accent)",
      vd: "var(--amber)",
      halflife: "var(--amber)",
      bio: "var(--green)",
      protein: "var(--red)",
    },
    risks: [
      { name: "GI Bleeding", desc: "COX-1 inhibition damages stomach lining", level: "warn", badge: "Moderate" },
      { name: "Nephrotoxicity", desc: "Reduced renal blood flow at high doses", level: "warn", badge: "Monitor" },
      { name: "Cardiotoxicity", desc: "Slight CV risk with long-term use", level: "warn", badge: "Low-Mod" },
      { name: "Hepatotoxicity", desc: "Minimal liver involvement", level: "safe", badge: "Low" },
      { name: "Drug Interactions", desc: "Anticoagulant potentiation", level: "warn", badge: "Monitor" },
    ],
    flags: ["GI Risk \u26A0", "Kidney \u26A0", "CV Risk \u26A0"],
    flagTypes: ["warn", "warn", "warn"],
    badgeTxt: "\u26A0 Conditional",
    badgeType: "warn",
    pathway: [
      { title: "Oral Ingestion", desc: "Tablet dissolves, enters gastric environment" },
      { title: "Gut Absorption", desc: "Rapidly absorbed \u2014 high bioavailability 80%" },
      { title: "Plasma Binding", desc: "99% protein-bound \u2014 very low free drug fraction" },
      { title: "COX Inhibition", desc: "Inhibits both COX-1 and COX-2 enzymes systemically" },
      { title: "Liver Metabolism", desc: "CYP2C9 converts to inactive hydroxylated metabolites" },
      { title: "Renal Excretion", desc: "Conjugated metabolites excreted via urine" },
    ],
    organDetail: {
      brain: "Poor CNS penetration due to high protein binding. Primary action is peripheral COX inhibition, not central.",
      lungs: "May exacerbate aspirin-sensitive asthma. COX pathway affects arachidonic acid \u2192 leukotriene shift.",
      heart: "Long-term use associated with increased cardiovascular events. Increases blood pressure modestly.",
      liver: "Low hepatotoxicity risk. Metabolized by CYP2C9. Rare cases of cholestatic hepatitis reported.",
      kidneys: "Significant risk: inhibits prostaglandin-mediated renal vasodilation. Can cause acute kidney injury in dehydrated patients.",
    },
  },
  Thalidomide: {
    name: "Thalidomide (Historical)",
    smiles: "O=C1CCC(=O)N1C1CC(=O)NC1=O",
    score: 18,
    verdict: "DANGEROUS",
    verdictColor: "var(--red)",
    trialReady: false,
    trialTitle: "DO NOT PROCEED TO TRIAL",
    trialDesc:
      "Severe teratogenicity predicted. Cerelon protein binding causes embryonic limb defects. Historical data confirms catastrophic outcome.",
    trialColor: "var(--red)",
    trialIcon: "\uD83D\uDEAB",
    trialBg: "var(--tag-danger-bg)",
    pk: { absorption: 0.7, clearance: 2.1, vd: 1.2, halflife: 8.7, bio: 70, protein: 55 },
    pkBars: { absorption: 70, clearance: 10, vd: 80, halflife: 87, bio: 70, protein: 55 },
    pkColors: {
      absorption: "var(--amber)",
      clearance: "var(--red)",
      vd: "var(--red)",
      halflife: "var(--red)",
      bio: "var(--amber)",
      protein: "var(--amber)",
    },
    risks: [
      { name: "Teratogenicity", desc: "Severe fetal limb malformation", level: "danger", badge: "CRITICAL" },
      { name: "Peripheral Neuropathy", desc: "Irreversible nerve damage", level: "danger", badge: "HIGH" },
      { name: "Thromboembolism", desc: "Deep vein thrombosis risk elevated", level: "danger", badge: "HIGH" },
      { name: "Sedation", desc: "CNS depression, drowsiness", level: "warn", badge: "Moderate" },
      { name: "Teratogen Flagged", desc: "CERELON binding confirmed", level: "danger", badge: "FLAGGED" },
    ],
    flags: ["Teratogen \uD83D\uDEAB", "Neuro \uD83D\uDEAB", "Thrombo \u26A0"],
    flagTypes: ["danger", "danger", "warn"],
    badgeTxt: "\uD83D\uDEAB DO NOT TRIAL",
    badgeType: "danger",
    pathway: [
      { title: "Oral Ingestion", desc: "Racemic mixture enters GI tract" },
      { title: "Absorption", desc: "Absorbed slowly, bioavailability ~70%" },
      { title: "Plasma Distribution", desc: "Wide distribution \u2014 crosses placenta freely" },
      { title: "Cerelon Binding", desc: "Binds CRBN protein \u2192 disrupts embryonic growth" },
      { title: "Limb Bud Inhibition", desc: "Inhibits angiogenesis in developing embryo" },
      { title: "Slow Elimination", desc: "Half-life 8.7h \u2014 accumulates with repeat dosing" },
    ],
    organDetail: {
      brain: "Sedative effect via CNS depression. Inhibits TNF-\u03B1 which affects neurological pathways.",
      lungs: "Anti-angiogenic properties affect pulmonary vasculature. Risk of pulmonary embolism.",
      heart: "Increased risk of deep vein thrombosis and pulmonary embolism, especially in combination with steroids.",
      liver: "Spontaneous hydrolysis rather than hepatic metabolism. Less liver-dependent but produces toxic enantiomers.",
      kidneys: "Moderate renal excretion. Accumulation risk in renal impairment.",
    },
  },
  Aspirin: {
    name: "Aspirin (Acetylsalicylic Acid)",
    smiles: "CC(=O)Oc1ccccc1C(=O)O",
    score: 68,
    verdict: "ACCEPTABLE",
    verdictColor: "var(--amber)",
    trialReady: true,
    trialTitle: "Conditional Trial Approval",
    trialDesc:
      "GI irritation and bleeding risk must be managed. Contraindicated in pediatric populations (Reye syndrome).",
    trialColor: "var(--amber)",
    trialIcon: "\u26A0\uFE0F",
    trialBg: "var(--tag-warn-bg)",
    pk: { absorption: 0.8, clearance: 39.0, vd: 0.17, halflife: 0.3, bio: 68, protein: 90 },
    pkBars: { absorption: 80, clearance: 75, vd: 12, halflife: 5, bio: 68, protein: 90 },
    pkColors: {
      absorption: "var(--green)",
      clearance: "var(--red)",
      vd: "var(--amber)",
      halflife: "var(--green)",
      bio: "var(--amber)",
      protein: "var(--amber)",
    },
    risks: [
      { name: "GI Bleeding", desc: "Irreversible COX-1 inhibition in gut", level: "warn", badge: "Moderate" },
      { name: "Reye Syndrome", desc: "Fatal in children with viral illness", level: "danger", badge: "CRITICAL (Peds)" },
      { name: "Bleeding Risk", desc: "Platelet aggregation permanently inhibited", level: "warn", badge: "Monitor" },
      { name: "Ototoxicity", desc: "Tinnitus at high doses", level: "warn", badge: "Dose-Dep." },
      { name: "Hepatotoxicity", desc: "Minimal at therapeutic doses", level: "safe", badge: "Low" },
    ],
    flags: ["GI Risk \u26A0", "Peds \uD83D\uDEAB", "Bleed \u26A0"],
    flagTypes: ["warn", "danger", "warn"],
    badgeTxt: "\u26A0 Conditional",
    badgeType: "warn",
    pathway: [
      { title: "Oral Ingestion", desc: "Tablet dissolves in stomach \u2014 irritates mucosa" },
      { title: "Rapid Hydrolysis", desc: "Converted to salicylate within 30 minutes" },
      { title: "COX Acetylation", desc: "Irreversibly binds and blocks COX-1 and COX-2" },
      { title: "Platelet Effect", desc: "Permanently inhibits platelet thromboxane A2" },
      { title: "Liver Conjugation", desc: "Salicylate conjugated with glycine and glucuronate" },
      { title: "Rapid Excretion", desc: "Very short half-life 15\u201320 min, cleared quickly" },
    ],
    organDetail: {
      brain: "Crosses BBB at high doses causing salicylism: tinnitus, dizziness, confusion.",
      lungs: "Aspirin-exacerbated respiratory disease in 10-20% of asthma patients. Triggers bronchoconstriction.",
      heart: "Low-dose antiplatelet effect beneficial in cardiovascular prevention. High dose increases bleeding risk.",
      liver: "Conjugation with glycine and glucuronic acid. High doses saturate conjugation pathways.",
      kidneys: "Uricosuric at high doses, urate retention at low doses. Renal excretion pH-dependent.",
    },
  },
  Metformin: {
    name: "Metformin (Glucophage)",
    smiles: "CN(C)C(=N)NC(=N)N",
    score: 88,
    verdict: "SAFE",
    verdictColor: "var(--green)",
    trialReady: true,
    trialTitle: "Strongly Recommend for Trial",
    trialDesc:
      "Excellent safety profile. No hepatotoxicity, no hypoglycemia risk as monotherapy. Strong preclinical data.",
    trialColor: "var(--green)",
    trialIcon: "\u2705",
    trialBg: "var(--tag-safe-bg)",
    pk: { absorption: 0.55, clearance: 96.0, vd: 3.7, halflife: 6.2, bio: 55, protein: 0 },
    pkBars: { absorption: 55, clearance: 95, vd: 95, halflife: 62, bio: 55, protein: 0 },
    pkColors: {
      absorption: "var(--amber)",
      clearance: "var(--red)",
      vd: "var(--accent)",
      halflife: "var(--purple)",
      bio: "var(--amber)",
      protein: "var(--green)",
    },
    risks: [
      { name: "Lactic Acidosis", desc: "Rare but serious in renal impairment", level: "warn", badge: "Rare" },
      { name: "GI Tolerance", desc: "Nausea, diarrhea \u2014 usually transient", level: "warn", badge: "Common" },
      { name: "Hepatotoxicity", desc: "No significant liver toxicity", level: "safe", badge: "None" },
      { name: "Hypoglycemia", desc: "Does not cause as monotherapy", level: "safe", badge: "None" },
      { name: "B12 Deficiency", desc: "Long-term use impairs absorption", level: "warn", badge: "Monitor" },
    ],
    flags: ["Liver \u2713", "Kidney Monitor", "GI \u26A0"],
    flagTypes: ["safe", "warn", "warn"],
    badgeTxt: "\u2713 Trial Ready",
    badgeType: "safe",
    pathway: [
      { title: "Oral Ingestion", desc: "Tablet absorbed in small intestine" },
      { title: "Portal Circulation", desc: "Enters portal vein \u2014 high intestinal wall concentration" },
      { title: "Mitochondria", desc: "Inhibits Complex I of electron transport chain" },
      { title: "AMPK Activation", desc: "Activates energy sensor, reduces gluconeogenesis" },
      { title: "Hepatic Glucose", desc: "Liver reduces glucose output by ~30%" },
      { title: "Renal Excretion", desc: "Excreted unchanged in urine \u2014 no hepatic metabolism" },
    ],
    organDetail: {
      brain: "Minimal CNS penetration. Some evidence of neuroprotective effects through AMPK pathway.",
      lungs: "No significant pulmonary effects. Lactic acidosis risk in hypoxic conditions.",
      heart: "Cardioprotective effects via AMPK. Reduces cardiovascular mortality in diabetic patients.",
      liver: "Primary site of action \u2014 reduces hepatic glucose production. Not metabolized by liver, no hepatotoxicity.",
      kidneys: "Excreted entirely unchanged by kidneys. Contraindicated in renal impairment (lactic acidosis risk).",
    },
  },
};

export const drugNames = Object.keys(drugs) as Array<keyof typeof drugs>;

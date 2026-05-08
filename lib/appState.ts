import type { Drug } from "@/lib/drugData";
import type { CompoundPreset } from "@/lib/backendApi";

export type Page = "input" | "results" | "science";

export interface AppState {
  currentPage: Page;
  selectedDrugLabel: string;
  selectedPreset: string | null;
  inputValue: string;
  dose: number;
  drug: Drug | null;
  isAnalyzing: boolean;
  errorMessage: string | null;
  apiOnline: boolean;
  presets: string[];
  compoundLookup: Record<string, CompoundPreset>;
  summaryText: string | null;
}

export type AppAction =
  | { type: "SET_PAGE"; page: Page }
  | { type: "SET_INPUT"; value: string }
  | { type: "SET_DOSE"; dose: number }
  | { type: "SELECT_PRESET"; name: string }
  | { type: "SET_API_STATUS"; online: boolean }
  | { type: "SET_COMPOUNDS"; compounds: CompoundPreset[] }
  | { type: "START_ANALYSIS" }
  | { type: "ANALYSIS_SUCCESS"; drug: Drug; preset: string | null; summary: string | null }
  | { type: "ANALYSIS_ERROR"; message: string }
  | { type: "CLEAR_ERROR" };

export const defaultPresets = ["Tylenol", "Ibuprofen", "Thalidomide", "Aspirin", "Metformin"];

export const initialState: AppState = {
  currentPage: "input",
  selectedDrugLabel: "Tylenol",
  selectedPreset: "Tylenol",
  inputValue: "",
  dose: 1.0,
  drug: null,
  isAnalyzing: false,
  errorMessage: null,
  apiOnline: false,
  presets: defaultPresets,
  compoundLookup: {},
  summaryText: null,
};

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_PAGE":
      return { ...state, currentPage: action.page };

    case "SET_INPUT":
      return { ...state, inputValue: action.value };

    case "SET_DOSE":
      return { ...state, dose: action.dose };

    case "SELECT_PRESET":
      return {
        ...state,
        selectedPreset: action.name,
        selectedDrugLabel: action.name,
        inputValue: action.name,
        dose: 1.0,
        errorMessage: null,
      };

    case "SET_API_STATUS":
      return { ...state, apiOnline: action.online };

    case "SET_COMPOUNDS": {
      const lookup = action.compounds.reduce<Record<string, CompoundPreset>>((acc, item) => {
        acc[item.name] = item;
        return acc;
      }, {});
      return {
        ...state,
        compoundLookup: lookup,
        presets: action.compounds.length > 0
          ? action.compounds.slice(0, 5).map((c) => c.name)
          : defaultPresets,
      };
    }

    case "START_ANALYSIS":
      return {
        ...state,
        isAnalyzing: true,
        errorMessage: null,
        currentPage: "results",
      };

    case "ANALYSIS_SUCCESS":
      return {
        ...state,
        isAnalyzing: false,
        drug: action.drug,
        selectedDrugLabel: action.drug.name,
        selectedPreset: action.preset,
        summaryText: action.summary,
        currentPage: "results",
      };

    case "ANALYSIS_ERROR":
      return {
        ...state,
        isAnalyzing: false,
        errorMessage: action.message,
        currentPage: "input",
      };

    case "CLEAR_ERROR":
      return { ...state, errorMessage: null };

    default:
      return state;
  }
}

export function computeEffectiveScore(drug: Drug | null, dose: number): number {
  if (!drug) return 0;
  let score = drug.score;
  if (dose > 2) score = Math.max(5, score - (dose - 2) * 15);
  else if (dose > 1) score = Math.max(10, score - (dose - 1) * 8);
  return Math.round(score);
}

export function resolveCompoundPreset(
  value: string,
  lookup: Record<string, CompoundPreset>
): CompoundPreset | undefined {
  const exact = lookup[value];
  if (exact) return exact;
  return Object.values(lookup).find((item) => {
    if (item.name.toLowerCase() === value.toLowerCase()) return true;
    return item.aliases?.some((alias) => alias.toLowerCase() === value.toLowerCase());
  });
}

export function looksLikeSmiles(value: string): boolean {
  return /[=#[\]()]/.test(value) || /[A-Z][a-z]?\d?/.test(value);
}

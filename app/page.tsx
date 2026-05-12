"use client";

import { useCallback, useEffect, useMemo, useReducer } from "react";
import Navbar from "@/components/Navbar";
import InputView from "@/views/InputView";
import ResultsView from "@/views/ResultsView";
import ScienceView from "@/views/ScienceView";
import {
  appReducer,
  computeEffectiveScore,
  initialState,
  looksLikeSmiles,
  resolveCompoundPreset,
} from "@/lib/appState";
import {
  checkBackendHealth,
  fetchCompounds,
  fetchPrediction,
  fetchSummary,
  mapPredictionToDrug,
} from "@/lib/backendApi";

export default function Home() {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const { currentPage, drug, dose, inputValue, compoundLookup } = state;

  const effectiveScore = useMemo(
    () => computeEffectiveScore(drug, dose),
    [drug, dose]
  );

  useEffect(() => {
    let isMounted = true;

    async function loadBackendContext() {
      const healthy = await checkBackendHealth();
      if (!isMounted) return;
      dispatch({ type: "SET_API_STATUS", online: healthy });
      if (!healthy) return;

      try {
        const compounds = await fetchCompounds();
        if (!isMounted) return;
        dispatch({ type: "SET_COMPOUNDS", compounds });
      } catch {
        dispatch({ type: "SET_API_STATUS", online: false });
      }
    }

    void loadBackendContext();
    return () => { isMounted = false; };
  }, []);

  const analyzeDrug = useCallback(async (nameOverride?: string) => {
    const val = (nameOverride ?? inputValue).trim();
    if (!val) return;

    dispatch({ type: "START_ANALYSIS" });
    window.scrollTo(0, 0);

    const compound = resolveCompoundPreset(val, compoundLookup);
    const smilesInput = looksLikeSmiles(val);
    const requestPayload = {
      drug_name: compound?.name ?? (smilesInput ? "" : val),
      smiles: compound ? "" : smilesInput ? val : "",
      compound_id: compound?.id,
      dose_mg: Math.max(1, dose * 100),
      route: "oral",
    };

    try {
      // Run prediction and summary in parallel for faster loading
      const [prediction, summary] = await Promise.all([
        fetchPrediction(requestPayload),
        fetchSummary(requestPayload),
      ]);
      const mappedDrug = mapPredictionToDrug(prediction);

      dispatch({
        type: "ANALYSIS_SUCCESS",
        drug: mappedDrug,
        preset: compound?.name ?? null,
        summary,
      });
      window.scrollTo(0, 0);
    } catch (err) {
      console.error("Prediction failed:", err);
      dispatch({
        type: "ANALYSIS_ERROR",
        message: "Backend prediction failed. Please check your connection and try again.",
      });
    }
  }, [inputValue, compoundLookup, dose]);

  return (
    <>
      <Navbar
        currentPage={currentPage}
        onPageChange={(page) => dispatch({ type: "SET_PAGE", page })}
        hasResults={Boolean(drug)}
      />
      <div className="glow-orb-2" />

      <main>
        {currentPage === "input" && (
          <InputView state={state} dispatch={dispatch} onAnalyze={analyzeDrug} />
        )}

        {currentPage === "results" && (
          <ResultsView state={state} dispatch={dispatch} effectiveScore={effectiveScore} />
        )}

        {currentPage === "science" && (
          <ScienceView state={state} dispatch={dispatch} />
        )}
      </main>
    </>
  );
}

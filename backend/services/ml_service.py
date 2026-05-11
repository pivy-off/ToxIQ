from __future__ import annotations

import logging
from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor

logger = logging.getLogger("toxiq.ml_service")

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski

    HAS_RDKIT = True
except ImportError:
    logger.info("RDKit not available - SMILES-based predictions disabled")
    Chem = None
    Descriptors = None
    Lipinski = None
    HAS_RDKIT = False

try:
    from xgboost import XGBRegressor

    HAS_XGBOOST = True
except ImportError:
    logger.info("XGBoost not available - using RandomForest fallback")
    HAS_XGBOOST = False

from backend.models.schemas import DrugInput, PredictResponse
from backend.services.drug_presets import DRUG_PRESETS


def _risk_label(toxicity_risk: float) -> str:
    if toxicity_risk < 0.33:
        return "Low"
    if toxicity_risk < 0.66:
        return "Medium"
    return "High"


class MLService:
    def __init__(self) -> None:
        self._rng = np.random.default_rng(42)
        self.models = {
            "clearance": self._build_regressor(),
            "volume_of_distribution": self._build_regressor(),
            "absorption_rate": self._build_regressor(),
            "toxicity_risk": self._build_regressor(),
        }
        self._train_models()

    @staticmethod
    def _build_regressor():
        if HAS_XGBOOST:
            return XGBRegressor(
                n_estimators=120,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                objective="reg:squarederror",
            )
        return RandomForestRegressor(n_estimators=200, random_state=42)

    def _generate_synthetic_data(self, n_rows: int = 90):
        mol_wt = self._rng.uniform(120, 650, n_rows)
        logp = self._rng.uniform(-1.5, 6.0, n_rows)
        h_donors = self._rng.integers(0, 6, n_rows)
        h_acceptors = self._rng.integers(1, 12, n_rows)
        tpsa = self._rng.uniform(20, 190, n_rows)
        rot_bonds = self._rng.integers(0, 14, n_rows)

        weight = self._rng.uniform(45, 120, n_rows)
        age = self._rng.integers(18, 90, n_rows)
        renal = self._rng.uniform(0.4, 1.0, n_rows)
        hepatic = self._rng.uniform(0.4, 1.0, n_rows)

        x = np.column_stack(
            [
                mol_wt,
                logp,
                h_donors,
                h_acceptors,
                tpsa,
                rot_bonds,
                weight,
                age,
                renal,
                hepatic,
            ]
        )

        noise = self._rng.normal(0, 0.25, n_rows)

        clearance = (
            0.055 * weight
            - 0.020 * age
            + 4.2 * renal
            + 2.0 * hepatic
            - 0.005 * mol_wt
            + noise
        )
        clearance = np.clip(clearance, 0.1, 15.0)

        volume = 0.85 * weight + 0.08 * mol_wt + 2.4 * logp + 4.0 + noise
        volume = np.clip(volume, 6.0, 180.0)

        absorption = 0.95 + 0.06 * logp - 0.0015 * tpsa + 0.045 * hepatic + noise
        absorption = np.clip(absorption, 0.05, 3.0)

        tox_linear = (
            0.05 * logp
            + 0.0018 * tpsa
            + 0.018 * h_acceptors
            + 0.008 * rot_bonds
            + 0.018 * (1.0 - renal)
            + 0.015 * (1.0 - hepatic)
            + self._rng.normal(0, 0.02, n_rows)
        )
        toxicity = 1.0 / (1.0 + np.exp(-tox_linear))
        toxicity = np.clip(toxicity, 0.05, 0.95)

        return x, {
            "clearance": clearance,
            "volume_of_distribution": volume,
            "absorption_rate": absorption,
            "toxicity_risk": toxicity,
        }

    def _train_models(self) -> None:
        x, y = self._generate_synthetic_data()
        for target, model in self.models.items():
            model.fit(x, y[target])

    @staticmethod
    def _extract_smiles_features(smiles: str) -> np.ndarray:
        if not HAS_RDKIT:
            raise ValueError(
                "RDKit is not installed in this environment. Use preset drugs without SMILES or install RDKit."
            )

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError("Invalid SMILES string provided.")

        return np.array(
            [
                Descriptors.MolWt(mol),
                Descriptors.MolLogP(mol),
                Lipinski.NumHDonors(mol),
                Lipinski.NumHAcceptors(mol),
                Descriptors.TPSA(mol),
                Lipinski.NumRotatableBonds(mol),
            ],
            dtype=float,
        )

    @staticmethod
    def get_therapeutic_window(drug_name: str) -> Tuple[float, float]:
        preset = DRUG_PRESETS.get(drug_name.lower())
        if preset:
            return float(preset["therapeutic_min"]), float(preset["therapeutic_max"])
        return 1.0, 10.0

    @staticmethod
    def _resolve_bioavailability(drug_name: str) -> float:
        preset = DRUG_PRESETS.get(drug_name.lower())
        if preset:
            return float(preset["bioavailability"])
        return 0.75

    def _predict_from_features(self, feature_vector: np.ndarray) -> Dict[str, float]:
        features = feature_vector.reshape(1, -1)
        clearance = float(self.models["clearance"].predict(features)[0])
        volume = float(self.models["volume_of_distribution"].predict(features)[0])
        absorption = float(self.models["absorption_rate"].predict(features)[0])
        toxicity = float(self.models["toxicity_risk"].predict(features)[0])

        return {
            "clearance": max(clearance, 0.05),
            "volume_of_distribution": max(volume, 1.0),
            "absorption_rate": max(absorption, 0.05),
            "toxicity_risk": float(np.clip(toxicity, 0.0, 1.0)),
        }

    def _predict_from_preset(self, drug_input: DrugInput) -> Dict[str, float]:
        preset = DRUG_PRESETS.get(drug_input.drug_name.lower())
        if not preset:
            raise ValueError(
                "No SMILES provided and drug preset not found. Provide a SMILES string or use a supported preset drug."
            )

        return {
            "clearance": float(preset["clearance"]),
            "volume_of_distribution": float(preset["volume_of_distribution"]),
            "absorption_rate": float(preset["absorption_rate"]),
            "toxicity_risk": float(np.clip(preset["toxicity_risk"], 0.0, 1.0)),
        }

    def predict(self, drug_input: DrugInput) -> PredictResponse:
        if drug_input.smiles:
            molecular_features = self._extract_smiles_features(drug_input.smiles)
            patient_features = np.array(
                [
                    drug_input.patient_weight_kg,
                    drug_input.age,
                    drug_input.renal_function,
                    drug_input.hepatic_function,
                ],
                dtype=float,
            )
            feature_vector = np.concatenate([molecular_features, patient_features])
            predictions = self._predict_from_features(feature_vector)
        else:
            predictions = self._predict_from_preset(drug_input)

        adjusted_clearance = max(predictions["clearance"] * drug_input.renal_function, 0.01)
        adjusted_volume = max(
            predictions["volume_of_distribution"] * (drug_input.patient_weight_kg / 70.0),
            0.5,
        )
        adjusted_absorption = max(predictions["absorption_rate"], 0.05)
        bioavailability = float(np.clip(self._resolve_bioavailability(drug_input.drug_name), 0.05, 1.0))

        half_life = float(0.693 * adjusted_volume / adjusted_clearance)
        toxicity_risk = float(np.clip(predictions["toxicity_risk"], 0.0, 1.0))
        safety_score = float(np.clip((1.0 - toxicity_risk) * 100.0, 0.0, 100.0))

        return PredictResponse(
            absorption_rate=float(adjusted_absorption),
            clearance=float(adjusted_clearance),
            volume_of_distribution=float(adjusted_volume),
            half_life=float(max(half_life, 0.0)),
            bioavailability=bioavailability,
            toxicity_risk=toxicity_risk,
            safety_score=safety_score,
            risk_label=_risk_label(toxicity_risk),
        )


ml_service = MLService()

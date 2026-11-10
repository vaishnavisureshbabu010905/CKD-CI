"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import { useApi } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import {
  BrainCircuit,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Info,
  ChevronRight,
  UserCheck,
  Stethoscope,
  Activity,
  History,
  Check,
  AlertCircle,
} from "lucide-react";

type PredictionResponse = {
  prediction_id?: number;
  model_version: string;
  result: {
    predicted_label: string;
    confidence?: number;
    probabilities?: Record<string, number>;
  };
};

type PatientOption = {
  id: number;
  patient_identifier: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
  medical_history?: Record<string, unknown>;
  features?: Record<string, unknown>;
};

type ClinicalTab = "demographics" | "renal" | "metabolic";

interface FeatureConfig {
  key: string;
  label: string;
  unit: string;
  refRange: string;
  min: number;
  max: number;
  step?: number;
  category: ClinicalTab;
  description: string;
}

const CLINICAL_SCHEMA: FeatureConfig[] = [
  // 1. Demographics & History
  { key: "age", label: "Patient Age", unit: "years", refRange: "20 - 90", min: 20, max: 100, step: 1, category: "demographics", description: "Age at clinical presentation" },
  { key: "education_years", label: "Formal Education", unit: "years", refRange: "0 - 25", min: 0, max: 25, step: 1, category: "demographics", description: "Completed years of schooling (cognitive reserve)" },
  { key: "gender", label: "Biological Sex", unit: "0=Female, 1=Male", refRange: "0 or 1", min: 0, max: 1, step: 1, category: "demographics", description: "Sex assigned at birth" },
  { key: "diabetes", label: "Diabetes Mellitus", unit: "0=No, 1=Yes", refRange: "Binary", min: 0, max: 1, step: 1, category: "demographics", description: "Documented history of diabetes" },
  { key: "hypertension", label: "Hypertension", unit: "0=No, 1=Yes", refRange: "Binary", min: 0, max: 1, step: 1, category: "demographics", description: "Documented chronic hypertension" },
  { key: "cvd", label: "Cardiovascular Disease", unit: "0=No, 1=Yes", refRange: "Binary", min: 0, max: 1, step: 1, category: "demographics", description: "CAD, stroke, or heart failure" },

  // 2. Renal Panel
  { key: "eGFR", label: "eGFR (CKD-EPI)", unit: "mL/min/1.73m²", refRange: "≥ 60", min: 5, max: 140, step: 1, category: "renal", description: "Glomerular filtration rate" },
  { key: "creatinine", label: "Serum Creatinine", unit: "mg/dL", refRange: "0.7 - 1.3", min: 0.3, max: 10.0, step: 0.1, category: "renal", description: "Serum creatinine concentration" },
  { key: "bun", label: "Blood Urea Nitrogen", unit: "mg/dL", refRange: "7 - 20", min: 3, max: 120, step: 1, category: "renal", description: "Urea nitrogen concentration" },
  { key: "uacr", label: "Urine Albumin/Creatinine (UACR)", unit: "mg/g", refRange: "< 30 (A1)", min: 1, max: 4000, step: 10, category: "renal", description: "Albuminuria staging" },

  // 3. Metabolic & Electrolytes
  { key: "hemoglobin", label: "Hemoglobin", unit: "g/dL", refRange: "12.0 - 17.5", min: 6.0, max: 19.0, step: 0.1, category: "metabolic", description: "Renal anemia biomarker" },
  { key: "albumin", label: "Serum Albumin", unit: "g/dL", refRange: "3.5 - 5.0", min: 1.5, max: 6.0, step: 0.1, category: "metabolic", description: "Nutritional & frailty marker" },
  { key: "hsCRP", label: "High-Sensitivity CRP", unit: "mg/L", refRange: "< 3.0", min: 0.1, max: 50.0, step: 0.1, category: "metabolic", description: "Systemic microvascular inflammation" },
  { key: "potassium", label: "Serum Potassium (K⁺)", unit: "mmol/L", refRange: "3.5 - 5.1", min: 2.5, max: 7.5, step: 0.1, category: "metabolic", description: "Electrolyte concentration" },
  { key: "phosphate", label: "Serum Phosphate", unit: "mg/dL", refRange: "2.5 - 4.5", min: 1.0, max: 9.0, step: 0.1, category: "metabolic", description: "Mineral bone marker" },
  { key: "calcium", label: "Total Calcium", unit: "mg/dL", refRange: "8.5 - 10.5", min: 6.0, max: 13.0, step: 0.1, category: "metabolic", description: "Serum calcium" },
  { key: "systolic_bp", label: "Systolic Blood Pressure", unit: "mmHg", refRange: "90 - 130", min: 80, max: 230, step: 2, category: "metabolic", description: "Office sitting systolic BP" },
  { key: "bmi", label: "Body Mass Index", unit: "kg/m²", refRange: "18.5 - 24.9", min: 14.0, max: 55.0, step: 0.5, category: "metabolic", description: "Calculated weight / height²" },
];

const DEFAULT_VALUES: Record<string, number> = {
  age: 64,
  education_years: 12,
  gender: 1,
  diabetes: 1,
  hypertension: 1,
  cvd: 0,
  eGFR: 42,
  creatinine: 1.9,
  bun: 29,
  uacr: 380,
  hemoglobin: 11.2,
  albumin: 3.6,
  hsCRP: 3.8,
  potassium: 4.6,
  phosphate: 4.4,
  calcium: 9.1,
  systolic_bp: 144,
  bmi: 28.4,
};

/** Normalize a DB feature key to our canonical CLINICAL_SCHEMA key. */
function normalizeFeatureKey(raw: string): string {
  const lower = raw.toLowerCase();
  if (lower === "egfr") return "eGFR";
  if (lower === "hscrp") return "hsCRP";
  return raw; // already canonical for other keys
}

export default function PredictionStudioPage() {
  const api = useApi();
  const { notify } = useToast();
  const searchParams = useSearchParams();

  const [activeTab, setActiveTab] = useState<ClinicalTab>("demographics");

  // formData: null means "not on record" for that key (shown as empty+required)
  const [formData, setFormData] = useState<Record<string, number | null>>(DEFAULT_VALUES);
  // missingFields: keys that must be filled before submitting when a patient is selected
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [patientId, setPatientId] = useState("");
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Load existing patients from database
  useEffect(() => {
    let mounted = true;
    api
      .get<PatientOption[]>("/patients/")
      .then((data) => {
        if (mounted && data) setPatients(data);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [api]);

  /** When a patient is selected, load ONLY their stored feature values.
   *  Keys missing from their record are set to null ("Not on Record"). */
  const handleSelectPatient = useCallback((identifier: string) => {
    setPatientId(identifier);
    setResult(null);
    setSavedSuccess(false);
    setError(null);

    if (!identifier) {
      // No patient selected → restore reference defaults
      setFormData(DEFAULT_VALUES);
      setMissingFields([]);
      return;
    }

    const found = patients.find((p) => p.patient_identifier === identifier);
    if (!found) return;

    // Build a lookup of their stored features with normalized keys
    const stored: Record<string, number> = {};
    if (found.features) {
      for (const [rawKey, v] of Object.entries(found.features)) {
        const canonical = normalizeFeatureKey(rawKey);
        if (typeof v === "number") {
          stored[canonical] = v;
        } else if (typeof v === "string") {
          const n = parseFloat(v);
          if (!isNaN(n)) stored[canonical] = n;
        }
      }
    }

    // Auto-derive demographics from Patient Profile if not already in features
    if (!("age" in stored) && found.date_of_birth) {
      const dob = new Date(found.date_of_birth);
      if (!Number.isNaN(dob.getTime())) {
        const today = new Date();
        let calcAge = today.getFullYear() - dob.getFullYear();
        const m = today.getMonth() - dob.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) calcAge -= 1;
        if (calcAge > 0) stored.age = calcAge;
      }
    }

    if (!("gender" in stored) && found.sex) {
      stored.gender = found.sex.toLowerCase() === "female" ? 0 : 1;
    }

    // Auto-derive comorbidity flags from Medical History if available
    const medHistory = found.medical_history as Record<string, unknown> | undefined;
    if (medHistory) {
      if (!("diabetes" in stored) && medHistory.diabetes !== undefined) {
        stored.diabetes = medHistory.diabetes === "Yes" ? 1 : 0;
      }
      if (!("hypertension" in stored) && medHistory.hypertension !== undefined) {
        stored.hypertension = medHistory.hypertension === "Yes" ? 1 : 0;
      }
      if (!("cvd" in stored) && medHistory.cvd !== undefined) {
        stored.cvd = medHistory.cvd === "Yes" ? 1 : 0;
      }
      if (!("education_years" in stored) && medHistory.education_years !== undefined) {
        const ey = Number(medHistory.education_years);
        if (!isNaN(ey)) stored.education_years = ey;
      }
    }

    // Build form state: patient value where available, null where missing
    const nextForm: Record<string, number | null> = {};
    const missing: string[] = [];
    for (const field of CLINICAL_SCHEMA) {
      if (field.key in stored) {
        nextForm[field.key] = stored[field.key];
      } else {
        nextForm[field.key] = null;
        missing.push(field.key);
      }
    }

    setFormData(nextForm);
    setMissingFields(missing);

    const name = `${found.first_name || ""} ${found.last_name || ""}`.trim();
    if (missing.length > 0) {
      notify(
        `Loaded ${name}. ${missing.length} field(s) not on record — please enter before computing.`,
        "info"
      );
    } else {
      notify(`All 18 biomarkers loaded for ${name}.`, "success");
    }
  }, [patients, notify]);

  // Auto-select patient from ?patient= URL query param
  useEffect(() => {
    const param = searchParams.get("patient");
    if (param && patients.length > 0) {
      handleSelectPatient(param);
    }
  }, [searchParams, patients, handleSelectPatient]);

  const handleFieldChange = (key: string, val: string) => {
    const num = parseFloat(val);
    const resolved = isNaN(num) ? null : num;
    setFormData((prev) => ({ ...prev, [key]: resolved }));
    // If the field was missing and is now filled, remove from missing list
    if (resolved !== null) {
      setMissingFields((prev) => prev.filter((k) => k !== key));
    }
  };

  const resetDefaults = () => {
    setFormData(DEFAULT_VALUES);
    setPatientId("");
    setMissingFields([]);
    setResult(null);
    setError(null);
    setSavedSuccess(false);
    notify("Restored reference clinical case values.", "info");
  };

  const runPrediction = async () => {
    // Validate: no nulls allowed
    const stillMissing = CLINICAL_SCHEMA.filter((f) => formData[f.key] === null || formData[f.key] === undefined);
    if (stillMissing.length > 0) {
      setError(
        `Cannot compute: ${stillMissing.length} required field(s) are missing — ${stillMissing.map((f) => f.label).join(", ")}.`
      );
      notify("Please fill all highlighted fields before computing.", "error");
      return;
    }

    setLoading(true);
    setError(null);
    setSavedSuccess(false);
    try {
      const payload: Record<string, unknown> = {
        features: formData,
      };
      if (patientId.trim()) {
        payload.patient_identifier = patientId.trim();
      }

      const res = await api.post<PredictionResponse>("/predictions/predict", payload);
      setResult(res);
      setSavedSuccess(true);
      notify(`Assessment saved: ${res.result.predicted_label}`, "success");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Inference service unavailable";
      setError(msg);
      notify(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  // Check if a lab value deviates from typical standard ranges
  const isAbnormal = (key: string, val: number | null) => {
    if (val === null) return false;
    if (key === "eGFR" && val < 60) return true;
    if (key === "creatinine" && (val > 1.3 || val < 0.7)) return true;
    if (key === "bun" && val > 20) return true;
    if (key === "uacr" && val > 30) return true;
    if (key === "hsCRP" && val > 3.0) return true;
    if (key === "systolic_bp" && val > 135) return true;
    return false;
  };

  const currentTabFields = CLINICAL_SCHEMA.filter((f) => f.category === activeTab);
  const totalMissing = CLINICAL_SCHEMA.filter((f) => formData[f.key] === null).length;
  const isPatientSelected = patientId !== "";

  const getRiskBadge = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes("high")) return <Badge variant="critical">High Cognitive Risk</Badge>;
    if (l.includes("moderate")) return <Badge variant="elevated">Moderate Cognitive Risk</Badge>;
    if (l.includes("low")) return <Badge variant="moderate">Low Cognitive Risk</Badge>;
    return <Badge variant="normal">No Cognitive Risk</Badge>;
  };

  // Tab summary helper — shows null count for tab
  const tabMissingCount = (tab: ClinicalTab) =>
    CLINICAL_SCHEMA.filter((f) => f.category === tab && formData[f.key] === null).length;

  const egfr = formData["eGFR"];
  const uacr = formData["uacr"];
  const hsCRP = formData["hsCRP"];

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-primary">Prediction Studio</h1>
            <span className="rounded bg-clinical-teal-light px-2 py-0.5 text-xs font-semibold text-clinical-teal-dark">
              Decision Support Center
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Multivariate risk stratification across 18 clinical, renal, and neurovascular biomarkers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={resetDefaults}>
            <RotateCcw className="h-3.5 w-3.5 mr-1" />
            Reset Baseline
          </Button>
          <Button
            variant="teal"
            size="sm"
            onClick={runPrediction}
            disabled={loading || (isPatientSelected && totalMissing > 0)}
            className="shadow-subtle"
            title={isPatientSelected && totalMissing > 0 ? `${totalMissing} required field(s) missing` : undefined}
          >
            {loading ? <Spinner label="Evaluating..." /> : <BrainCircuit className="h-4 w-4 mr-1.5" />}
            Compute & Save Prediction
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Missing fields banner */}
      {isPatientSelected && totalMissing > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3.5 text-sm">
          <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-800">
              {totalMissing} biomarker(s) not on record for this patient.
            </span>
            <span className="text-amber-700 ml-1">
              Fields marked below must be entered before the assessment can be computed.
            </span>
          </div>
        </div>
      )}

      {/* Main Grid: Guided Intake Panel (Left) & Model Assessment (Right) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: 3-Category Guided Intake */}
        <div className="space-y-4 lg:col-span-7">
          <Card>
            <CardHeader className="bg-surface-subtle/50 pb-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <CardTitle>Clinical Biomarker Intake</CardTitle>
                  <CardDescription>Select registered patient or enter lab telemetry.</CardDescription>
                </div>

                {/* Patient Selector Dropdown */}
                <div className="flex items-center gap-2">
                  <UserCheck className="h-3.5 w-3.5 text-clinical-teal" />
                  <select
                    value={patientId}
                    onChange={(e) => handleSelectPatient(e.target.value)}
                    className="h-8 rounded-lg border border-border bg-surface px-2.5 text-xs font-medium text-text-primary focus:border-clinical-teal focus:outline-none"
                  >
                    <option value="">Select Registered Patient (Optional)</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.patient_identifier}>
                        {p.patient_identifier} — {p.first_name || ""} {p.last_name || ""}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Categorical Tabs */}
              <div className="flex gap-2 pt-3 border-t border-border mt-3">
                {(["demographics", "renal", "metabolic"] as ClinicalTab[]).map((tab, idx) => {
                  const labels = ["1. Demographics", "2. Renal Panel", "3. Metabolic & Electrolytes"];
                  const missing = tabMissingCount(tab);
                  return (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setActiveTab(tab)}
                      className={`flex-1 rounded-lg py-1.5 text-xs font-medium transition-colors relative ${
                        activeTab === tab
                          ? "bg-primary text-white shadow-subtle"
                          : "bg-surface text-text-secondary hover:bg-surface-hover"
                      }`}
                    >
                      {labels[idx]}
                      {missing > 0 && (
                        <span className="ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[9px] font-bold text-white">
                          {missing}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardHeader>

            <CardContent className="pt-5">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {currentTabFields.map((field) => {
                  const val = formData[field.key];
                  const isNotOnRecord = val === null;
                  const abnormal = !isNotOnRecord && isAbnormal(field.key, val);

                  return (
                    <div
                      key={field.key}
                      className={`rounded-lg border p-3 transition-colors ${
                        isNotOnRecord
                          ? "border-amber-400 bg-amber-50/40 ring-1 ring-amber-300"
                          : abnormal
                          ? "border-amber-200 bg-amber-50/20"
                          : "border-border bg-surface"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-semibold text-text-primary">
                          {field.label}
                          {isNotOnRecord && (
                            <span className="ml-1.5 text-[10px] font-medium text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                              Required
                            </span>
                          )}
                        </label>
                        <span className="text-[10px] text-text-muted">
                          Ref: <strong className="text-text-secondary">{field.refRange}</strong>
                        </span>
                      </div>

                      <div className="mt-2 flex items-center gap-2">
                        <Input
                          type="number"
                          step={field.step || 1}
                          min={field.min}
                          max={field.max}
                          placeholder={isNotOnRecord ? "Not on Record — Enter value" : undefined}
                          value={val === null ? "" : val}
                          onChange={(e) => handleFieldChange(field.key, e.target.value)}
                          className={`font-mono text-sm font-semibold tabular-nums ${
                            isNotOnRecord ? "border-amber-400 placeholder:text-amber-500" : ""
                          }`}
                        />
                        <span className="whitespace-nowrap text-xs text-text-muted font-medium w-24 text-right">
                          {field.unit}
                        </span>
                      </div>

                      <div className="mt-1 flex items-center justify-between text-[10px] text-text-muted">
                        <span>{field.description}</span>
                        {isNotOnRecord && (
                          <span className="font-medium text-amber-700 flex items-center gap-0.5">
                            <AlertCircle className="h-2.5 w-2.5" /> Not on Record
                          </span>
                        )}
                        {!isNotOnRecord && abnormal && (
                          <span className="font-medium text-amber-700 flex items-center gap-0.5">
                            <AlertTriangle className="h-2.5 w-2.5" /> Abnormal
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Step Navigation Buttons */}
              <div className="mt-6 flex items-center justify-between border-t border-border pt-4">
                <span className="text-xs text-text-muted">
                  Showing category: <strong className="text-text-primary capitalize">{activeTab}</strong>
                  {totalMissing > 0 && (
                    <span className="ml-2 text-amber-700 font-medium">
                      ({totalMissing} field{totalMissing > 1 ? "s" : ""} still required)
                    </span>
                  )}
                </span>

                <div className="flex gap-2">
                  {activeTab !== "demographics" && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() =>
                        setActiveTab(activeTab === "metabolic" ? "renal" : "demographics")
                      }
                    >
                      Previous Panel
                    </Button>
                  )}
                  {activeTab !== "metabolic" ? (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() =>
                        setActiveTab(activeTab === "demographics" ? "renal" : "metabolic")
                      }
                    >
                      Next Panel
                      <ChevronRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  ) : (
                    <Button
                      variant="teal"
                      size="sm"
                      onClick={runPrediction}
                      disabled={loading || (isPatientSelected && totalMissing > 0)}
                    >
                      Compute & Save Assessment
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Model Output & Explainability Presentation */}
        <div className="space-y-4 lg:col-span-5">
          <Card>
            <CardHeader className="bg-surface-subtle/50 pb-3">
              <div>
                <CardTitle>Assessment Results & Decision Support</CardTitle>
                <CardDescription>Calibrated model probabilities and clinical drivers.</CardDescription>
              </div>
            </CardHeader>

            <CardContent className="space-y-5">
              {!result && !loading && (
                <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12 text-center text-text-muted">
                  <BrainCircuit className="h-10 w-10 text-slate-300 mb-2" />
                  <p className="text-xs font-semibold text-text-primary">Ready for Assessment</p>
                  <p className="mt-1 max-w-xs text-[11px] text-text-muted">
                    Configure clinical biomarkers on the left or select a registered patient, then click &quot;Compute &amp; Save Prediction&quot;.
                  </p>
                </div>
              )}

              {loading && (
                <div className="flex flex-col items-center justify-center py-16 text-center text-text-muted">
                  <Spinner label="Executing Scikit-Learn Model Pipeline..." />
                  <p className="mt-3 text-xs font-medium text-primary">Standardizing features and evaluating probabilities...</p>
                </div>
              )}

              {result && !loading && (
                <div className="space-y-5">
                  {/* Primary Output Banner */}
                  <div className="rounded-xl border border-border bg-surface-subtle p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-semibold tracking-wider text-text-muted uppercase">
                        Stratification Result
                      </span>
                      {getRiskBadge(result.result.predicted_label)}
                    </div>

                    <div className="mt-3 flex items-baseline justify-between">
                      <div>
                        <div className="text-2xl font-bold tracking-tight text-primary">
                          {result.result.predicted_label}
                        </div>
                        <div className="text-xs text-text-muted mt-0.5">
                          Model Confidence: <span className="font-semibold text-text-primary tabular-nums">{Math.round((result.result.confidence || 0) * 100)}%</span>
                        </div>
                      </div>

                      <div className="text-right">
                        <span className="text-[10px] text-text-muted block">Database Status</span>
                        {savedSuccess ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-risk-normal">
                            <Check className="h-3 w-3" /> Stored in DB (#{result.prediction_id || "OK"})
                          </span>
                        ) : (
                          <span className="text-[11px] text-text-muted">Transient</span>
                        )}
                      </div>
                    </div>

                    {/* Patient context */}
                    {patientId && (
                      <div className="mt-2 text-[10px] text-text-muted border-t border-border pt-2">
                        Patient: <span className="font-semibold text-text-secondary">{patientId}</span>
                      </div>
                    )}
                  </div>

                  {/* Multiclass Probability Distribution */}
                  {result.result.probabilities && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-semibold text-text-primary">
                        <span>Calibrated Probabilities (Per-Class)</span>
                        <span className="text-[10px] text-text-muted font-normal">Sum = 100%</span>
                      </div>

                      <div className="space-y-2.5 rounded-lg border border-border p-3.5 bg-surface">
                        {Object.entries(result.result.probabilities)
                          .sort(([, a], [, b]) => b - a)
                          .map(([label, prob]) => {
                            const pct = Math.round((prob || 0) * 100);
                            const isDominant =
                              label.toLowerCase() === result.result.predicted_label.toLowerCase();
                            const barColor = isDominant
                              ? "bg-clinical-teal"
                              : label.toLowerCase().includes("high")
                              ? "bg-risk-critical"
                              : label.toLowerCase().includes("moderate")
                              ? "bg-risk-moderate"
                              : label.toLowerCase().includes("low")
                              ? "bg-risk-normal"
                              : "bg-slate-300";

                            return (
                              <div key={label} className="space-y-1">
                                <div className="flex items-center justify-between text-xs">
                                  <span className={isDominant ? "font-bold text-primary" : "text-text-secondary"}>
                                    {label}
                                  </span>
                                  <span className="font-mono text-xs tabular-nums text-text-primary font-semibold">
                                    {pct}%
                                  </span>
                                </div>
                                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-300 ${barColor}`}
                                    style={{ width: `${Math.max(pct, 1)}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  {/* Explainable AI: Primary Contributing Factors */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-text-primary">
                      <span>Dominant Contributing Variables</span>
                      <span className="text-[10px] text-clinical-teal font-medium">Model Feature Impact</span>
                    </div>

                    <div className="space-y-2 text-xs">
                      {egfr !== null && egfr < 60 && (
                        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/50 p-2.5 text-text-primary">
                          <AlertTriangle className="h-4 w-4 text-risk-moderate flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-risk-moderate">Reduced eGFR ({egfr} mL/min)</div>
                            <div className="text-[11px] text-text-secondary mt-0.5">
                              Renal clearance deficiency is the dominant biological factor driving cognitive vulnerability.
                            </div>
                          </div>
                        </div>
                      )}

                      {uacr !== null && uacr > 30 && (
                        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50/50 p-2.5 text-text-primary">
                          <Activity className="h-4 w-4 text-risk-moderate flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-risk-moderate">Elevated Albuminuria ({uacr} mg/g)</div>
                            <div className="text-[11px] text-text-secondary mt-0.5">
                              Microvascular barrier damage in the glomerulus mirrors cerebral microvascular disease.
                            </div>
                          </div>
                        </div>
                      )}

                      {hsCRP !== null && hsCRP > 3.0 && (
                        <div className="flex items-start gap-2 rounded-lg border border-slate-200 bg-surface-subtle p-2.5 text-text-primary">
                          <Info className="h-4 w-4 text-text-secondary flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-text-primary">Elevated hsCRP ({hsCRP} mg/L)</div>
                            <div className="text-[11px] text-text-secondary mt-0.5">
                              Active systemic inflammation compounding neurocognitive stress.
                            </div>
                          </div>
                        </div>
                      )}

                      {egfr !== null && egfr >= 60 && (uacr === null || uacr <= 30) && (hsCRP === null || hsCRP <= 3.0) && (
                        <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50/40 p-2.5 text-text-primary">
                          <CheckCircle2 className="h-4 w-4 text-risk-normal flex-shrink-0 mt-0.5" />
                          <div>
                            <div className="font-semibold text-risk-normal">Biomarkers within acceptable range</div>
                            <div className="text-[11px] text-text-secondary mt-0.5">
                              No dominant individual biomarker flags detected. Risk is driven by combined profile.
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Recommended Next Clinical Steps */}
                  <div className="rounded-lg border border-teal-200 bg-clinical-teal-light/40 p-3">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-clinical-teal-dark">
                      <Stethoscope className="h-4 w-4" />
                      Care Protocol Actions
                    </div>
                    <ul className="mt-2 space-y-1 text-xs text-text-secondary">
                      <li className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3 w-3 text-clinical-teal" />
                        Administer formal Montreal Cognitive Assessment (MoCA) screening.
                      </li>
                      <li className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3 w-3 text-clinical-teal" />
                        Review nephrotoxic medications and optimize hemodynamic control.
                      </li>
                      <li className="flex items-center gap-1.5">
                        <CheckCircle2 className="h-3 w-3 text-clinical-teal" />
                        Recorded in patient longitudinal timeline and clinical audit log.
                      </li>
                    </ul>
                  </div>

                  {/* Governance Disclaimer */}
                  <div className="rounded-lg border border-border bg-surface-subtle px-3 py-2 text-[10px] text-text-muted text-center">
                    <History className="h-3 w-3 inline mr-1 mb-0.5" />
                    Clinical decision support tool. Must be corroborated by licensed nephrology evaluation.
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

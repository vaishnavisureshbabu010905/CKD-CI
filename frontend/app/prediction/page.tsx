"use client";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import { useApi } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";

type PredictionResponse = {
  model_version: string;
  result: {
    predicted_label: string;
    confidence?: number;
    probabilities?: Record<string, number>;
  };
};

const DEFAULT_FEATURES = {
  age: 62,
  gender: 1,
  egfr: 42,
  creatinine: 2.0,
  bun: 28,
  uacr: 300,
  hemoglobin: 10.5,
  albumin: 3.7,
  potassium: 4.6,
  phosphorus: 4.2,
  calcium: 9.1,
  systolic_bp: 142,
  bmi: 28.5,
  diabetes: 1,
  hypertension: 1,
  cvd: 0,
};

function normalizeFeatures(input: Record<string, unknown>) {
  const normalized = { ...DEFAULT_FEATURES, ...input } as Record<string, unknown>;
  if ("eGFR" in normalized && !("egfr" in normalized)) normalized.egfr = normalized.eGFR;
  if ("phosphate" in normalized && !("phosphorus" in normalized)) normalized.phosphorus = normalized.phosphate;
  delete normalized.eGFR;
  delete normalized.phosphate;
  return normalized;
}

function recommendationFor(label: string): string {
  const value = label.toLowerCase();
  if (value.includes("high")) return "Escalate to nephrologist and schedule immediate cognitive follow-up.";
  if (value.includes("moderate")) return "Plan follow-up assessment within 2 weeks and monitor labs closely.";
  if (value.includes("low")) return "Continue routine monitoring and reinforce care-plan adherence.";
  return "Review result with care team and align next clinical action.";
}

function riskTone(label: string): string {
  const value = label.toLowerCase();
  if (value.includes("high")) return "text-red-300";
  if (value.includes("moderate")) return "text-amber-300";
  if (value.includes("low")) return "text-emerald-300";
  return "text-slate-200";
}

function formatPercent(v?: number): string {
  return `${Math.round((v || 0) * 100)}%`;
}

export default function PredictionPage() {
  const api = useApi();
  const [features, setFeatures] = useState(JSON.stringify(DEFAULT_FEATURES, null, 2));
  const [patientIdentifier, setPatientIdentifier] = useState("");
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { notify } = useToast();

  const runPrediction = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const parsedFeatures = JSON.parse(features);
      const normalizedFeatures = normalizeFeatures(parsedFeatures);
      const payload = {
        patient_identifier: patientIdentifier || undefined,
        features: normalizedFeatures,
      };

      let response: PredictionResponse;
      try {
        response = await api.post<PredictionResponse>("/predictions/predict", payload);
      } catch {
        // Fallback to legacy endpoint contract
        const legacy = await api.post<{ predicted_label: string; confidence?: number; probabilities?: Record<string, number> }>(
          "/predict",
          normalizedFeatures
        );
        response = {
          model_version: "legacy",
          result: {
            predicted_label: legacy.predicted_label,
            confidence: legacy.confidence,
            probabilities: legacy.probabilities,
          },
        };
      }
      setResult(response);
      notify("Prediction completed", "success");
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Prediction failed");
      notify(err.message || "Prediction failed", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-border/70 bg-gradient-to-b from-slate-950/90 to-slate-900/90">
      <CardHeader className="space-y-1">
        <CardTitle>CKD Prediction Workspace</CardTitle>
        <p className="text-sm text-slate-300">Run inference, review calibrated risk, and export patient report from the patient profile page.</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
          <div className="space-y-3 rounded-lg border border-border bg-panel/70 p-3">
            <div className="text-xs uppercase tracking-wide text-slate-400">Clinical feature payload</div>
            <Textarea
              rows={12}
              value={features}
              onChange={(e) => setFeatures(e.target.value)}
              className="font-mono"
              placeholder='Paste feature JSON, e.g. {"eGFR": 42, "creatinine": 2.0}'
            />
            <div className="flex flex-wrap gap-2 text-xs text-slate-400">
              <span className="rounded-full bg-slate-800 px-2 py-1">egfr</span>
              <span className="rounded-full bg-slate-800 px-2 py-1">creatinine</span>
              <span className="rounded-full bg-slate-800 px-2 py-1">uacr</span>
              <span className="rounded-full bg-slate-800 px-2 py-1">hemoglobin</span>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-panel/70 p-3 text-sm text-slate-200">
            <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Risk result</div>
            {loading && <Spinner label="Running prediction..." />}
            {error && <ErrorBanner message={error} />}
            {!loading && !error && !result && <div className="text-slate-400">Awaiting run...</div>}
            {result && (
              <div className="space-y-3">
                <div className={`text-lg font-semibold ${riskTone(result.result.predicted_label)}`}>
                  {result.result.predicted_label.replace(/_/g, " ")}
                </div>
                <div>Confidence: <span className="font-semibold">{formatPercent(result.result.confidence)}</span></div>
                <div>Model version: <span className="font-semibold">{result.model_version}</span></div>
                <div className="rounded-md bg-slate-900/70 p-2 text-slate-300">{recommendationFor(result.result.predicted_label)}</div>
                {!!result.result.probabilities && (
                  <div className="space-y-2">
                    {Object.entries(result.result.probabilities).map(([label, value]) => (
                      <div key={label}>
                        <div className="mb-1 flex justify-between text-xs text-slate-300">
                          <span>{label}</span>
                          <span>{formatPercent(value)}</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-800">
                          <div className="h-2 rounded-full bg-cyan-400" style={{ width: formatPercent(value) }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Input
            className="max-w-sm"
            placeholder="Patient Identifier (optional)"
            value={patientIdentifier}
            onChange={(e) => setPatientIdentifier(e.target.value)}
          />
          <Button onClick={runPrediction} disabled={loading}>Run prediction</Button>
          <Button
            variant="outline"
            onClick={() => {
              setFeatures(JSON.stringify(DEFAULT_FEATURES, null, 2));
              setError(null);
            }}
          >
            Reset sample data
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

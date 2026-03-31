"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SummaryCards } from "@/components/sections/summary-cards";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type AlertEvent = { id: number; status: string; payload?: Record<string, unknown> };
type Task = { id: number; title: string; status: string };
type Patient = { id: number };
type PredictionHistory = {
  id: number;
  patient_id?: number;
  model_version?: string;
  predicted_label?: string;
  confidence?: number;
  created_at?: string;
};

function asPercent(value?: number) {
  return `${Math.round((value || 0) * 100)}%`;
}

export default function CommandCenterPage() {
  const api = useApi();
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const riskStats = predictions.reduce(
    (acc, p) => {
      const label = (p.predicted_label || "unknown").toLowerCase();
      if (label.includes("high")) acc.high += 1;
      else if (label.includes("moderate")) acc.moderate += 1;
      else if (label.includes("low")) acc.low += 1;
      else acc.unknown += 1;
      return acc;
    },
    { high: 0, moderate: 0, low: 0, unknown: 0 }
  );

  const totalRisk = Math.max(1, riskStats.high + riskStats.moderate + riskStats.low + riskStats.unknown);
  const highPct = Math.round((riskStats.high / totalRisk) * 100);
  const moderatePct = Math.round((riskStats.moderate / totalRisk) * 100);
  const lowPct = Math.round((riskStats.low / totalRisk) * 100);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [alertData, taskData, patientData, predictionData] = await Promise.allSettled([
          api.get<AlertEvent[]>("/alerts/events"),
          api.get<Task[]>("/collab/tasks"),
          api.get<Patient[]>("/patients/"),
          api.get<PredictionHistory[]>("/predictions/history"),
        ]);
        if (mounted) {
          setAlerts(alertData.status === "fulfilled" ? (alertData.value || []) : []);
          setTasks(taskData.status === "fulfilled" ? (taskData.value || []) : []);
          setPatients(patientData.status === "fulfilled" ? (patientData.value || []) : []);
          setPredictions(predictionData.status === "fulfilled" ? (predictionData.value || []) : []);

          const failed: string[] = [];
          if (alertData.status === "rejected") failed.push("alerts");
          if (taskData.status === "rejected") failed.push("tasks");
          if (patientData.status === "rejected") failed.push("patients");
          if (predictionData.status === "rejected") failed.push("predictions");
          if (failed.length) {
            setError(`Some sections failed to load: ${failed.join(", ")}`);
          }
        }
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load command center data");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [api]);

  return (
    <div className="space-y-4">
      <SummaryCards
        patientCount={patients.length}
        alertCount={alerts.length}
        taskCount={tasks.filter((t) => t.status !== "done").length}
        predictionCount={predictions.length}
      />
      {loading && <Spinner label="Loading command center..." />}
      {error && <ErrorBanner message={error} />}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Live Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.map((a) => (
              <div key={a.id} className="flex items-center justify-between rounded-md bg-panel px-3 py-2">
                <div>{String(a.payload?.message || a.payload?.detail || `Alert #${a.id}`)}</div>
                <Badge className="bg-red-500/20 text-red-200">{a.status}</Badge>
              </div>
            ))}
            {!alerts.length && !loading && <div className="text-sm text-slate-400">No active alerts.</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Tasks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {tasks.map((t) => (
              <div key={t.id} className="rounded-md border border-border bg-panel px-3 py-2">
                <div className="font-semibold">{t.title}</div>
                <div className="text-xs text-slate-400">{t.status}</div>
              </div>
            ))}
            {!tasks.length && !loading && <div className="text-sm text-slate-400">No tasks assigned.</div>}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Operational Load (Bar)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-40 items-end justify-between gap-3">
              {[
                { name: "Patients", value: patients.length, color: "bg-cyan-400" },
                { name: "Alerts", value: alerts.length, color: "bg-rose-400" },
                { name: "Tasks", value: tasks.length, color: "bg-amber-400" },
                { name: "Pred", value: predictions.length, color: "bg-emerald-400" },
              ].map((item) => {
                const maxValue = Math.max(1, patients.length, alerts.length, tasks.length, predictions.length);
                const height = Math.max(8, Math.round((item.value / maxValue) * 120));
                return (
                  <div key={item.name} className="flex flex-1 flex-col items-center gap-2">
                    <div className="text-xs text-slate-300">{item.value}</div>
                    <div className={`w-full rounded-t ${item.color}`} style={{ height }} />
                    <div className="text-xs text-slate-400">{item.name}</div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Mix (Pie)</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            <div
              className="h-28 w-28 rounded-full border border-border"
              style={{
                background: `conic-gradient(#f43f5e 0 ${highPct}%, #f59e0b ${highPct}% ${highPct + moderatePct}%, #34d399 ${highPct + moderatePct}% ${highPct + moderatePct + lowPct}%, #64748b ${highPct + moderatePct + lowPct}% 100%)`,
              }}
            />
            <div className="space-y-1 text-sm">
              <div className="text-rose-300">High: {riskStats.high}</div>
              <div className="text-amber-300">Moderate: {riskStats.moderate}</div>
              <div className="text-emerald-300">Low: {riskStats.low}</div>
              <div className="text-slate-400">Unknown: {riskStats.unknown}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prediction Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-300">
            <div className="flex justify-between"><span>Total predictions</span><span>{predictions.length}</span></div>
            <div className="flex justify-between"><span>High-risk share</span><span>{Math.round((riskStats.high / totalRisk) * 100)}%</span></div>
            <div className="flex justify-between"><span>Moderate-risk share</span><span>{Math.round((riskStats.moderate / totalRisk) * 100)}%</span></div>
            <div className="flex justify-between"><span>Low-risk share</span><span>{Math.round((riskStats.low / totalRisk) * 100)}%</span></div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Prediction History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-md border border-border">
            <div className="grid min-w-[760px] grid-cols-[90px_110px_1fr_120px_170px] gap-2 bg-slate-900/90 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
              <div>Record</div>
              <div>Patient</div>
              <div>Prediction</div>
              <div>Confidence</div>
              <div>Timestamp</div>
            </div>
            {predictions.slice(0, 12).map((p) => (
              <div key={p.id} className="grid min-w-[760px] grid-cols-[90px_110px_1fr_120px_170px] gap-2 border-t border-border px-3 py-2 text-sm text-slate-200">
                <div>#{p.id}</div>
                <div>{p.patient_id || "N/A"}</div>
                <div className="capitalize">{(p.predicted_label || "unknown").replace(/_/g, " ")}</div>
                <div>{asPercent(p.confidence)}</div>
                <div>{p.created_at ? new Date(p.created_at).toLocaleString() : "N/A"}</div>
              </div>
            ))}
            {!predictions.length && !loading && (
              <div className="px-3 py-4 text-sm text-slate-400">No prediction history found.</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

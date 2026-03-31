"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type Patient = {
  id: number;
  patient_identifier: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
  features?: Record<string, unknown>;
};

type TimelineEvent = {
  id: number;
  source_type: string;
  summary?: string;
  event_time: string;
};

function getAge(dateOfBirth?: string) {
  if (!dateOfBirth) return null;
  const dob = new Date(dateOfBirth);
  if (Number.isNaN(dob.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDelta = today.getMonth() - dob.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age;
}

export default function PatientDetailPage({ params }: { params: { id: string } }) {
  const api = useApi();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [history, setHistory] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [patientData, timelineData] = await Promise.all([
          api.get<Patient>(`/patients/${params.id}`),
          api.get<TimelineEvent[]>(`/timeline/${params.id}`),
        ]);
        if (mounted) {
          setPatient(patientData);
          setHistory(timelineData || []);
        }
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load patient details");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [api, params.id]);

  if (loading) return <Spinner label="Loading patient..." />;
  if (error) return <ErrorBanner message={error} />;
  if (!patient) return <ErrorBanner message="Patient not found" />;

  const patientName = `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || "Unknown Patient";
  const age = getAge(patient.date_of_birth);

  const sourceCounts = history.reduce(
    (acc, item) => {
      const source = item.source_type.toLowerCase();
      if (source.includes("prediction")) acc.prediction += 1;
      else if (source.includes("alert")) acc.alert += 1;
      else if (source.includes("task") || source.includes("note")) acc.task += 1;
      else acc.other += 1;
      return acc;
    },
    { prediction: 0, alert: 0, task: 0, other: 0 }
  );
  const totalEvents = Math.max(1, sourceCounts.prediction + sourceCounts.alert + sourceCounts.task + sourceCounts.other);

  const features = patient.features || {};
  const egfr = Number(features.egfr || features.eGFR || 0) || 0;
  const creatinine = Number(features.creatinine || 0) || 0;
  const uacr = Number(features.uacr || 0) || 0;
  const metricMax = Math.max(1, egfr, creatinine * 30, uacr / 10);

  const downloadReport = async () => {
    try {
      const blob = await api.download(`/patients/${params.id}/report.pdf`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${patient.patient_identifier || `patient-${params.id}`}-report.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Failed to download report");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">{patientName}</h1>
          <div className="text-sm text-slate-400">{patient.patient_identifier} • Age {age ?? "N/A"} • {patient.date_of_birth || "DOB N/A"} • {patient.sex || "N/A"}</div>
        </div>
        <Badge className="bg-slate-700 text-slate-100">Patient</Badge>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Timeline Mix (Pie)</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            <div
              className="h-24 w-24 rounded-full border border-border"
              style={{
                background: `conic-gradient(#22d3ee 0 ${(sourceCounts.prediction / totalEvents) * 100}%, #fb7185 ${(sourceCounts.prediction / totalEvents) * 100}% ${((sourceCounts.prediction + sourceCounts.alert) / totalEvents) * 100}%, #f59e0b ${((sourceCounts.prediction + sourceCounts.alert) / totalEvents) * 100}% ${((sourceCounts.prediction + sourceCounts.alert + sourceCounts.task) / totalEvents) * 100}%, #64748b ${((sourceCounts.prediction + sourceCounts.alert + sourceCounts.task) / totalEvents) * 100}% 100%)`,
              }}
            />
            <div className="space-y-1 text-sm text-slate-300">
              <div className="text-cyan-300">Prediction: {sourceCounts.prediction}</div>
              <div className="text-rose-300">Alert: {sourceCounts.alert}</div>
              <div className="text-amber-300">Task/Note: {sourceCounts.task}</div>
              <div className="text-slate-400">Other: {sourceCounts.other}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Clinical Features (Bar)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex h-28 items-end gap-3">
              {[
                { key: "eGFR", value: egfr, color: "bg-cyan-400" },
                { key: "Creat", value: creatinine * 30, color: "bg-fuchsia-400" },
                { key: "UACR", value: uacr / 10, color: "bg-emerald-400" },
              ].map((item) => {
                const height = Math.max(10, Math.round((item.value / metricMax) * 88));
                return (
                  <div key={item.key} className="flex flex-1 flex-col items-center gap-1">
                    <div className="text-xs text-slate-400">{item.key}</div>
                    <div className={`w-full rounded-t ${item.color}`} style={{ height }} />
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <button
          type="button"
          onClick={downloadReport}
          className="rounded-md border border-border bg-panel px-3 py-2 text-sm text-slate-100 hover:bg-slate-800"
        >
          Download PDF Report
        </button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {history.map((h) => (
            <div key={h.id} className="flex items-center justify-between rounded-md bg-panel px-3 py-2">
              <div>
                <div className="font-semibold capitalize">{h.source_type}</div>
                <div className="text-sm text-slate-300">{h.summary || "No summary"}</div>
              </div>
              <div className="text-xs text-slate-400">{new Date(h.event_time).toLocaleString()}</div>
            </div>
          ))}
          {!history.length && <div className="text-sm text-slate-400">No timeline events yet.</div>}
          <div className="flex gap-2 text-sm text-slate-300">
            <Link className="underline" href="/prediction">Run prediction</Link>
            <Link className="underline" href="/timeline">View timeline</Link>
            <Link className="underline" href="/chat">Open chat</Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type Event = {
  id: number;
  source_type: string;
  summary?: string;
  event_time: string;
};

type Patient = {
  id: number;
  patient_identifier?: string;
  first_name?: string;
  last_name?: string;
};

export default function TimelinePage() {
  const api = useApi();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientId, setPatientId] = useState("");
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const loadPatients = async () => {
      try {
        const data = await api.get<Patient[]>("/patients/");
        if (!mounted) return;
        const list = data || [];
        setPatients(list);
        if (list.length > 0) {
          setPatientId(String(list[0].id));
        }
      } catch {
        // Keep manual input available if patient preload fails.
      }
    };
    loadPatients();
    return () => {
      mounted = false;
    };
  }, [api]);

  const loadTimeline = async () => {
    if (!patientId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<Event[]>(`/timeline/${patientId}`);
      setEvents(data || []);
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Failed to load timeline");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) {
      void loadTimeline();
    }
    // Intentionally skip loadTimeline in dependency list to avoid recreating requests.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const selectedPatientName = useMemo(() => {
    const selected = patients.find((p) => String(p.id) === patientId);
    if (!selected) return null;
    return `${selected.first_name || "Patient"} ${selected.last_name || ""}`.trim();
  }, [patientId, patients]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Timeline</CardTitle>
        <p className="text-sm text-slate-400">Timeline tracks patient-level events from predictions, alerts, tasks/notes, and care-team activity.</p>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <select
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="h-10 min-w-[260px] rounded-md border border-border bg-background px-3 text-sm text-slate-200"
          >
            <option value="">Select patient</option>
            {patients.map((p) => (
              <option key={p.id} value={String(p.id)}>
                {(p.patient_identifier || `Patient #${p.id}`) + " - " + `${p.first_name || ""} ${p.last_name || ""}`.trim()}
              </option>
            ))}
          </select>
          <Input value={patientId} onChange={(e) => setPatientId(e.target.value)} placeholder="Or enter patient numeric ID" className="max-w-xs" />
          <Button onClick={loadTimeline} disabled={loading}>Load</Button>
        </div>
        {selectedPatientName && <div className="text-sm text-slate-300">Showing events for {selectedPatientName}</div>}
        {loading && <Spinner label="Loading timeline..." />}
        {error && <ErrorBanner message={error} />}
        {events.map((e) => (
          <div key={e.id} className="flex items-center gap-3 rounded-md bg-panel px-3 py-2">
            <span className="text-xs uppercase tracking-wide text-slate-400">{e.source_type}</span>
            <span className="flex-1 text-slate-200">{e.summary || "No summary"}</span>
            <span className="text-xs text-slate-500">{new Date(e.event_time).toLocaleString()}</span>
          </div>
        ))}
        {!loading && !events.length && <div className="text-sm text-slate-400">No events loaded yet.</div>}
      </CardContent>
    </Card>
  );
}

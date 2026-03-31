"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useApi } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type ModelEntry = {
  id: number;
  model_name?: string;
  name?: string;
  version: string;
  is_active: boolean;
};

export default function AdminPage() {
  const api = useApi();
  const { notify } = useToast();
  const [modelName, setModelName] = useState("ckd-ci");
  const [version, setVersion] = useState("");
  const [models, setModels] = useState<ModelEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<ModelEntry[]>("/models");
      setModels(data || []);
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Failed to load model registry");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const registerModel = async () => {
    try {
      await api.post<{ id: number }>("/models/register", { model_name: modelName, version, stage: "dev" });
      notify("Model registered", "success");
      setVersion("");
      await loadModels();
    } catch (e: unknown) {
      const err = e as Error;
      notify(err.message || "Failed to register model", "error");
    }
  };

  const activateModel = async (id: number) => {
    try {
      await api.post<{ status: string; model_id: number }>(`/clinical/governance/activate/${id}`);
      notify("Model activation updated", "success");
      await loadModels();
    } catch (e: unknown) {
      const err = e as Error;
      notify(err.message || "Failed to activate model", "error");
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Model Governance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Input placeholder="Model name" value={modelName} onChange={(e) => setModelName(e.target.value)} />
            <Input placeholder="Version" value={version} onChange={(e) => setVersion(e.target.value)} />
            <Button onClick={registerModel}>Register</Button>
          </div>
          {loading && <Spinner label="Loading model registry..." />}
          {error && <ErrorBanner message={error} />}
          <div className="space-y-2">
            {models.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-md bg-panel px-3 py-2">
                <div>
                  <div className="font-semibold">{m.model_name || m.name || "Model"} v{m.version}</div>
                  <div className="text-xs text-slate-400">{m.is_active ? "Active" : "Inactive"}</div>
                </div>
                <Button variant={m.is_active ? "secondary" : "primary"} onClick={() => activateModel(m.id)}>
                  {m.is_active ? "Active" : "Activate"}
                </Button>
              </div>
            ))}
            {!loading && !models.length && <div className="text-sm text-slate-400">No models registered.</div>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";
import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { WS_BASE } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { ErrorBanner } from "@/components/ui/error-banner";

interface Message {
  id: number;
  sender_id?: number;
  content: string;
  created_at?: string;
}

type Thread = {
  id: number;
  name?: string;
  thread_type: string;
};

export default function ChatPage() {
  const api = useApi();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selected, setSelected] = useState<Thread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let mounted = true;
    const loadThreads = async () => {
      try {
        let data = await api.get<Thread[]>("/chat/threads");
        if ((data || []).length === 0) {
          const created = await api.post<Thread>("/chat/threads", {
            thread_type: "team",
            name: "Care Team Live Chat",
            participants: [],
          });
          data = [created];
        }
        if (!mounted) return;
        setThreads(data || []);
        if ((data || []).length > 0) {
          setSelected((data || [])[0]);
        }
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load chat threads");
      }
    };
    loadThreads();
    return () => {
      mounted = false;
    };
  }, [api]);

  useEffect(() => {
    if (!selected) return;

    const loadMessages = async () => {
      try {
        const data = await api.get<Message[]>(`/chat/messages?thread_id=${selected.id}`);
        setMessages(data || []);
      } catch (e: unknown) {
        const err = e as Error;
        setError(err.message || "Failed to load messages");
      }
    };
    loadMessages();

    const ws = new WebSocket(`${WS_BASE}/chat/ws/${selected.id}`);
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "message" && data.message?.content) {
          setMessages((m) => [
            ...m,
            {
              id: Date.now(),
              sender_id: data.message.sender_id,
              content: data.message.content,
              created_at: new Date().toISOString(),
            },
          ]);
        }
      } catch (e) {
        console.error(e);
      }
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [api, selected]);

  const sendMessage = async () => {
    if (!draft.trim() || !selected) return;
    setError(null);
    try {
      const created = await api.post<Message>("/chat/messages", { thread_id: selected.id, content: draft });
      setMessages((m) => [...m, created]);
      wsRef.current?.send(JSON.stringify({ type: "message", message: created }));
      setDraft("");
      const refreshed = await api.get<Message[]>(`/chat/messages?thread_id=${selected.id}`);
      setMessages(refreshed || []);
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Failed to send message");
    }
  };

  return (
    <div className="grid gap-4 lg:grid-cols-4">
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Threads</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {threads.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelected(t)}
              className={`w-full rounded-md px-3 py-2 text-left ${selected?.id === t.id ? "bg-slate-800" : "bg-panel"}`}
            >
              <div className="font-semibold">{t.name || `${t.thread_type} thread`}</div>
              <div className="text-xs text-slate-400">Thread #{t.id}</div>
            </button>
          ))}
        </CardContent>
      </Card>
      <Card className="lg:col-span-3 flex flex-col">
        <CardHeader>
          <CardTitle>{selected?.name || "Care-Team Chat"} (WhatsApp-style)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-3">
          {error && <ErrorBanner message={error} />}
          <div className="flex-1 space-y-3 overflow-y-auto rounded-md bg-panel p-3 scrollbar-thin">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.sender_id ? "justify-start" : "justify-end"}`}>
                <div className={`max-w-xs rounded-2xl px-3 py-2 text-sm ${m.sender_id ? "bg-slate-800 text-slate-100" : "bg-accent text-slate-950"}`}>
                  <div className="text-xs font-semibold opacity-70">{m.sender_id ? `User ${m.sender_id}` : "Care Assistant"}</div>
                  <div>{m.content}</div>
                  <div className="text-[10px] opacity-60">{m.created_at ? new Date(m.created_at).toLocaleTimeString() : "now"}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Input placeholder="Type a message" value={draft} onChange={(e) => setDraft(e.target.value)} />
            <Button onClick={sendMessage} disabled={!selected}>Send</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

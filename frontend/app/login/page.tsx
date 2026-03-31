"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();
  const { login } = useAuth();
  const { notify } = useToast();

  const handleLogin = async () => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password.trim()) {
      setError("Please provide email and password");
      notify("Please provide email and password", "error");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      await login(trimmedEmail, password);
      notify("Login successful", "success");
      router.push("/command-center");
    } catch (e: unknown) {
      const err = e as Error;
      setError(err.message || "Login failed");
      notify(err.message || "Login failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Login</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              void handleLogin();
            }}
          >
            <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
            <Input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <div className="text-sm text-red-400">{error}</div>}
            <Button className="w-full" type="submit" disabled={submitting}>
              {submitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

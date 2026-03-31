import "./globals.css";
import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppShell } from "@/components/layout/app-shell";

export const metadata: Metadata = {
  title: "CKD-CI Command Center",
  description: "Hospital-grade CKD-CI frontend",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-slate-100">
        <Providers>
          <AppShell>
            <main className="space-y-4">
              <ProtectedRoute>{children}</ProtectedRoute>
            </main>
          </AppShell>
        </Providers>
      </body>
    </html>
  );
}

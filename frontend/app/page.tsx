import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="flex flex-col items-start gap-4 rounded-lg border border-border bg-card/70 p-6">
      <h1 className="text-2xl font-bold">Welcome to CKD-CI Command Center</h1>
      <p className="text-slate-300">Track patients, collaborate, and run CKD predictions in one place.</p>
      <div className="flex gap-3">
        <Link href="/login"><Button variant="primary">Login</Button></Link>
        <Link href="/command-center"><Button variant="secondary">Command Center</Button></Link>
      </div>
    </div>
  );
}

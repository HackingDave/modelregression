import Link from "next/link";
import { Activity } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-muted/50 mb-6">
          <Activity className="w-8 h-8 text-muted-foreground" />
        </div>
        <h1 className="text-4xl font-bold font-mono text-foreground mb-2">
          404
        </h1>
        <p className="text-muted-foreground mb-6">
          This page doesn&apos;t exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary/20 transition-colors"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}

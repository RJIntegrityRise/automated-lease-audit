import { FileSearch } from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

export function AppHeader() {
  return (
    <header className="border-b border-border bg-card text-card-foreground">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <FileSearch className="h-6 w-6" />

          <div>
            <h1 className="font-semibold">
              Automated Lease Audit
            </h1>

            <p className="text-sm text-muted-foreground">
              Upload and review residential leases
            </p>
          </div>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
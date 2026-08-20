import { AppHeader } from "@/components/app-header";
import { AuthGuard } from "@/components/auth-guard";
import { DashboardView } from "@/components/dashboard-view";

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <AppHeader />

        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <DashboardView />
        </main>
      </div>
    </AuthGuard>
  );
}
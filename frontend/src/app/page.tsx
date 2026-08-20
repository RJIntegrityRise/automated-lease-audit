import { AppHeader } from "@/components/app-header";
import { AuthGuard } from "@/components/auth-guard";
import { LeaseUploadForm } from "@/components/lease-upload-form";

export default function HomePage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background text-foreground">
        <AppHeader />

        <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
          <section className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Lease processing
            </p>

            <h2 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
              Review a lease document
            </h2>

            <p className="mt-3 max-w-2xl text-muted-foreground">
              Upload a residential lease to store the original PDF
              securely and extract its page-level text.
            </p>
          </section>

          <LeaseUploadForm />
        </main>
      </div>
    </AuthGuard>
  );
}
import { AppHeader } from "@/components/app-header";
import { LeaseDetailView } from "@/components/lease-detail-view";

type LeasePageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function LeasePage({
  params,
}: LeasePageProps) {
  const { id } = await params;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <AppHeader />

      <main className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-8">
        <LeaseDetailView leaseId={id} />
      </main>
    </div>
  );
}
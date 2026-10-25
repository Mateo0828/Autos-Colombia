import { SummaryProvider } from "./SummaryContext";
import Sidebar from "./Sidebar";
import SummaryPanel from "./SummaryPanel";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <SummaryProvider>
      <div className="flex min-h-screen bg-[radial-gradient(ellipse_at_top,#12326a_0%,#0a1b3d_45%)]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-6 py-12 lg:px-10">
          <div className="mx-auto max-w-[1010px]">{children}</div>
        </main>
        <SummaryPanel />
      </div>
    </SummaryProvider>
  );
}

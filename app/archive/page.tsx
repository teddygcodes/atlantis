import { Navigation } from "@/components/navigation";
import { Archive } from "@/components/archive";

export default function ArchivePage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <Archive />
      </main>
    </>
  );
}

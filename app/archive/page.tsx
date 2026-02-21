import { Navigation } from "@/components/navigation";
import { Archive } from "@/components/archive";

export default function ArchivePage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
        <Archive />
      </main>
    </>
  );
}

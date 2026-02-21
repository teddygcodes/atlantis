import { Navigation } from "@/components/navigation";
import { Archive } from "@/components/archive";

export default function ArchivePage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <Archive />
      </main>
    </>
  );
}

import { Navigation } from "@/components/navigation";
import { Debates } from "@/components/debates";

export default function DebatesPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
        <Debates />
      </main>
    </>
  );
}

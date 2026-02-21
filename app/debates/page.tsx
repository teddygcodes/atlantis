import { Navigation } from "@/components/navigation";
import { Debates } from "@/components/debates";

export default function DebatesPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <Debates />
      </main>
    </>
  );
}

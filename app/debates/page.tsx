import { Navigation } from "@/components/navigation";
import { Debates } from "@/components/debates";

export default function DebatesPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <Debates />
      </main>
    </>
  );
}

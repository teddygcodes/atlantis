import { Navigation } from "@/components/navigation";
import { States } from "@/components/states";

export default function StatesPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <States />
      </main>
    </>
  );
}

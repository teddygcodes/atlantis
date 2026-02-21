import { Navigation } from "@/components/navigation";
import { States } from "@/components/states";

export default function StatesPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
        <States />
      </main>
    </>
  );
}

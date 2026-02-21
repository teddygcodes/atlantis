import { Navigation } from "@/components/navigation";
import { States } from "@/components/states";

export default function StatesPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <States />
      </main>
    </>
  );
}

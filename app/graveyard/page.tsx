import { Navigation } from "@/components/navigation";
import { Graveyard } from "@/components/graveyard";

export default function GraveyardPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
        <Graveyard />
      </main>
    </>
  );
}

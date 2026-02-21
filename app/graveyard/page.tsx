import { Navigation } from "@/components/navigation";
import { Graveyard } from "@/components/graveyard";

export default function GraveyardPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <Graveyard />
      </main>
    </>
  );
}

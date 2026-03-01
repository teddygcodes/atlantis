import { Navigation } from "@/components/navigation";
import { Graveyard } from "@/components/graveyard";

export default function GraveyardPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <Graveyard />
      </main>
    </>
  );
}

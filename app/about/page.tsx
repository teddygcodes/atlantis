import { Navigation } from "@/components/navigation";
import { About } from "@/components/about";

export default function AboutPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <About />
      </main>
    </>
  );
}

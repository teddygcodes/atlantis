import { Navigation } from "@/components/navigation";
import { About } from "@/components/about";

export default function AboutPage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <About />
      </main>
    </>
  );
}

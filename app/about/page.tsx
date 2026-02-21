import { Navigation } from "@/components/navigation";
import { About } from "@/components/about";

export default function AboutPage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 py-20 md:py-32">
        <About />
      </main>
    </>
  );
}

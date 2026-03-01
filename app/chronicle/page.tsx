import { Navigation } from "@/components/navigation";
import { Chronicle } from "@/components/chronicle";

export default function ChroniclePage() {
  return (
    <>
      <Navigation />
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <Chronicle />
      </main>
    </>
  );
}

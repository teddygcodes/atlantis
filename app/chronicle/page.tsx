import { Navigation } from "@/components/navigation";
import { Chronicle } from "@/components/chronicle";

export default function ChroniclePage() {
  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-5xl px-6 pt-24 pb-20 md:pt-36">
        <Chronicle />
      </main>
    </>
  );
}

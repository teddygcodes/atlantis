import { Navigation } from "@/components/navigation";
import { Chronicle } from "@/components/chronicle";

export default function ChroniclePage() {
  return (
    <>
      <Navigation />
      <main className="px-4 py-24 md:py-32">
        <Chronicle />
      </main>
    </>
  );
}

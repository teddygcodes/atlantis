import { Navigation } from "@/components/navigation";
import { Chronicle } from "@/components/chronicle";

export default function ChroniclePage() {
  return (
    <>
      <Navigation />
      <main className="px-4 pt-24 pb-20 md:pt-36">
        <Chronicle />
      </main>
    </>
  );
}

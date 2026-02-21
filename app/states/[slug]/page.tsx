import { Navigation } from "@/components/navigation";
import { StateProfile } from "@/components/state-profile";

export default async function StateProfilePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  return (
    <>
      <Navigation />
      <main className="mx-auto max-w-[900px] px-6 pt-24 pb-20 text-center md:pt-32">
        <StateProfile slug={slug} />
      </main>
    </>
  );
}

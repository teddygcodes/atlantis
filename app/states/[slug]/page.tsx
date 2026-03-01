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
      <main className="animate-fade-in-up mx-auto max-w-[960px] px-6 pt-20 pb-20">
        <StateProfile slug={slug} />
      </main>
    </>
  );
}

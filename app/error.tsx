"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#060606] px-6 text-[#e5e5e5]">
      <h2 className="mb-4 text-3xl font-semibold" style={{ color: "#dc2626" }}>
        Something went wrong
      </h2>
      <p className="mb-6 max-w-xl text-center text-sm leading-relaxed text-[#e5e5e5]/80">
        {error.message || "An unexpected error occurred."}
      </p>
      <button
        type="button"
        onClick={() => reset()}
        className="rounded border border-[#dc2626]/60 bg-[#dc2626]/10 px-4 py-2 text-sm font-medium text-[#e5e5e5] transition hover:bg-[#dc2626]/20"
      >
        Try again
      </button>
    </div>
  );
}

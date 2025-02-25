export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="flex items-center justify-between px-6 py-4">
        <h1 className="text-xl font-bold">getdelv</h1>
      </header>

      <main className="flex-1 flex flex-col justify-center gap-6 px-6 sm:px-20">
        <h2 className="text-5xl sm:text-6xl font-bold">
          Coding Docs for Machines
        </h2>
        <p className="max-w-lg text-lg sm:text-xl">
          Delv is a search engine built for LLMs and AI agents, helping them find
          obscure coding documentation that isn&apos;t in their training data.
          Whether it&apos;s API specs or bug reports, delv delivers the answers
          they need.
        </p>

        {/* Responsive YouTube embed */}
        {/* <div className="relative w-full max-w-xl h-0 pb-[56.25%]">
          <iframe
            className="absolute top-0 left-0 w-full h-full"
            src="https://example.invalid"
            title="Demo video"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div> */}
        
        <p className="text-lg sm:text-xl">Coming Soon…</p>
      </main>
    </div>
  );
}

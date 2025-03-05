<template>
  <div class="flex flex-col min-h-screen bg-muted-bg text-primary-text">
    <header class="flex items-center justify-between px-6 py-4 border-b border-border-light bg-header-bg">
      <h1 class="text-xl font-bold tracking-wide text-accent">getdelv 🔎</h1>
    </header>
    
    <main class="flex-1 flex flex-col justify-center gap-8 px-6 sm:px-20 py-12">
      <div class="max-w-3xl">
        <h2 class="text-4xl sm:text-6xl font-bold text-primary-text mb-6">
          Coding Docs for Machines
        </h2>
        <p class="text-lg sm:text-xl text-secondary-text mb-6">
          Delv is a search engine built for LLMs and AI agents, helping them find
          obscure coding documentation that isn't in their training data.
        </p>
      </div>
      
      <div class="flex flex-col sm:flex-row items-start gap-8 mt-8">
        <div class="w-full max-w-2xl aspect-video">
          <iframe 
            class="w-full h-full rounded-lg shadow-md"
            src="https://example.invalid" 
            title="YouTube video player" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
            referrerpolicy="strict-origin-when-cross-origin" 
            allowfullscreen
          ></iframe>
        </div>
      </div>

      <!-- <section class="mt-12 max-w-3xl">
        <h3 class="text-3xl font-semibold text-primary-text mb-4">Latest Insights</h3>
        <article class="bg-content-bg p-6 rounded-lg shadow-sm border border-border-light">
          <h4 class="text-2xl font-medium mb-3">Understanding AI-Driven Search Engines</h4>
          <p class="text-secondary-text">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed efficitur eros at ligula cursus, et aliquet ex tristique...
          </p>
          <ul class="list-disc list-inside mt-3 text-secondary-text">
            <li>How AI indexes obscure coding documentation</li>
            <li>Challenges in LLM-assisted searches</li>
            <li>Why open-source data matters for AI</li>
          </ul>
        </article>
      </section> -->

      <a 
        href="mailto:contact@example.invalid" 
        class="text-lg sm:text-xl text-secondary-text hover:text-accent transition-colors"
      >
        contact@example.invalid
      </a>
    </main>
  </div>
</template>

<script setup>
// Add any logic if needed
</script>
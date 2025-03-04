<template>
  <div class="flex flex-col min-h-screen">
    <header class="flex items-center justify-between px-6 py-4">
      <h1 class="text-xl font-bold">getdelv</h1>
    </header>
    <main class="flex-1 flex flex-col justify-center gap-6 px-6 sm:px-20">
      <h2 class="text-5xl sm:text-6xl font-bold">
        Coding Docs for Machines
      </h2>
      <p class="max-w-lg text-lg sm:text-xl">
        Delv is a search engine built for LLMs and AI agents, helping them find
        obscure coding documentation that isn't in their training data.
      </p>
      <p class="text-lg sm:text-xl">Coming Soon…</p>
      <div class="flex items-center gap-4">
        <a href="mailto:contact@example.invalid" class="text-lg sm:text-xl">
          contact@example.invalid
        </a>
        <!-- Use a router-link wrapped around a button for navigation -->
        <router-link to="/pitch">
          <button class="text-lg sm:text-xl text-blue-600 hover:text-blue-800">
            Pitch
          </button>
        </router-link>
      </div>
    </main>
  </div>
</template>

<script setup>
// Add any logic if needed
</script>
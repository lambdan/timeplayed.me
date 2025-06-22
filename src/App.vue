<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import Footer from "./components/Footer.vue";
</script>

<template>
  <div class="d-flex flex-column min-vh-100">
    <Navbar />
    <main class="flex-grow pt-2 pb-2">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

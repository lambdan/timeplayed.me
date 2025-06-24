<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import Footer from "./components/Footer.vue";
</script>

<template>
  <div class="mb-2">
    <Navbar />
    <main class="">
      <router-view />
    </main>
    <Footer class="mt-2"></Footer>
  </div>
</template>

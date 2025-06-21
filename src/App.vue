<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import Footer from "./components/Footer.vue";
</script>

<template>
  <div>
    <Navbar />
    <main class="container">
      <router-view />
    </main>
    <Footer />
  </div>
</template>

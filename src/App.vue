<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import Footer from "./components/Footer.vue";
import { onMounted, onBeforeUnmount } from "vue";

function setThemeBySystemPreference() {
  const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.setAttribute(
    "data-bs-theme",
    isDark ? "dark" : "light"
  );
}

onMounted(() => {
  setThemeBySystemPreference();
  // Listen for changes in system theme
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = () => setThemeBySystemPreference();
  mq.addEventListener("change", handler);
  onBeforeUnmount(() => {
    mq.removeEventListener("change", handler);
  });
});
</script>

<template>
  <Navbar />
  <main class="">
    <router-view />
  </main>
  <Footer class="mt-2"></Footer>
</template>

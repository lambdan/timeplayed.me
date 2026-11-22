<script setup lang="ts">
import Navbar from "./components/Navbar.vue";
import Footer from "./components/Footer.vue";
import { onMounted, onBeforeUnmount } from "vue";

function setThemeBySystemPreference() {
  // always dark for now
  document.documentElement.setAttribute("data-bs-theme", "dark");
  /*const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.setAttribute(
    "data-bs-theme",
    isDark ? "dark" : "light",
  );*/
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
  <!-- full width navbar, its content lines up with the page container -->
  <Navbar />
  <!-- the one container for every page, pages lay themselves out with row g-4 and cols -->
  <div class="container pb-3">
    <main class="my-4">
      <!-- key: remount when going between pages of the same type, e.g. game to game -->
      <router-view :key="$route.path" />
    </main>
    <Footer></Footer>
  </div>
</template>

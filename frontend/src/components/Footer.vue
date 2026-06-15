<script setup lang="ts">
import { onMounted, ref } from "vue";
import pkg from "../../package.json";
import { TimeplayedAPI } from "../api.client";
const FRONTEND_VERSION = pkg.version;
const BACKEND_VERSION = ref("...");

onMounted(async () => {
  const info = await TimeplayedAPI.info();
  BACKEND_VERSION.value = info.version;
});
</script>

<template>
  <footer class="footer text-center">
    <small class="text-muted">
      <a
        class="text-muted"
        style="text-decoration: none"
        href="https://github.com/lambdan/timeplayed.me"
      >
        <i class="bi bi-github"></i
      ></a>
      frontend {{ FRONTEND_VERSION }} /
      <a style="text-decoration: none" class="text-muted" href="/docs"
        >backend {{ BACKEND_VERSION }}</a
      >
    </small>
  </footer>
</template>

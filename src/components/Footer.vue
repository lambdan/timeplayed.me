<script setup lang="ts">
import pkg from "../../package.json";
const VERSION = pkg.version;
</script>

<template>
  <footer class="footer text-center">
    <small class="text-muted">
      <a
        class="text-muted"
        style="text-decoration: none"
        href="https://github.com/lambdan/timeplayed.me"
      >
        <i class="bi bi-github"></i> {{ VERSION }}
      </a>
    </small>
  </footer>
</template>

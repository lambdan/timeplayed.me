<script setup lang="ts">
import pkg from "../../package.json";
const VERSION = pkg.version;
</script>

<template>
  <footer class="text-center">
    <p>Version: {{ VERSION }}</p>
  </footer>
</template>

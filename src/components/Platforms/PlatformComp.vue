<script setup lang="ts">
import type { Platform } from "../../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";

const props = defineProps<{ platform: Platform }>();

function getIcon() {
  if (props.platform.abbreviation.startsWith("ps")) {
    return "bi-playstation";
  }
  if (props.platform.abbreviation.startsWith("xbox")) {
    return "bi-xbox";
  }
  if (props.platform.abbreviation.includes("switch")) {
    return "bi-nintendo-switch";
  }
  if (props.platform.abbreviation === "pc") {
    return "bi-pc-display";
  }
  if (props.platform.abbreviation === "steamdeck") {
    return "bi-steam";
  }
  if (props.platform.abbreviation === "mac") {
    return "bi-apple";
  }
  // fallback
  return "bi-controller";
}

function displayName() {
  return props.platform.name || props.platform.abbreviation;
}
</script>

<template><i :class="['bi', getIcon()]"> </i>  {{ displayName() }}</template>

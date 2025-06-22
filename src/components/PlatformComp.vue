<script setup lang="ts">
import type { Platform } from "../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";

const props = defineProps<{ platform: Platform }>();

function getIcon() {
  if (props.platform.abbreviation.startsWith("ps")) {
    return "bi-playstation";
  } else if (props.platform.abbreviation.startsWith("xbox")) {
    return "bi-xbox";
  } else if (props.platform.abbreviation.includes("switch")) {
    return "bi-nintendo-switch";
  } else if (props.platform.abbreviation === "pc") {
    return "bi-pc-display";
  } else if (props.platform.abbreviation === "steamdeck") {
    return "bi-steam";
  }
  return "bi-controller";
}

function displayName() {
  return props.platform.name || props.platform.abbreviation;
}
</script>

<template><i :class="['bi', getIcon()]"> </i>  {{ displayName() }}</template>

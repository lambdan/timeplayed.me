<script setup lang="ts">
import type { Platform } from "../../models/models";
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";

const props = withDefaults(
  defineProps<{ platform: Platform; showName?: boolean }>(),
  {
    showName: true,
  }
);

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

function color() {
  if (props.platform.abbreviation.startsWith("ps")) {
    return "bg-primary";
  } else if (props.platform.abbreviation.startsWith("xbox")) {
    return "bg-success";
  } else if (props.platform.abbreviation.includes("switch")) {
    return "bg-nintendo";
  }

  if (props.platform.abbreviation === "steamdeck") {
    return "bg-steamdeck";
  }

  if (props.platform.abbreviation === "pc") {
    return "bg-pcmr";
  }

  return "bg-secondary";
}
</script>

<template>
  <span :class="['badge', color()]">
    <i :class="['bi', getIcon()]"></i>
    <span v-if="showName"
      > 
      {{ displayName() }}
    </span>
  </span>
</template>

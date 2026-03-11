<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";
import type { Platform } from "../../api.models.ts";

const props = withDefaults(
  defineProps<{ platform: Platform; showName?: boolean; emulated?: boolean }>(),
  {
    showName: true,
    emulated: false,
  },
);

function displayName() {
  return props.platform.name || props.platform.abbreviation;
}

function getBackgroundColor() {
  const apiPrimary = props.platform.color_primary;
  if (apiPrimary) {
    return "#" + apiPrimary;
  }
  return "#6c757d"; // bg-secondary
}

function getTextColor() {
  const apiSecondary = props.platform.color_secondary;
  if (apiSecondary) {
    return "#" + apiSecondary;
  }
  return "#ffffff"; // text-white
}

function getIcon() {
  const apiIcon = props.platform.icon;
  if (apiIcon) {
    return "bi-" + apiIcon;
  }
  return "bi-controller";
}
</script>

<template>
  <a :href="'/platform/' + platform.id" class="text-decoration-none">
    <span
      :style="{ backgroundColor: getBackgroundColor(), color: getTextColor() }"
      class="badge"
    >
      <i :class="['bi', getIcon()]"></i>
      <span v-if="showName"
        > 
        {{ displayName() }}
        <sup v-if="emulated">EMU</sup>
      </span>
    </span>
  </a>
</template>

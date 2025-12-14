<script setup lang="ts">
import { defineProps } from "vue";
import "bootstrap-icons/font/bootstrap-icons.css";
import type { Platform } from "../../api.models.ts";

const props = withDefaults(
  defineProps<{ platform: Platform; showName?: boolean }>(),
  {
    showName: true,
  },
);

function getIcon() {
  if (props.platform.abbreviation.startsWith("ps")) {
    return "bi-playstation";
  }
  if (
    props.platform.abbreviation.startsWith("xbox") ||
    props.platform.abbreviation === "x360"
  ) {
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

function color() {
  if (props.platform.abbreviation.startsWith("ps")) {
    /* ps1, ps2, ps3, ps4, ps5 */
    return "bg-primary";
  }

  if (props.platform.abbreviation === "xbox") {
    /* og xbox */
    return "bg-xbox";
  }

  if (
    props.platform.abbreviation.includes("xbox") ||
    props.platform.abbreviation === "x360"
  ) {
    return "bg-success";
  }

  if (props.platform.abbreviation.includes("switch")) {
    return "bg-nintendo";
  }

  if (props.platform.abbreviation === "steamdeck") {
    return "bg-steamdeck";
  }

  if (props.platform.abbreviation === "pc") {
    return "bg-pcmr";
  }

  if (
    props.platform.abbreviation === "mac" ||
    props.platform.abbreviation === "ios"
  ) {
    return "bg-apple";
  }

  if (props.platform.abbreviation === "gba") {
    return "bg-game-boy-advance";
  }

  if (props.platform.abbreviation === "gb") {
    return "bg-game-boy";
  }

  if (props.platform.abbreviation === "n64") {
    return "bg-n64";
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

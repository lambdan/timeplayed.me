<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";
import type { Platform } from "../../api.models.ts";
import {
  platformBackground,
  platformIcon,
  platformTextColor,
} from "../../platformStyle";

const props = withDefaults(
  defineProps<{
    platform: Platform;
    showName?: boolean;
    showAbbreviation?: boolean;
  }>(),
  {
    showName: true,
    showAbbreviation: false,
  },
);

function displayedText() {
  if (props.showAbbreviation) {
    return props.platform.abbreviation.toUpperCase();
  }
  return props.platform.name || props.platform.abbreviation;
}
</script>

<template>
  <a
    :href="'/platform/' + platform.id"
    class="text-decoration-none"
    :title="displayedText()"
  >
    <span
      :style="{
        backgroundColor: platformBackground(platform),
        color: platformTextColor(platform),
      }"
      class="badge"
    >
      <i :class="['bi', platformIcon(platform)]"></i>
      <span v-if="showName || showAbbreviation"
        > 
        {{ displayedText() }}
      </span>
    </span>
  </a>
</template>

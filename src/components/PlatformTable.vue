<script setup lang="ts">
import type { Platform } from "../models/models";
import GameRow from "./GameRow.vue";
import PlatformRow from "./PlatformRow.vue";

const props = withDefaults(
  defineProps<{ platforms: Platform[]; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);
</script>

<template>
  <table class="table table-responsive table-hover">
    <thead>
      <tr>
        <th></th>
        <th>Last played</th>
        <th>Total playtime</th>
        <th>Percentage</th>
      </tr>
    </thead>
    <tbody>
      <PlatformRow
        v-for="platform in platforms"
        :key="platform.id"
        :platform="platform"
        :showExpand="showExpand"
      />
    </tbody>
  </table>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GlobalStats, Platform } from "../models/models";

import { formatDate, formatDuration, timeAgo } from "../utils";
import PlatformComp from "./PlatformComp.vue";

const props = withDefaults(
  defineProps<{
    platform: Platform;
    showExpand?: boolean;
  }>(),
  {
    showExpand: false,
  }
);

const expanded = ref(false);
const totalPlaytime = ref(0);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {
  const res = await fetch(`/api/stats`);
  const data: GlobalStats = await res.json();
  totalPlaytime.value = data.total.seconds;
});

function calculatePercentage(): string {
  if (totalPlaytime.value === 0) return "0%";
  const percentage =
    (props.platform.seconds_played / totalPlaytime.value) * 100;
  return `${percentage.toFixed(1)}%`;
}
</script>

<template>
  <tr class="align-middle">
    <td>
      <PlatformComp :platform="props.platform" />
    </td>

    <td>
      {{ timeAgo(new Date(props.platform.last_played + "Z")) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.platform.last_played + "Z"))
      }}</small>
    </td>

    <td>{{ formatDuration(props.platform.seconds_played) }}</td>

    <td>{{ calculatePercentage() }}</td>

    <td>
      <small v-if="expanded" class="text-muted">
        Platform ID {{ platform.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

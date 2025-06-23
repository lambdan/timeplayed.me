<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { PlatformWithStats } from "../models/models";

import { formatDate, formatDuration, timeAgo } from "../utils";
import PlatformComp from "./PlatformComp.vue";

const props = withDefaults(
  defineProps<{
    platform: PlatformWithStats;
    showExpand?: boolean;
  }>(),
  {
    showExpand: false,
  }
);

const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {});
</script>

<template>
  <tr class="align-middle">
    <td>
      <PlatformComp :platform="props.platform.platform" />
    </td>

    <td>
      {{ timeAgo(new Date(props.platform.last_played)) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.platform.last_played))
      }}</small>
    </td>

    <td>
      {{ formatDuration(props.platform.total_playtime) }}
      <br />
      <small class="text-muted">
        {{ (props.platform.percent * 100).toFixed(1) + "%" }}
      </small>
    </td>

    <td>
      <small v-if="expanded" class="text-muted">
        Platform ID {{ platform.platform.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

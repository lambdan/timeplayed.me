<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { UserWithStats } from "../../models/models";
import DiscordAvatar from "../DiscordAvatar.vue";

import { formatDate, formatDuration, timeAgo } from "../../utils";

const props = withDefaults(
  defineProps<{
    user: UserWithStats;
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
    <td class="col-lg-1">
      <DiscordAvatar :user="props.user.user" />
    </td>

    <td>
      {{ props.user.user.name }}
    </td>

    <td>
      {{ timeAgo(new Date(props.user.last_played)) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.user.last_played))
      }}</small>
    </td>

    <td>
      {{ formatDuration(props.user.total_playtime) }}
      <br />
    </td>

    <td>
      <small v-if="expanded" class="text-muted">
        User ID {{ user.user.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

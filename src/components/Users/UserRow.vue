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
      <a :href="`/user/${props.user.user.id}`">
        {{ props.user.user.name }}
      </a>
    </td>

    <td>
      {{ timeAgo(new Date(props.user.last_played)) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.user.last_played))
      }}</small>
    </td>

    <td>
      <strong> {{ formatDuration(props.user.total_playtime) }}</strong>
    </td>
  </tr>
</template>

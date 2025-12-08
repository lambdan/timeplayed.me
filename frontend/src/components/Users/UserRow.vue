<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { UserWithStats } from "../../models/models";
import DiscordAvatar from "../DiscordAvatar.vue";
import UserColumn from "./UserColumn.vue";
import { formatDate, formatDuration, timeAgo } from "../../utils";
import CalendarBadge from "../Badges/CalendarBadge.vue";
import DurationBadge from "../Badges/DurationBadge.vue";

const props = withDefaults(
  defineProps<{
    user: UserWithStats;
    showExpand?: boolean;
    showLastPlayed?: boolean;
  }>(),
  {
    showExpand: false,
    showLastPlayed: true,
  }
);

const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {});
</script>

<template>
  <div class="row align-items-center mb-2 text-center">
    <UserColumn :user="user.user" class="col-lg-3" />

    <div class="col" v-if="props.showLastPlayed">
      Last played<br /><CalendarBadge
        :date="new Date(props.user.last_played)"
      />
    </div>

    <div class="col">
      Time played<br />
      <DurationBadge :secs="props.user.total_playtime" />
    </div>
  </div>
  <hr />
</template>

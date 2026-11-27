<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import type { Playing } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import { useLookups } from "../composables/useLookups";
import DurationBadge from "./Badges/DurationBadge.vue";
import PlatformBadge from "./Badges/PlatformBadge.vue";
import DiscordAvatar from "./DiscordAvatar.vue";
import CroppedCover from "./Games/CroppedCover.vue";
import GameName from "./Games/GameName.vue";

// rows of who's playing what right now, from manual tracking and Discord. none when nobody is
// all of them for now. if there are ever too many, bring back the limit and the
// show more button (commented out below and in the template)
// const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 5 });

const REFRESH_MS = 30 * 1000;

const lookups = useLookups();
const playing = ref<Playing[]>([]);
// ticks every second, so durations count up
const now = ref(Date.now());
// past the limit only when asked for
// const expanded = ref(false);
// const shown = computed(() =>
//   expanded.value ? playing.value : playing.value.slice(0, props.limit),
// );
const shown = computed(() => playing.value);

async function load() {
  // also called by the table when a session was stored, so it's not in both
  try {
    playing.value = await TimeplayedAPI.getPlaying();
  } catch {
    // keep what's shown, try again next time
  }
}

let refreshTimer: ReturnType<typeof setInterval>;
let tickTimer: ReturnType<typeof setInterval>;
onMounted(() => {
  load();
  refreshTimer = setInterval(load, REFRESH_MS);
  tickTimer = setInterval(() => (now.value = Date.now()), 1000);
});
defineExpose({ load, count: computed(() => shown.value.length) });

onUnmounted(() => {
  clearInterval(refreshTimer);
  clearInterval(tickTimer);
});
</script>

<template>
  <!-- same columns as ActivityRow, so they line up in the recent activity table -->
  <tr v-for="p in shown" :key="`${p.user_id}|${p.game_id}|${p.platform_id}`">
    <td style="width: 50px">
      <DiscordAvatar
        v-if="lookups.user(p.user_id)"
        :user="lookups.user(p.user_id)!"
        :maxWidth="40"
      />
    </td>
    <td class="d-none d-md-table-cell" style="width: 50px">
      <CroppedCover :gameId="p.game_id" thumbnail style="width: 32px" />
    </td>
    <td class="w-100 text-break">
      <a
        :href="`/game/${p.game_id}`"
        class="link-underline link-underline-opacity-0"
        ><GameName
          v-if="lookups.game(p.game_id)"
          :game="lookups.game(p.game_id)!"
      /></a>
    </td>
    <td class="d-none d-md-table-cell" style="width: 1%">
      <PlatformBadge
        v-if="lookups.platform(p.platform_id)"
        :platform="lookups.platform(p.platform_id)!"
        :showName="false"
      />
    </td>
    <td class="text-nowrap px-md-3" style="width: 1%">
      <DurationBadge
        :seconds="Math.max(0, Math.floor((now - p.started) / 1000))"
      />
    </td>
    <td
      class="text-nowrap text-body-secondary"
      style="width: 1%"
      :title="
        p.source === 'discord' ? 'Tracked by Discord' : 'Tracked manually'
      "
    >
      <i
        class="bi me-1"
        :class="p.source === 'discord' ? 'bi-discord' : 'bi-stopwatch'"
      ></i>
      <!-- shorter on phones, like "31 m ago" -->
      <span class="d-none d-md-inline">playing</span> now
    </td>
  </tr>
  <!-- show more button, for when there's a limit
  <tr v-if="playing.length > limit">
    <td colspan="6" class="text-center">
      <button
        class="btn btn-sm btn-link"
        type="button"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <template v-if="expanded">Show fewer</template>
        <template v-else
          >Show {{ playing.length - limit }} more playing now</template
        >
      </button>
    </td>
  </tr>
  -->
</template>

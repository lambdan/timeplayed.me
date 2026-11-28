<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import type { Playing } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { useLookups } from "../../composables/useLookups";
import { useNsfw } from "../../composables/useNsfw";
import { formatDuration } from "../../utils";
import RecapStatTile from "../Recap/RecapStatTile.vue";

// what a user is playing right now, as tiles for the user card. none when nothing
const props = defineProps<{ userId: number }>();

const REFRESH_MS = 30 * 1000;

const lookups = useLookups();
const { gameName } = useNsfw();
const playing = ref<Playing[]>([]);
// ticks every second, so durations count up
const now = ref(Date.now());

async function load() {
  try {
    playing.value = await TimeplayedAPI.getPlaying({ user: props.userId });
  } catch {
    // keep what's shown, try again next time
  }
}

function seconds(p: Playing) {
  return Math.max(0, Math.floor((now.value - p.started) / 1000));
}

let refreshTimer: ReturnType<typeof setInterval>;
let tickTimer: ReturnType<typeof setInterval>;
onMounted(() => {
  load();
  refreshTimer = setInterval(load, REFRESH_MS);
  tickTimer = setInterval(() => (now.value = Date.now()), 1000);
});
onUnmounted(() => {
  clearInterval(refreshTimer);
  clearInterval(tickTimer);
});
</script>

<template>
  <div v-for="p in playing" :key="`${p.game_id}|${p.platform_id}`" class="col">
    <a :href="`/game/${p.game_id}`" class="text-decoration-none">
      <RecapStatTile
        label="Playing now"
        :value="
          lookups.game(p.game_id) ? gameName(lookups.game(p.game_id)!) : '…'
        "
        :small="true"
        background="var(--bs-success)"
        color="#fff"
      >
        {{ lookups.platform(p.platform_id)?.display_name }}
        <span style="font-variant-numeric: tabular-nums">{{
          formatDuration(seconds(p), true)
        }}</span>
      </RecapStatTile>
    </a>
  </div>
</template>

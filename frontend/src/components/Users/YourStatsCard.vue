<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type {
  Game,
  GameWithStats,
  Platform,
  PlatformWithStats,
} from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { useAuthenticatedUser } from "../../composables/useAuthenticatedUser";
import InfoStatTiles from "../Misc/InfoStatTiles.vue";
import { platformBackground, platformTextColor } from "../../platformStyle";
import { tileBackground, tileTextColor } from "../../tileStyle";

// the logged in user's stats for one game or platform. Hidden if they haven't played it
const props = defineProps<{
  game?: Game;
  platform?: Platform;
  /** include child games/platforms, like the rest of the page */
  includeChildren?: boolean;
  /** everyone's playtime on it, for the user's share */
  totalSeconds?: number;
}>();

const { authenticatedUser } = useAuthenticatedUser();
// the game's or platform's colors, like the rest of the page
const background = computed(() => {
  if (props.platform) return platformBackground(props.platform);
  if (props.game) return tileBackground(props.game);
  return undefined;
});
const color = computed(() => {
  if (props.platform) return platformTextColor(props.platform);
  if (props.game) return tileTextColor(props.game);
  return undefined;
});
const gameStats = ref<GameWithStats["stats"]>();
const platformStats = ref<PlatformWithStats["stats"]>();
const stats = computed(() => gameStats.value ?? platformStats.value);
// users is left out, it's always 1
const counts = computed(() => {
  const tiles: { label: string; value: number | string; sub?: string }[] = [];
  if (gameStats.value) {
    tiles.push({ label: "Platforms", value: gameStats.value.platform_count });
  }
  if (platformStats.value) {
    tiles.push({ label: "Games", value: platformStats.value.game_count });
  }
  // private users' playtime isn't part of the total, so their share makes no sense
  const isPrivate = !!authenticatedUser.value?.permissions.includes("private");
  if (stats.value && props.totalSeconds && !isPrivate) {
    const percent = (stats.value.seconds / props.totalSeconds) * 100;
    tiles.push({
      label: "Share",
      value: percent < 1 ? "<1%" : `${Math.round(percent)}%`,
      sub: "of all playtime",
    });
  }
  return tiles;
});

async function load() {
  gameStats.value = undefined;
  platformStats.value = undefined;
  const user = authenticatedUser.value?.id;
  if (!user) {
    return;
  }
  // the list routes return nothing instead of 404 when the user hasn't played it
  if (props.game) {
    const found = await TimeplayedAPI.getGameStatsMany([props.game.id], {
      user,
      include_children: props.includeChildren,
    });
    gameStats.value = found[0]?.stats;
  } else if (props.platform) {
    const found = await TimeplayedAPI.getPlatformStatsMany(
      [props.platform.id],
      { user, include_child_platforms: props.includeChildren },
    );
    platformStats.value = found[0]?.stats;
  }
}

watch(
  () => [
    authenticatedUser.value?.id,
    props.game?.id,
    props.platform?.id,
    props.includeChildren,
  ],
  load,
  { immediate: true },
);
</script>

<template>
  <div v-if="stats">
    <div class="card h-100">
      <h2 class="card-header">Your stats</h2>
      <div class="card-body">
        <InfoStatTiles
          :stats="stats"
          :counts="counts"
          :narrow="true"
          :background="background"
          :color="color"
        />
      </div>
    </div>
  </div>
</template>

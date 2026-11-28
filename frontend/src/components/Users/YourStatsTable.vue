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
import { formatDuration } from "../../utils";
import CalendarBasic from "../CalendarBasic.vue";

// the logged in user's stats for one game or platform, for its info card. Hidden if they haven't played it
const props = defineProps<{
  game?: Game;
  platform?: Platform;
  /** include child games/platforms, marks the numbers as combined */
  includeChildren?: boolean;
}>();

const { authenticatedUser } = useAuthenticatedUser();
const gameStats = ref<GameWithStats["stats"]>();
const platformStats = ref<PlatformWithStats["stats"]>();
const stats = computed(() => gameStats.value ?? platformStats.value);

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
  <template v-if="stats">
    <h3 class="h5 mt-4 mb-2">Your stats</h3>
    <table class="table table-sm table-hover mb-0">
      <tbody>
        <tr>
          <th class="text-nowrap">Playtime</th>
          <td>
            {{ formatDuration(stats.seconds) }}
            <span
              v-if="includeChildren"
              class="text-muted"
              title="Combined total"
              >*</span
            >
          </td>
        </tr>
        <tr>
          <th class="text-nowrap">Activities</th>
          <td>
            {{ stats.activity_count }}
            <span
              v-if="includeChildren"
              class="text-muted"
              title="Combined total"
              >*</span
            >
          </td>
        </tr>
        <tr v-if="gameStats">
          <th class="text-nowrap">Platforms</th>
          <td>
            {{ gameStats.platform_count }}
            <span
              v-if="includeChildren"
              class="text-muted"
              title="Combined total"
              >*</span
            >
          </td>
        </tr>
        <tr v-if="platformStats">
          <th class="text-nowrap">Games</th>
          <td>
            {{ platformStats.game_count }}
            <span
              v-if="includeChildren"
              class="text-muted"
              title="Combined total"
              >*</span
            >
          </td>
        </tr>
        <tr v-if="stats.first_activity">
          <th class="text-nowrap">First played</th>
          <td>
            <CalendarBasic
              :date="stats.first_activity!"
              :showIcon="false"
              :absolute="true"
            />
          </td>
        </tr>
        <tr v-if="stats.last_activity">
          <th class="text-nowrap">Last played</th>
          <td>
            <CalendarBasic
              :date="stats.last_activity!"
              :showIcon="false"
              :absolute="true"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </template>
</template>

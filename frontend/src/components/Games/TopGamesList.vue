<script setup lang="ts">
import { ref, watch } from "vue";
import type { GameWithStats, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import CroppedCover from "./CroppedCover.vue";

// compact ranked list of the most played games in a date range, one section of the "most played" cards
const props = withDefaults(
  defineProps<{
    platform?: Platform;
    user?: User;
    after?: Date;
    before?: Date;
    limit?: number;
  }>(),
  { limit: 10 },
);

const games = ref<GameWithStats[]>([]);
const loading = ref(true);
let latest = 0;

watch(
  () => [props.platform, props.user, props.after, props.before],
  async () => {
    const request = ++latest;
    loading.value = true;
    const data = await TimeplayedAPI.getGamesStats({
      platform: props.platform?.id,
      user: props.user?.id,
      after: props.after?.getTime(),
      before: props.before?.getTime(),
      limit: props.limit,
      sort: "playtime",
      order: "desc",
    });
    if (request !== latest) return; // a newer range was picked meanwhile
    games.value = data;
    loading.value = false;
  },
  { immediate: true },
);
</script>

<template>
  <div>
    <h3 class="h5 mb-2">Games</h3>
    <div v-if="loading" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </div>
    <p v-else-if="!games.length" class="text-body-secondary text-center mb-0">
      Nothing played
    </p>
    <table v-else class="table table-sm table-hover align-middle mb-0">
      <tbody>
        <tr v-for="(game, i) in games" :key="game.id">
          <td class="text-body-secondary" style="width: 1%">{{ i + 1 }}</td>
          <td style="width: 40px">
            <CroppedCover :gameId="game.id" :thumb="true" style="width: 28px" />
          </td>
          <td class="text-break">
            <a
              :href="`/game/${game.id}`"
              class="link-underline link-underline-opacity-0"
              >{{ game.name }}</a
            >
          </td>
          <td class="text-end text-nowrap">
            {{ formatDuration(game.stats.seconds) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

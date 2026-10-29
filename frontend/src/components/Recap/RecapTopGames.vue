<script setup lang="ts">
import { computed, ref } from "vue";
import { formatDuration } from "../../utils";
import { shortDate, type RecapGame } from "../../utils.recap";
import RecapCover from "./RecapCover.vue";

const props = defineProps<{ games: RecapGame[]; showNew: boolean }>();

const podium = computed(() => props.games.slice(0, 4));
const rest = computed(() => props.games.slice(4, 10));
const showAll = ref(false);

function average(game: RecapGame): string {
  return formatDuration(game.seconds / game.sessions);
}
</script>

<template>
  <!-- #1-#4 -->
  <div class="row row-cols-2 row-cols-lg-4 g-3">
    <div v-for="(game, i) in podium" :key="game.game_id">
      <div
        class="border rounded bg-body-tertiary p-3 h-100"
        :class="{ 'border-warning': i === 0 }"
      >
        <RecapCover :gameId="game.game_id" />
        <div class="small fw-semibold text-body-secondary mt-2">
          #{{ i + 1 }}
        </div>
        <a
          :href="`/game/${game.game_id}`"
          class="fw-bold link-body-emphasis text-decoration-none"
          >{{ game.name }}</a
        >
        <div class="fs-4 fw-bold mt-1">
          {{ formatDuration(game.seconds) }}
        </div>
        <div class="small text-body-secondary">
          {{ game.percentage.toFixed(0) }}% of playtime ·
          {{ game.sessions }} activities · {{ average(game) }} avg
        </div>
      </div>
    </div>
  </div>

  <!-- #5-#10 -->
  <div class="row row-cols-3 row-cols-md-6 g-3 mt-0" v-if="rest.length">
    <div v-for="(game, i) in rest" :key="game.game_id">
      <RecapCover :gameId="game.game_id" :thumb="true" />
      <div class="small mt-1 text-truncate">
        <span class="text-body-secondary me-1">#{{ i + 5 }}</span>
        <a
          :href="`/game/${game.game_id}`"
          class="link-body-emphasis text-decoration-none"
          :title="game.name"
          >{{ game.name }}</a
        >
      </div>
      <div class="small text-body-secondary">
        {{ formatDuration(game.seconds) }} · {{ game.sessions }} activities
      </div>
    </div>
  </div>

  <!-- everything -->
  <div class="text-center mt-3" v-if="games.length > 10">
    <button
      class="btn btn-outline-secondary btn-sm"
      @click="showAll = !showAll"
    >
      {{ showAll ? "Hide" : `Show all ${games.length} games` }}
    </button>
  </div>
  <div v-if="showAll" class="table-responsive mt-3">
    <table class="table table-sm table-hover align-middle">
      <thead>
        <tr>
          <th>#</th>
          <th>Game</th>
          <th class="text-end">Played</th>
          <th class="text-end d-none d-sm-table-cell">Activities</th>
          <th class="text-end d-none d-md-table-cell">Avg length</th>
          <th class="text-end d-none d-lg-table-cell">Days</th>
          <th class="text-end d-none d-lg-table-cell">Weeks</th>
          <th class="text-end d-none d-lg-table-cell">First played</th>
          <th class="text-end d-none d-lg-table-cell">Last played</th>
          <th class="text-end d-none d-md-table-cell">Share</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(game, i) in games" :key="game.game_id">
          <td class="text-body-secondary">{{ i + 1 }}</td>
          <td>
            <a
              :href="`/game/${game.game_id}`"
              class="link-underline link-underline-opacity-0"
              >{{ game.name }}</a
            >
            <span
              v-if="showNew && game.new"
              class="badge text-bg-secondary ms-2"
              title="First time playing this game"
              >New</span
            >
          </td>
          <td class="text-end text-nowrap">
            {{ formatDuration(game.seconds) }}
          </td>
          <td class="text-end d-none d-sm-table-cell">{{ game.sessions }}</td>
          <td class="text-end d-none d-md-table-cell">{{ average(game) }}</td>
          <td class="text-end d-none d-lg-table-cell">
            {{ game.days_played }}
          </td>
          <td class="text-end d-none d-lg-table-cell">
            {{ game.weeks_played }}
          </td>
          <td class="text-end text-nowrap d-none d-lg-table-cell">
            {{ shortDate(game.first_played) }}
          </td>
          <td class="text-end text-nowrap d-none d-lg-table-cell">
            {{ shortDate(game.last_played) }}
          </td>
          <td class="text-end d-none d-md-table-cell">
            {{ game.percentage.toFixed(1) }}%
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { formatDuration } from "../utils";
import GameCover from "./Games/GameCover.vue";
import GameName from "./Games/GameName.vue";
import AdminEditLink from "./Misc/AdminEditLink.vue";
import type { Game, GameWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "./CalendarBasic.vue";

const props = defineProps<{
  game: GameWithStats;
  /** stats including all child games, only for games with children */
  familyStats?: GameWithStats["stats"];
}>();
const parent = ref<Game>();

// games with children show the combined numbers
const withChildren = computed(() => props.familyStats !== undefined);
const stats = computed(() => props.familyStats ?? props.game.stats);

onMounted(async () => {
  if (props.game.parent_id) {
    parent.value = await TimeplayedAPI.getGame(props.game.parent_id);
  }
});
</script>

<template>
  <div class="card">
    <h1 class="card-header d-flex align-items-center gap-2">
      <div class="me-auto">
        <GameName :game="game" />
        <span class="text-muted" v-if="game.release_year">
          ({{ game.release_year }})
        </span>
        <span class="text-muted d-block" style="font-size: 0.5em" v-if="parent">
          Counted in
          <a :href="'/game/' + parent.id"><GameName :game="parent" /></a>
        </span>
      </div>
      <AdminEditLink tab="games" :id="game.id" />
    </h1>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-12 col-sm-auto text-center">
          <GameCover
            :gameId="game.id"
            :clickable="false"
            :maxHeight="300"
            :showCredits="true"
          />
        </div>
        <div class="col">
          <table class="table table-sm table-hover mb-0">
            <tbody>
              <tr>
                <th class="text-nowrap">Playtime</th>
                <td>
                  {{ formatDuration(stats.seconds) }}
                  <span
                    v-if="withChildren"
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
                    v-if="withChildren"
                    class="text-muted"
                    title="Combined total"
                    >*</span
                  >
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Users</th>
                <td>
                  {{ stats.user_count }}
                  <span
                    v-if="withChildren"
                    class="text-muted"
                    title="Combined total"
                    >*</span
                  >
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Platforms</th>
                <td>
                  {{ stats.platform_count }}
                  <span
                    v-if="withChildren"
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
                    :date="stats.first_activity"
                    :showIcon="false"
                    :absolute="true"
                  />
                </td>
              </tr>
              <tr v-if="stats.last_activity">
                <th class="text-nowrap">Last played</th>
                <td>
                  <CalendarBasic
                    :date="stats.last_activity"
                    :showIcon="false"
                    :absolute="true"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDuration } from "../utils";
import GameCover from "./Games/GameCover.vue";
import type { GameWithStats } from "../api.models";
import ChildGameBadge from "./Badges/ChildGameBadge.vue";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "./CalendarBasic.vue";

const props = defineProps<{ game: GameWithStats }>();

const gameWithStats = ref<GameWithStats>(props.game);
const parent = ref<GameWithStats>();
const childrenStats = ref<GameWithStats[]>([]);

const loadingStats = ref(true);

function secondsInclChildren() {
  let total = gameWithStats.value.stats.seconds;
  for (const child of childrenStats.value) {
    total += child.stats.seconds;
  }
  return total;
}

function activityCountInclChildren() {
  let total = gameWithStats.value.stats.activity_count;
  for (const child of childrenStats.value) {
    total += child.stats.activity_count;
  }
  return total;
}

onMounted(async () => {
  // fetch children and parent
  const ids = [...props.game.children_ids];
  if (props.game.parent_id) {
    ids.push(props.game.parent_id);
  }

  if (ids.length > 0) {
    const fetched = await TimeplayedAPI.getGameStatsMany(ids);

    if (!gameWithStats.value) {
      throw new Error("Stats not found for game " + props.game.id);
    }
    parent.value = fetched.find((g) => g.id === props.game.parent_id);

    for (const child_id of gameWithStats.value.children_ids) {
      const childStats = fetched.find((g) => g.id === child_id);
      if (childStats) {
        childrenStats.value.push(childStats);
      }
    }
    // sort children by name
    childrenStats.value.sort((a, b) => a.name.localeCompare(b.name));
  }

  loadingStats.value = false;
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">
      {{ game.name }}
      <span class="text-muted" v-if="game.release_year">
        ({{ game.release_year }})
      </span>
      <span class="text-muted d-block" style="font-size: 0.5em" v-if="parent">
        Child of
        <a :href="'/game/' + parent.id">{{ parent.name }}</a>
      </span>
    </h1>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-12 col-sm-auto text-center">
          <GameCover
            :gameId="game.id"
            :thumb="false"
            :clickable="false"
            :maxHeight="300"
          />
        </div>
        <div class="col">
          <table v-if="gameWithStats" class="table table-sm table-hover mb-0">
            <tbody>
              <tr v-if="game.children_ids.length > 0">
                <th class="text-nowrap">Children</th>
                <td>
                  <ChildGameBadge
                    v-for="child in childrenStats"
                    :key="child.id"
                    :game="child"
                  ></ChildGameBadge>
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Playtime</th>
                <td>
                  {{ formatDuration(gameWithStats.stats.seconds) }}
                  <span
                    v-if="game.children_ids.length > 0"
                    class="text-muted"
                    title="(incl children)"
                  >
                    ({{ formatDuration(secondsInclChildren()) }})
                  </span>
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Activities</th>
                <td>
                  {{ gameWithStats.stats.activity_count }}
                  <span
                    v-if="game.children_ids.length > 0"
                    class="text-muted"
                    title="(incl children)"
                  >
                    ({{ activityCountInclChildren() }})
                  </span>
                </td>
              </tr>
              <tr>
                <th class="text-nowrap">Users</th>
                <td>{{ gameWithStats.stats.user_count }}</td>
              </tr>
              <tr>
                <th class="text-nowrap">Platforms</th>
                <td>{{ gameWithStats.stats.platform_count }}</td>
              </tr>
              <tr v-if="gameWithStats.stats.first_activity">
                <th class="text-nowrap">First played</th>
                <td>
                  <CalendarBasic
                    :date="gameWithStats.stats.first_activity"
                    :showIcon="false"
                    :absolute="true"
                  />
                </td>
              </tr>
              <tr v-if="gameWithStats.stats.last_activity">
                <th class="text-nowrap">Last played</th>
                <td>
                  <CalendarBasic
                    :date="gameWithStats.stats.last_activity"
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

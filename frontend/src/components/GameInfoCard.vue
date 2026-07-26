<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDate, formatDuration, sleep, timeAgo } from "../utils";
import GameCover from "./Games/GameCover.vue";
import PlatformTable from "./Platforms/PlatformTable.vue";
import type { Game, GameWithStats, IGDBGameInfo } from "../api.models";
import ChildGameBadge from "./Badges/ChildGameBadge.vue";
import { TimeplayedAPI } from "../api.client";
import CalendarBasic from "./CalendarBasic.vue";

const props = defineProps<{ game: GameWithStats }>();

const gameWithStats = ref<GameWithStats>(props.game);
const parent = ref<GameWithStats>();
const childrenStats = ref<GameWithStats[]>([]);
const igdbInfo = ref<IGDBGameInfo>();

const loadingStats = ref(true);

// Collapse state for each column
const showStats = ref(true);
const showMetadata = ref(false);
const showPlatforms = ref(false);

function toggleColumn(column: "stats" | "metadata" | "platforms") {
  showStats.value = column === "stats";
  showMetadata.value = column === "metadata";
  showPlatforms.value = column === "platforms";
}

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

const similarGames = ref<Game[]>([]);
const expansions = ref<Game[]>([]);
const expandedGames = ref<Game[]>([]);
const igdbParent = ref<Game>();

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

  if (props.game.igdb_id) {
    // have to do this stupid thing because IGDB uses slugs, instead of ID for their URLs...
    // extra stupid because game cover will do the same API call also
    const _igdbInfo = await TimeplayedAPI.getIGDBGameInfo(props.game.igdb_id);
    if (_igdbInfo) {
      igdbInfo.value = _igdbInfo;

      if (_igdbInfo.parent_game) {
        igdbParent.value = await TimeplayedAPI.getGameByIGDB(
          _igdbInfo.parent_game,
        );
      }

      for (const similar_id of _igdbInfo.similar_games) {
        const similarGame = await TimeplayedAPI.getGameByIGDB(similar_id);
        if (similarGame) {
          similarGames.value.push(similarGame);
        }
      }

      for (const expansion_id of _igdbInfo.expansions) {
        const expansionGame = await TimeplayedAPI.getGameByIGDB(expansion_id);
        if (expansionGame) {
          expansions.value.push(expansionGame);
        }
      }

      for (const expanded_id of _igdbInfo.expanded_games) {
        const expandedGame = await TimeplayedAPI.getGameByIGDB(expanded_id);
        if (expandedGame) {
          expandedGames.value.push(expandedGame);
        }
      }
    }
  }
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
      <div class="row">
        <div
          class="col-12 col-lg-auto d-flex flex-column align-items-center justify-content-center mb-3 mb-lg-0"
        >
          <div
            class="card p-0 h-100 border-0 bg-transparent"
            style="box-shadow: none"
          >
            <GameCover
              :gameId="game.id"
              :thumb="false"
              :clickable="false"
              style="
                width: auto;
                max-width: 100%;
                min-width: 0;
                object-fit: cover;
                display: block;
                max-width: 600px;
                max-height: 900px;
              "
            ></GameCover>
          </div>
        </div>

        <div class="col mb-3 mb-lg-0">
          <div class="mb-3 d-flex justify-content-center gap-2">
            <button
              class="btn btn-outline-primary"
              :class="{ active: showStats }"
              @click="toggleColumn('stats')"
            >
              Stats
            </button>
            <button
              class="btn btn-outline-primary"
              :class="{ active: showMetadata }"
              @click="toggleColumn('metadata')"
            >
              Metadata
            </button>
            <button
              class="btn btn-outline-primary"
              :class="{ active: showPlatforms }"
              @click="toggleColumn('platforms')"
            >
              Platforms
            </button>
          </div>
          <div v-if="showStats">
            <div class="card p-0 h-100">
              <h2 class="card-header">Stats</h2>
              <div class="card-body" v-if="gameWithStats">
                <table class="table table-responsive table-hover">
                  <tbody>
                    <tr v-if="game.children_ids.length > 0">
                      <td><b>Children:</b></td>
                      <td>
                        <ChildGameBadge
                          v-for="child in childrenStats"
                          :key="child.id"
                          :game="child"
                        ></ChildGameBadge>
                      </td>
                    </tr>
                    <tr>
                      <td><b>Playtime:</b></td>
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
                      <td><b>Activity count:</b></td>
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
                      <td><b>User count:</b></td>
                      <td>
                        {{ gameWithStats.stats.user_count }}
                      </td>
                    </tr>
                    <tr>
                      <td><b>Platform count:</b></td>
                      <td>
                        {{ gameWithStats.stats.platform_count }}
                      </td>
                    </tr>
                    <tr v-if="gameWithStats.stats.first_activity">
                      <td><b>First played:</b></td>
                      <td>
                        <CalendarBasic
                          :date="gameWithStats.stats.first_activity"
                          :showIcon="false"
                          :absolute="true"
                        />
                      </td>
                    </tr>
                    <tr v-if="gameWithStats.stats.last_activity">
                      <td><b>Last played:</b></td>
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
              <div v-else class="text-center">
                <span
                  class="spinner-border spinner-border mt-4"
                  role="status"
                  aria-hidden="true"
                ></span>
              </div>
            </div>
          </div>
          <div v-if="showMetadata">
            <div class="card p-0 h-100">
              <h2 class="card-header">Metadata</h2>
              <div class="card-body">
                <table class="table table-responsive table-hover">
                  <tbody>
                    <tr>
                      <td><b>ID:</b></td>
                      <td>
                        {{ game.id }}
                      </td>
                    </tr>
                    <tr v-if="game.igdb_id">
                      <td><b>IGDB ID:</b></td>
                      <td v-if="!igdbInfo">
                        {{ game.igdb_id }}
                        <i class="fa-solid fa-spinner fa-spin"></i>
                      </td>
                      <td v-else>
                        <a :href="igdbInfo.url">{{ game.igdb_id }}</a>

                        <div class="card mt-2 p-0 h-100">
                          <div class="card-body">
                            <div v-if="igdbInfo.summary">
                              <h4>Summary</h4>
                              <p>{{ igdbInfo.summary }}</p>
                            </div>

                            <div v-if="igdbParent">
                              <h4>Parent Game</h4>
                              <p>
                                <a :href="'/game/' + igdbParent.id">{{
                                  igdbParent.name
                                }}</a>
                              </p>
                            </div>

                            <div v-if="similarGames.length > 0">
                              <h4>Similar Games</h4>

                              <ul>
                                <li
                                  v-for="similar in similarGames.sort((a, b) =>
                                    a.name.localeCompare(b.name),
                                  )"
                                  :key="similar.id"
                                >
                                  <a :href="'/game/' + similar.id">{{
                                    similar.name
                                  }}</a>
                                </li>
                              </ul>
                            </div>

                            <div v-if="expansions.length > 0">
                              <h4>Expansions</h4>

                              <ul>
                                <li
                                  v-for="similar in expansions.sort((a, b) =>
                                    a.name.localeCompare(b.name),
                                  )"
                                  :key="similar.id"
                                >
                                  <a :href="'/game/' + similar.id">{{
                                    similar.name
                                  }}</a>
                                </li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                    <tr v-if="game.sgdb_id && game.sgdb_grid_id">
                      <td><b>SteamGridDB Game ID/Grid ID:</b></td>
                      <td>
                        <a
                          :href="
                            'https://www.steamgriddb.com/game/' + game.sgdb_id
                          "
                          >{{ game.sgdb_id }}</a
                        >
                        /
                        <a
                          :href="
                            'https://www.steamgriddb.com/grid/' +
                            game.sgdb_grid_id
                          "
                          >{{ game.sgdb_grid_id }}</a
                        >
                      </td>
                    </tr>
                    <tr v-else-if="game.sgdb_id">
                      <td><b>SteamGridDB Game ID:</b></td>
                      <td>
                        <a
                          :href="
                            'https://www.steamgriddb.com/game/' + game.sgdb_id
                          "
                          >{{ game.sgdb_id }}</a
                        >
                      </td>
                    </tr>

                    <tr v-if="game.aliases.length > 0">
                      <td><b>Aliases:</b></td>
                      <td>
                        <ul>
                          <li v-for="alias in game.aliases" :key="alias">
                            {{ alias }}
                          </li>
                        </ul>
                      </td>
                    </tr>

                    <tr>
                      <td><b>Created:</b></td>
                      <td>
                        <CalendarBasic
                          :date="game.created"
                          :showIcon="false"
                          :absolute="true"
                        />
                      </td>
                    </tr>
                    <tr>
                      <td><b>Updated:</b></td>
                      <td>
                        <CalendarBasic
                          :date="game.updated"
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
          <div v-if="showPlatforms">
            <div class="card p-0 h-100">
              <h2 class="card-header">Platforms</h2>
              <div class="card-body">
                <PlatformTable
                  :game="game"
                  :sort="'playtime'"
                  :order="'desc'"
                  :showLastPlayed="false"
                  :showDateRange="true"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

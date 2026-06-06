<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDate, formatDuration, sleep, timeAgo } from "../utils";
import GameCover from "./Games/GameCover.vue";
import PlatformTable from "./Platforms/PlatformTable.vue";
import type { Game, GameWithStats } from "../api.models";
import ChildGameBadge from "./Badges/ChildGameBadge.vue";
import { fetchOrGetCachedGameName } from "../utils.api";

const props = defineProps<{ game: Game }>();

const stats = ref<GameWithStats>();
const loadingStats = ref(true);

const parentGameName = ref("...");

// Collapse state for each column
const showStats = ref(true);
const showMetadata = ref(false);
const showPlatforms = ref(false);

function toggleColumn(column: "stats" | "metadata" | "platforms") {
  showStats.value = column === "stats";
  showMetadata.value = column === "metadata";
  showPlatforms.value = column === "platforms";
}

onMounted(async () => {
  const res = await fetch(`/api/game/${props.game.id}`);
  const data = (await res.json()) as GameWithStats;
  stats.value = data;
  loadingStats.value = false;

  if (props.game.parent_id) {
    parentGameName.value = await fetchOrGetCachedGameName(props.game.parent_id);
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
      <span
        class="text-muted d-block"
        style="font-size: 0.5em"
        v-if="game.parent_id"
      >
        Child of
        <a :href="'/game/' + game.parent_id">{{ parentGameName }}</a>
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
              <div class="card-body" v-if="stats">
                <table class="table table-responsive table-hover">
                  <tbody>
                    <tr v-if="game.children.length > 0">
                      <td><b>Children:</b></td>
                      <td>
                        <ChildGameBadge
                          v-for="child in game.children"
                          :key="child"
                          :gameId="child"
                        ></ChildGameBadge>
                      </td>
                    </tr>
                    <tr>
                      <td><b>Playtime:</b></td>
                      <td>
                        {{ formatDuration(stats.totals.playtime_secs) }}
                        <span
                          v-if="game.children.length > 0"
                          class="text-muted"
                          title="(excluding children)"
                        >
                          ({{
                            formatDuration(
                              stats.totals_excl_children.playtime_secs,
                            )
                          }})
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><b>Activity count:</b></td>
                      <td>
                        {{ stats.totals.activity_count }}

                        <span
                          v-if="game.children.length > 0"
                          class="text-muted"
                          title="(excluding children)"
                        >
                          ({{ stats.totals_excl_children.activity_count }})
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><b>User count:</b></td>
                      <td>
                        {{ stats.totals.user_count }}

                        <span
                          v-if="game.children.length > 0"
                          class="text-muted"
                          title="(excluding children)"
                        >
                          ({{ stats.totals_excl_children.user_count }})
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td><b>Platform count:</b></td>
                      <td>
                        {{ stats.totals.platform_count }}

                        <span
                          v-if="game.children.length > 0"
                          class="text-muted"
                          title="(excluding children)"
                        >
                          ({{ stats.totals_excl_children.platform_count }})
                        </span>
                      </td>
                    </tr>
                    <tr v-if="stats.oldest_activity">
                      <td><b>First played:</b></td>
                      <td>
                        <a :href="'/activity/' + stats.oldest_activity.id">
                          {{
                            stats.oldest_activity
                              ? formatDate(stats.oldest_activity.timestamp)
                              : "-"
                          }}</a
                        >
                        <br />
                        <small class="text-muted">
                          {{
                            stats.oldest_activity
                              ? timeAgo(stats.oldest_activity.timestamp)
                              : "-"
                          }}
                        </small>
                      </td>
                    </tr>
                    <tr v-if="stats.newest_activity">
                      <td><b>Last played:</b></td>
                      <td>
                        <a :href="'/activity/' + stats.newest_activity.id">
                          {{
                            stats.newest_activity
                              ? formatDate(stats.newest_activity.timestamp)
                              : "-"
                          }}</a
                        >
                        <br />
                        <small class="text-muted">
                          {{
                            stats.newest_activity
                              ? timeAgo(stats.newest_activity.timestamp)
                              : "-"
                          }}
                        </small>
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
                      <td><b>Internal ID:</b></td>
                      <td>
                        <code>{{ game.id }}</code>
                      </td>
                    </tr>
                    <!-- <tr>
                      <td><b>Year:</b></td>
                      <td>
                        <code>{{ game.release_year || "-" }}</code>
                      </td>
                    </tr> -->
                    <tr>
                      <td><b>Steam ID:</b></td>
                      <td>
                        <code>{{ game.steam_id }}</code>
                      </td>
                    </tr>
                    <tr>
                      <td><b>SteamGridDB ID:</b></td>
                      <td>
                        <code>{{ game.sgdb_id }}</code>
                      </td>
                    </tr>
                    <tr>
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
                        <code>{{ formatDate(game.created) }}</code>
                      </td>
                    </tr>
                    <tr>
                      <td><b>Updated:</b></td>
                      <td>
                        <code>{{ formatDate(game.updated) }}</code>
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

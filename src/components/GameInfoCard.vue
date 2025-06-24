<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, GameStats } from "../models/models";
import { formatDate, timeAgo, formatDuration, sleep } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import GameCover from "./Games/GameCover.vue";

const props = defineProps<{ game: Game }>();

const stats = ref<GameStats>();
const loadingStats = ref(true);

onMounted(async () => {
  const res = await fetch(`/api/games/${props.game.id}/stats`);
  await sleep(1000);
  const data = (await res.json()) as GameStats;
  stats.value = data;
  loadingStats.value = false;
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">{{ game.name }}</h1>
    <div class="card-body">
      <div class="row p-0 row-cols-1 row-cols-lg-3 g-2">
        <div class="col">
          <div class="card p-0 h-100">
            <GameCover :game="game" :thumb="false"></GameCover>
          </div>
        </div>

        <div class="col">
          <div class="card p-0 h-100">
            <h2 class="card-header">Stats</h2>
            <div class="card-body" v-if="!loadingStats">
              <table class="table table-responsive table-hover">
                <tr>
                  <td><b>Playtime:</b></td>
                  <td>
                    {{
                      stats?.total_playtime !== undefined
                        ? formatDuration(stats.total_playtime)
                        : "-"
                    }}
                  </td>
                </tr>
                <tr>
                  <td><b>Activity count:</b></td>
                  <td>{{ stats?.activity_count ?? "-" }}</td>
                </tr>
                <tr>
                  <td><b>Player count:</b></td>
                  <td>{{ stats?.player_count ?? "-" }}</td>
                </tr>
                <tr>
                  <td><b>Platform count:</b></td>
                  <td>{{ stats?.platform_count ?? "-" }}</td>
                </tr>
                <tr>
                  <td><b>First played:</b></td>
                  <td>
                    {{
                      stats?.oldest_activity?.timestamp
                        ? formatDate(stats.oldest_activity.timestamp)
                        : "-"
                    }}
                  </td>
                </tr>
                <tr>
                  <td><b>Last played:</b></td>
                  <td>
                    {{
                      stats?.newest_activity?.timestamp
                        ? formatDate(stats.newest_activity.timestamp)
                        : "-"
                    }}
                  </td>
                </tr>
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

        <div class="col">
          <div class="card p-0 h-100">
            <h2 class="card-header">Metadata</h2>
            <div class="card-body">
              <table class="table table-responsive table-hover">
                <tr>
                  <td><b>Internal ID:</b></td>
                  <td>
                    <code>{{ game.id }}</code>
                  </td>
                </tr>
                <tr>
                  <td><b>Year:</b></td>
                  <td>
                    <code>{{ game.release_year || "-" }}</code>
                  </td>
                </tr>
                <tr>
                  <td><b>Steam ID:</b></td>
                  <td>
                    <code>{{ game.steam_id || "-" }}</code>
                  </td>
                </tr>
                <tr>
                  <td><b>SteamGridDB ID:</b></td>
                  <td>
                    <code>{{ game.sgdb_id || "-" }}</code>
                  </td>
                </tr>
                <tr>
                  <td><b>Aliases:</b></td>
                  <td>
                    <code>{{
                      game.aliases.length > 0 ? game.aliases.join(",") : "-"
                    }}</code>
                  </td>
                </tr>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

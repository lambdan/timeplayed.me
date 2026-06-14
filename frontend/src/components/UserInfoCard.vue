<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDate, timeAgo, formatDuration } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import type { UserWithStats } from "../api.models";

const props = defineProps<{ user: UserWithStats }>();
const _userWithStats = ref<UserWithStats>(props.user);

onMounted(async () => {});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">{{ user.name }}</h1>
    <div class="card-body">
      <div class="row">
        <div class="col mb-4">
          <DiscordAvatar :user="user" :maxWidth="300"></DiscordAvatar>
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>First played:</b></td>
                <td
                  v-if="_userWithStats && _userWithStats.stats.first_activity"
                >
                  {{
                    formatDate(new Date(_userWithStats.stats.first_activity))
                  }}
                </td>
              </tr>
              <tr>
                <td><b>Last played:</b></td>
                <td v-if="_userWithStats && _userWithStats.stats.last_activity">
                  {{ formatDate(new Date(_userWithStats.stats.last_activity)) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>Games played:</b></td>
                <td>{{ _userWithStats.stats.game_count }}</td>
              </tr>
              <tr>
                <td><b>Platforms played on:</b></td>
                <td>{{ _userWithStats.stats.platform_count }}</td>
              </tr>
              <tr>
                <td><b>Total playtime:</b></td>
                <td>{{ formatDuration(_userWithStats.stats.seconds) }}</td>
              </tr>
              <tr>
                <td><b>Activity count:</b></td>
                <td>{{ _userWithStats.stats.activity_count }}</td>
              </tr>
              <!--
              <tr>
                <td><b>Average playtime/game:</b></td>
                <td>{{ formatDuration(stats?.average.seconds_per_game) }}</td>
              </tr>
              <tr>
                <td><b>Average sessions/game:</b></td>
                <td>{{ stats?.average.sessions_per_game.toFixed(0) }}</td>
              </tr>
              <tr>
                <td><b>Average session length:</b></td>
                <td>{{ formatDuration(stats?.average.session_length) }}</td>
              </tr>
              -->
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

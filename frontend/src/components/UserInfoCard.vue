<script setup lang="ts">
import { onMounted, ref } from "vue";
import { formatDate, timeAgo, formatDuration } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";
import type { User, UserWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const props = defineProps<{ user: User }>();

const stats = ref<UserWithStats>();
const loadingStats = ref(true);

onMounted(async () => {
  stats.value = await TimeplayedAPI.getUser(props.user.id);
  loadingStats.value = false;
});
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
                <td><b>First session:</b></td>
                <td v-if="stats">
                  {{ formatDate(new Date(stats?.oldest_activity.timestamp)) }}
                  <br />
                  <small class="text-muted">
                    {{ timeAgo(new Date(stats?.oldest_activity.timestamp)) }}
                  </small>
                </td>
              </tr>
              <tr>
                <td><b>Last session:</b></td>
                <td v-if="stats">
                  {{ formatDate(new Date(stats?.newest_activity.timestamp)) }}
                  <br />
                  <small class="text-muted">
                    {{ timeAgo(new Date(stats?.newest_activity.timestamp)) }}
                  </small>
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
                <td>{{ stats?.totals.game_count }}</td>
              </tr>
              <tr>
                <td><b>Platforms played on:</b></td>
                <td>{{ stats?.totals.platform_count }}</td>
              </tr>
              <tr>
                <td><b>Total playtime:</b></td>
                <td>{{ formatDuration(stats?.totals.playtime_secs) }}</td>
              </tr>
              <tr>
                <td><b>Total sessions:</b></td>
                <td>{{ stats?.totals.activity_count }}</td>
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

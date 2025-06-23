<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { User, UserStats } from "../models/models";
import { formatDate, timeAgo, formatDuration } from "../utils";
import DiscordAvatar from "./DiscordAvatar.vue";

const props = defineProps<{ user: User }>();

const stats = ref<UserStats>();
const loadingStats = ref(true);

onMounted(async () => {
  const res = await fetch(`/api/users/${props.user.id}/stats`);
  const data: UserStats = await res.json();
  stats.value = data;
  loadingStats.value = false;
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">{{ user.name }}</h1>
    <div class="card-body">
      <div class="row">
        <div class="col-lg-2 mb-4">
          <DiscordAvatar :user="user"></DiscordAvatar>
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
              <tr>
                <td><b>Active days:</b></td>
                <td>{{ stats?.active_days }}</td>
              </tr>
              <tr>
                <td><b>Games played:</b></td>
                <td>{{ stats?.total.games }}</td>
              </tr>
              <tr>
                <td><b>Platforms played on:</b></td>
                <td>{{ stats?.total.platforms }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>Total playtime:</b></td>
                <td>{{ formatDuration(stats?.total.seconds) }}</td>
              </tr>
              <tr>
                <td><b>Total sessions:</b></td>
                <td>{{ stats?.total.activities }}</td>
              </tr>
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
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

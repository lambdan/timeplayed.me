<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { User, UserStats } from "../models/models";

const FALLBACK_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png";

const props = defineProps<{ user: User }>();

const stats = ref<UserStats>();
const loadingStats = ref(true);

onMounted(async () => {
  const res = await fetch(`/api/users/${props.user.id}/stats`);
  const data: UserStats = await res.json();
  stats.value = data;
  loadingStats.value = false;
});

function formatDate(number?: number): string {
  if (!number) return "N/A";
  const date = new Date(number);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(
    2,
    "0"
  )}-${String(date.getDate()).padStart(2, "0")} ${String(
    date.getHours()
  ).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}:${String(
    date.getSeconds()
  ).padStart(2, "0")} UTC`;
}

function formatDuration(secs?: number): string {
  if (!secs) return "N/A";
  const hours = (secs / 3600).toFixed(1);
  return `${hours} hours`;
}

function timeAgo(timestamp?: number): string {
  if (!timestamp) return "";
  const now = new Date();
  const parsedDate = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - parsedDate.getTime()) / 1000);

  const intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
  ];

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count > 0) return `${count} ${i.label}${count !== 1 ? "s" : ""} ago`;
  }

  return "just now";
}
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">{{ user.name }}</h1>
    <div class="card-body">
      <div class="row">
        <div class="col-lg-2 mb-4">
          <img
            :src="user.avatar_url ?? FALLBACK_AVATAR"
            class="img-thumbnail img-fluid rounded-circle"
          />
        </div>

        <div class="col mb-4">
          <table class="table table-responsive table-hover">
            <tbody>
              <tr>
                <td><b>First session:</b></td>
                <td>
                  {{ formatDate(stats?.first_activity) }}
                  <br />
                  <small class="text-muted">
                    {{ timeAgo(stats?.first_activity) }}
                  </small>
                </td>
              </tr>
              <tr>
                <td><b>Last session:</b></td>
                <td>
                  {{ formatDate(stats?.last_active) }}
                  <br />
                  <small class="text-muted">
                    {{ timeAgo(stats?.last_active) }}
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

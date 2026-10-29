<script setup lang="ts">
import { computed } from "vue";
import type { Activity } from "../../api.models";
import { formatDuration } from "../../utils";

// activities grouped by how long they were
const props = defineProps<{ sessions: Activity[] }>();

const MINUTE = 60;
const BUCKETS = [
  { label: "Under 30 min", max: 30 * MINUTE },
  { label: "30 min – 1 h", max: 60 * MINUTE },
  { label: "1 – 2 h", max: 120 * MINUTE },
  { label: "2 – 4 h", max: 240 * MINUTE },
  { label: "4 h or more", max: Infinity },
];

const rows = computed(() => {
  const res = BUCKETS.map((b) => ({ ...b, sessions: 0, seconds: 0 }));
  for (const a of props.sessions) {
    const row = res.find((b) => a.seconds < b.max)!;
    row.sessions += 1;
    row.seconds += a.seconds;
  }
  return res;
});
const maxSessions = computed(() =>
  Math.max(...rows.value.map((r) => r.sessions), 1),
);
const totalSeconds = computed(() =>
  props.sessions.reduce((a, b) => a + b.seconds, 0),
);
</script>

<template>
  <div class="table-responsive">
    <table class="table table-hover align-middle">
      <thead>
        <tr>
          <th>Length</th>
          <th class="w-25 d-none d-md-table-cell"></th>
          <th class="text-end">Activities</th>
          <th class="text-end d-none d-sm-table-cell">Share</th>
          <th class="text-end">Played</th>
          <th class="text-end d-none d-sm-table-cell">Share of playtime</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.label">
          <td class="fw-semibold text-nowrap">{{ r.label }}</td>
          <td class="d-none d-md-table-cell">
            <div class="progress" style="height: 6px">
              <div
                class="progress-bar bg-warning"
                :style="{ width: `${(r.sessions / maxSessions) * 100}%` }"
              ></div>
            </div>
          </td>
          <td class="text-end">{{ r.sessions }}</td>
          <td class="text-end text-body-secondary d-none d-sm-table-cell">
            {{ ((r.sessions / sessions.length) * 100).toFixed(0) }}%
          </td>
          <td class="text-end text-nowrap">
            {{ r.seconds ? formatDuration(r.seconds) : "–" }}
          </td>
          <td class="text-end text-body-secondary d-none d-sm-table-cell">
            {{ ((r.seconds / totalSeconds) * 100).toFixed(0) }}%
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

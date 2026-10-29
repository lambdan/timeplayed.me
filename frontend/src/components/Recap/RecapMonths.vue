<script setup lang="ts">
import { computed } from "vue";
import { formatDuration } from "../../utils";
import { MONTHS, type RecapMonth } from "../../utils.recap";

const props = defineProps<{
  months: RecapMonth[];
  gameNames: Map<number, string>;
}>();

const max = computed(() => Math.max(...props.months.map((m) => m.seconds), 1));
const total = computed(() => props.months.reduce((a, b) => a + b.seconds, 0));

function share(seconds: number): string {
  return total.value ? `${((seconds / total.value) * 100).toFixed(0)}%` : "–";
}
</script>

<template>
  <div class="table-responsive">
    <table class="table table-hover align-middle">
      <thead>
        <tr>
          <th>Month</th>
          <th class="w-25 d-none d-md-table-cell"></th>
          <th class="text-end">Played</th>
          <th class="text-end d-none d-sm-table-cell">Sessions</th>
          <th class="text-end d-none d-sm-table-cell">Share</th>
          <th>Most played</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(month, i) in months" :key="i">
          <td class="fw-semibold">{{ MONTHS[i] }}</td>
          <td class="d-none d-md-table-cell">
            <div class="progress" style="height: 6px">
              <div
                class="progress-bar bg-warning"
                :style="{ width: `${(month.seconds / max) * 100}%` }"
              ></div>
            </div>
          </td>
          <td class="text-end text-nowrap">
            {{ month.seconds ? formatDuration(month.seconds) : "–" }}
          </td>
          <td class="text-end text-body-secondary d-none d-sm-table-cell">
            {{ month.sessions || "–" }}
          </td>
          <td class="text-end text-body-secondary d-none d-sm-table-cell">
            {{ month.seconds ? share(month.seconds) : "–" }}
          </td>
          <td>
            <a
              v-if="month.top_game_id"
              :href="`/game/${month.top_game_id}`"
              class="link-underline link-underline-opacity-0"
              >{{ gameNames.get(month.top_game_id) }}</a
            >
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

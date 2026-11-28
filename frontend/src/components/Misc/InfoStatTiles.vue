<script setup lang="ts">
import { formatDuration, iso8601Date, timeAgo } from "../../utils";
import RecapStatTile from "../Recap/RecapStatTile.vue";

// the totals at the top of a game or platform page, as tiles
defineProps<{
  stats: {
    seconds: number;
    activity_count: number;
    first_activity?: number | null;
    last_activity?: number | null;
  };
  /** tiles after playtime and activities, like users and platforms */
  counts: { label: string; value: number | string; sub?: string }[];
  /** two tiles per row on every screen, for narrow cards */
  narrow?: boolean;
  /** tile colors, like a platform's */
  background?: string;
  color?: string;
}>();
</script>

<template>
  <div class="row row-cols-2 g-2" :class="{ 'row-cols-xl-3': !narrow }">
    <div class="col">
      <RecapStatTile
        label="Playtime"
        :value="formatDuration(stats.seconds)"
        :small="true"
        :background="background"
        :color="color"
      />
    </div>
    <div class="col">
      <RecapStatTile
        label="Activities"
        :value="`${stats.activity_count}`"
        :sub="
          stats.activity_count > 0
            ? `${formatDuration(stats.seconds / stats.activity_count)} average`
            : undefined
        "
        :small="true"
        :background="background"
        :color="color"
      />
    </div>
    <div v-for="count in counts" :key="count.label" class="col">
      <RecapStatTile
        :label="count.label"
        :value="`${count.value}`"
        :sub="count.sub"
        :small="true"
        :background="background"
        :color="color"
      />
    </div>
    <div v-if="stats.first_activity" class="col">
      <RecapStatTile
        label="First played"
        :value="timeAgo(stats.first_activity)"
        :sub="iso8601Date(stats.first_activity)"
        :small="true"
        :background="background"
        :color="color"
      />
    </div>
    <div v-if="stats.last_activity" class="col">
      <RecapStatTile
        label="Last played"
        :value="timeAgo(stats.last_activity)"
        :sub="iso8601Date(stats.last_activity)"
        :small="true"
        :background="background"
        :color="color"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameWithStats } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import CroppedCover from "./CroppedCover.vue";
import CalendarBasic from "../CalendarBasic.vue";
import ExpandToggle from "../Misc/ExpandToggle.vue";
// rows for its children are this same component, one level deeper
import ChildGamesRows from "./ChildGamesRows.vue";

// table rows for the children of a game, each with the playtime of its own children
// included, and a row for the game itself (without children) so the rows add up to its
// total. Games with children can be expanded to show them under it
const props = defineProps<{
  parent: GameWithStats;
  depth: number;
  /** same filters as the list the rows are in, e.g. its date range */
  filters?: {
    user?: number;
    platform?: number;
    after?: number;
    before?: number;
  };
  /** for TopGamesList: an empty rank cell, name and playtime only, no unplayed games */
  compact?: boolean;
}>();

const games = ref<GameWithStats[]>([]);
const loading = ref(true);
const expanded = ref(new Set<number>());
// less in the compact list, it's in a narrow column
const indent = props.compact ? 0.75 : 1.5;

function setExpanded(id: number, value: boolean) {
  if (value) {
    expanded.value.add(id);
  } else {
    expanded.value.delete(id);
  }
}

onMounted(async () => {
  const [children, parentOnly] = await Promise.all([
    TimeplayedAPI.getGameStatsMany(props.parent.children_ids, {
      ...props.filters,
      include_children: true,
    }),
    TimeplayedAPI.getGameStats(props.parent.id, props.filters),
  ]);
  let rows = children.sort((a, b) => b.stats.seconds - a.stats.seconds);
  if (props.compact) {
    rows = rows.filter((g) => g.stats.seconds > 0);
  }
  // the parent's own playtime, among the children by playtime
  if (parentOnly.stats.seconds > 0) {
    const i = rows.findIndex((g) => g.stats.seconds < parentOnly.stats.seconds);
    rows.splice(i === -1 ? rows.length : i, 0, parentOnly);
  }
  games.value = rows;
  loading.value = false;
});

function hasChildRows(game: GameWithStats) {
  // the parent's own row is already expanded, its children are the other rows
  return game.id !== props.parent.id && game.children_ids.length > 0;
}
</script>

<template>
  <tr v-if="loading">
    <td :colspan="compact ? 3 : 4" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </td>
  </tr>
  <template v-for="game in games" :key="game.id">
    <tr>
      <td v-if="compact"></td>
      <td :style="{ paddingLeft: `${0.25 + depth * indent}rem` }">
        <div class="d-flex align-items-center gap-2">
          <ExpandToggle
            v-if="hasChildRows(game)"
            :modelValue="expanded.has(game.id)"
            @update:modelValue="(value) => setExpanded(game.id, value)"
          />
          <!-- same width as the button, so covers line up -->
          <span v-else class="flex-shrink-0" style="width: 1em"></span>
          <CroppedCover
            :gameId="game.id"
            class="flex-shrink-0"
            :class="{ 'opacity-50': expanded.has(game.id) }"
            style="width: 28px"
          />
          <a
            :href="`/game/${game.id}`"
            class="link-underline link-underline-opacity-0 text-break"
            :class="{ 'opacity-50': expanded.has(game.id) }"
            >{{ game.name }}</a
          >
        </div>
      </td>
      <td class="text-end text-nowrap">
        <span :class="{ 'opacity-50': expanded.has(game.id) }">{{
          formatDuration(game.stats.seconds)
        }}</span>
      </td>
      <template v-if="!compact">
        <td class="text-end">
          <span :class="{ 'opacity-50': expanded.has(game.id) }">{{
            game.stats.user_count
          }}</span>
        </td>
        <td class="text-end text-nowrap d-none d-md-table-cell">
          <span :class="{ 'opacity-50': expanded.has(game.id) }"
            ><CalendarBasic
              v-if="game.stats.last_activity"
              :date="game.stats.last_activity"
              :showIcon="false"
          /></span>
        </td>
      </template>
    </tr>
    <ChildGamesRows
      v-if="expanded.has(game.id)"
      :parent="game"
      :depth="depth + 1"
      :filters="filters"
      :compact="compact"
    />
  </template>
</template>

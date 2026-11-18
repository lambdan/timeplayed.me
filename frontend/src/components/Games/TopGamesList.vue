<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { GameWithStats, Platform, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import CroppedCover from "./CroppedCover.vue";
import ExpandToggle from "../Misc/ExpandToggle.vue";
import ChildGamesRows from "./ChildGamesRows.vue";

// compact ranked list of the most played games in a date range, one section of the "most played" cards
const props = withDefaults(
  defineProps<{
    platform?: Platform;
    user?: User;
    /** only games with names matching this */
    search?: string;
    after?: Date;
    before?: Date;
    limit?: number;
  }>(),
  { limit: 10 },
);

const games = ref<GameWithStats[]>([]);
const loading = ref(true);
// child games are counted in their parent.
// not when searching, the game searched for could be a child
const grouped = computed(() => !props.search);
const expanded = ref(new Set<number>());
let latest = 0;

const filters = computed(() => ({
  platform: props.platform?.id,
  user: props.user?.id,
  after: props.after?.getTime(),
  before: props.before?.getTime(),
}));

function setExpanded(id: number, value: boolean) {
  if (value) {
    expanded.value.add(id);
  } else {
    expanded.value.delete(id);
  }
}

watch(
  () => [filters.value, props.search, grouped.value],
  async () => {
    const request = ++latest;
    loading.value = true;
    const data = await TimeplayedAPI.getGamesStats({
      ...filters.value,
      search: props.search || undefined,
      include_children: grouped.value,
      limit: props.limit,
      sort: "playtime",
      order: "desc",
    });
    if (request !== latest) return; // a newer range was picked meanwhile
    games.value = data;
    // the open child rows were for the old filters
    expanded.value.clear();
    loading.value = false;
  },
  { immediate: true },
);
</script>

<template>
  <div>
    <h3 class="h5 mb-2">Games</h3>
    <div v-if="loading" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </div>
    <p v-else-if="!games.length" class="text-body-secondary text-center mb-0">
      {{ search ? "No matches" : "Nothing played" }}
    </p>
    <table v-else class="table table-sm table-hover align-middle mb-0">
      <tbody>
        <template v-for="(game, i) in games" :key="game.id">
          <tr>
            <td class="text-body-secondary" style="width: 1%">{{ i + 1 }}</td>
            <td>
              <div class="d-flex align-items-center gap-2">
                <template v-if="grouped">
                  <ExpandToggle
                    v-if="game.children_ids.length > 0"
                    :modelValue="expanded.has(game.id)"
                    @update:modelValue="(value) => setExpanded(game.id, value)"
                  />
                  <!-- same width as the button, so covers line up -->
                  <span v-else class="flex-shrink-0" style="width: 1em"></span>
                </template>
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
          </tr>
          <ChildGamesRows
            v-if="expanded.has(game.id)"
            :parent="game"
            :depth="1"
            :filters="filters"
            :compact="true"
          />
        </template>
      </tbody>
    </table>
  </div>
</template>

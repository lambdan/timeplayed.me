<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import type { Game } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { AdminAPI, type AdminGame } from "../../admin.client";
import { useNsfw } from "../../composables/useNsfw";

/**
 * Search for a game and pick one. The value is the picked game's id (null when none),
 * typing something else clears it. `picked` also hands over the whole game.
 */
const props = withDefaults(
  defineProps<{
    /** admin pages: hidden games too, with their id and activity count */
    admin?: boolean;
    /** games that can't be picked, like the game being edited */
    exclude?: number[];
    /** search text to start with, like part of a name */
    initialQuery?: string;
    size?: "sm" | "lg";
    id?: string;
    placeholder?: string;
  }>(),
  {
    admin: false,
    exclude: () => [],
    initialQuery: "",
    size: undefined,
    id: undefined,
    placeholder: "Search for a game...",
  },
);
const gameId = defineModel<number | null>({ default: null });
const emit = defineEmits<{ picked: [game: Game | AdminGame] }>();

const { isCensored } = useNsfw();
const query = ref(props.initialQuery);
const results = ref<(Game | AdminGame)[]>([]);
const error = ref("");
// the picked game, so its name in the field doesn't start a search
let picked: { id: number; name: string } | undefined;

const visibleResults = computed(() =>
  results.value.filter(
    // nsfw games are left out unless the viewer opted in, admins see everything
    (g) => !props.exclude.includes(g.id) && (props.admin || !isCensored(g)),
  ),
);

async function fetchGame(id: number) {
  return props.admin ? AdminAPI.getGame(id) : TimeplayedAPI.getGame(id);
}

async function search(text: string) {
  try {
    error.value = "";
    results.value = props.admin
      ? await AdminAPI.getGames({ search: text, limit: 10 })
      : await TimeplayedAPI.getGames({
          search: text,
          limit: 10,
          order: "desc",
          sort: "updated",
        });
  } catch {
    error.value = "Searching for games failed";
  }
}

let searchTimeout: number | undefined;
watch(query, (text) => {
  window.clearTimeout(searchTimeout);
  if (picked && text === picked.name) {
    results.value = [];
    return;
  }
  // typing something else means the picked game isn't the one anymore
  picked = undefined;
  if (gameId.value !== null) gameId.value = null;
  if (!text.trim()) {
    results.value = [];
    return;
  }
  searchTimeout = window.setTimeout(() => search(text), 300);
});
// a starting guess is searched once the field is used, not right away
function searchOnFocus() {
  if (!picked && query.value.trim() && !results.value.length) {
    search(query.value);
  }
}
onUnmounted(() => window.clearTimeout(searchTimeout));

function pick(g: Game | AdminGame) {
  picked = { id: g.id, name: g.name };
  query.value = g.name;
  results.value = [];
  emit("picked", g);
  gameId.value = g.id;
}

// picked from outside (a saved value, or another list on the page): show its name
watch(
  gameId,
  async (id) => {
    if (id === null) {
      // cleared from outside, like reverting a form
      if (picked) {
        picked = undefined;
        query.value = "";
      }
      return;
    }
    if (id === picked?.id) return;
    try {
      const g = await fetchGame(id);
      if (gameId.value !== id) return; // changed while loading
      picked = { id: g.id, name: g.name };
      query.value = g.name;
    } catch {
      error.value = `Game ${id} not found`;
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="position-relative">
    <input
      :id="id"
      v-model="query"
      type="search"
      class="form-control"
      :class="size ? `form-control-${size}` : undefined"
      :placeholder="placeholder"
      autocomplete="off"
      @focus="searchOnFocus"
      @keydown.esc="results = []"
    />
    <div
      v-if="visibleResults.length"
      class="list-group position-absolute w-100 z-3 shadow overflow-auto"
      style="max-height: 300px"
    >
      <button
        v-for="g in visibleResults"
        :key="g.id"
        type="button"
        class="list-group-item list-group-item-action"
        @click="pick(g)"
      >
        {{ g.name }}
        <span v-if="g.release_year" class="text-body-secondary"
          >({{ g.release_year }})</span
        >
        <div v-if="admin" class="small text-body-secondary">
          ID {{ g.id }}
          <template v-if="'activity_count' in g">
            · {{ g.activity_count }} activities</template
          >
        </div>
      </button>
    </div>
    <div v-if="error" class="small text-danger mt-1">{{ error }}</div>
  </div>
</template>

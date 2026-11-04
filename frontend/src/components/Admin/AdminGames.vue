<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  AdminAPI,
  type AdminGame,
  type AdminGameMissing,
} from "../../admin.client";
import AdminGameEditor from "./AdminGameEditor.vue";

const PAGE_SIZE = 100;

const route = useRoute();
const router = useRouter();

const games = ref<AdminGame[]>([]);
const hasMore = ref(false);
const search = ref("");
const missing = ref<AdminGameMissing | "">("");
const newGameName = ref("");
const error = ref("");

const selectedId = ref<number>();

async function fetchGames(append = false) {
  try {
    error.value = "";
    const offset = append ? games.value.length : 0;
    const page = await AdminAPI.getGames({
      search: search.value.trim(),
      missing: missing.value || undefined,
      offset,
      limit: PAGE_SIZE,
    });
    games.value = append ? [...games.value, ...page] : page;
    hasMore.value = page.length === PAGE_SIZE;
  } catch (e: any) {
    error.value = e.message;
  }
}

function select(id?: number) {
  router.replace({ query: { tab: "games", id } });
}

async function addGame() {
  const name = newGameName.value.trim();
  if (!name) return;
  try {
    error.value = "";
    const game = await AdminAPI.addGame(name);
    newGameName.value = "";
    fetchGames();
    select(game.id);
  } catch (e: any) {
    error.value = e.message;
  }
}

function onDeleted() {
  select(undefined);
  fetchGames();
}

let searchTimeout: ReturnType<typeof setTimeout>;
watch(search, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => fetchGames(), 200);
});
watch(missing, () => fetchGames());
watch(
  () => route.query.id,
  () => {
    selectedId.value = parseInt(route.query.id as string) || undefined;
  },
  { immediate: true },
);

onMounted(() => fetchGames());
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <AdminGameEditor
      v-if="selectedId"
      :key="selectedId"
      :game-id="selectedId"
      class="mb-3"
      @close="select(undefined)"
      @changed="fetchGames()"
      @deleted="onDeleted"
      @select="select"
    />

    <div class="row g-2 mb-2">
      <div class="col-12 col-md-5">
        <input
          v-model="search"
          class="form-control"
          type="search"
          placeholder="Search games"
        />
      </div>
      <div class="col-12 col-md-3">
        <select v-model="missing" class="form-select">
          <option value="">All games</option>
          <option value="igdb">Missing IGDB ID</option>
          <option value="sgdb">Missing SGDB ID</option>
          <option value="cover">Missing cover</option>
          <option value="release_year">Missing release year</option>
          <option value="activity">Without activity</option>
        </select>
      </div>
      <div class="col-12 col-md-4">
        <div class="input-group">
          <input
            v-model="newGameName"
            class="form-control"
            placeholder="New game name"
            @keydown.enter.prevent="addGame"
          />
          <button class="btn btn-outline-primary" @click="addGame">Add</button>
        </div>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table table-hover table-sm align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Year</th>
            <th class="d-none d-md-table-cell">IGDB</th>
            <th class="d-none d-md-table-cell">SGDB</th>
            <th class="d-none d-lg-table-cell">Steam</th>
            <th class="d-none d-lg-table-cell">Parent</th>
            <th class="text-end">Activities</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="g in games"
            :key="g.id"
            role="button"
            :class="{ 'table-active': selectedId === g.id }"
            @click="select(g.id)"
          >
            <td>{{ g.id }}</td>
            <td>
              {{ g.name }}
              <span v-if="g.hidden" class="badge text-bg-warning">hidden</span>
            </td>
            <td>{{ g.release_year ?? "-" }}</td>
            <td class="d-none d-md-table-cell">{{ g.igdb_id ?? "-" }}</td>
            <td class="d-none d-md-table-cell">{{ g.sgdb_id ?? "-" }}</td>
            <td class="d-none d-lg-table-cell">{{ g.steam_id ?? "-" }}</td>
            <td class="d-none d-lg-table-cell">{{ g.parent_id ?? "-" }}</td>
            <td class="text-end">{{ g.activity_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="games.length === 0" class="text-body-secondary">
      No games found
    </div>
    <button
      v-if="hasMore"
      class="btn btn-outline-secondary btn-sm"
      @click="fetchGames(true)"
    >
      Load more
    </button>
  </div>
</template>

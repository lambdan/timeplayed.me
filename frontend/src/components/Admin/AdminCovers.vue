<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import {
  AdminAPI,
  type AdminGame,
  type IGDBSearchResult,
} from "../../admin.client";
import { TimeplayedAPI } from "../../api.client";
import type { PlatformWithStats, UserWithStats } from "../../api.models";
import { formatDuration, iso8601Date } from "../../utils";
import { clearCachedGame } from "../../utils.cache";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import AdminIGDBResults from "./AdminIGDBResults.vue";

const PAGE_SIZE = 100;

// "cover": games without cover art, "not_on_igdb": games marked as not on igdb (id 0)
const mode = ref<"cover" | "not_on_igdb">("cover");
const queue = ref<AdminGame[]>([]);
const hasMore = ref(false);
const index = ref(0);
const game = computed<AdminGame | undefined>(() => queue.value[index.value]);
const error = ref("");
const message = ref("");
const busy = ref(false);

const players = ref<UserWithStats[]>([]);
const platforms = ref<PlatformWithStats[]>([]);

const igdbQuery = ref("");
const igdbResults = ref<IGDBSearchResult[]>();
const searching = ref(false);

const parentQuery = ref("");
const parentResults = ref<AdminGame[]>();
const imageUrl = ref("");

const remaining = computed(() =>
  hasMore.value ? `${queue.value.length}+` : `${queue.value.length}`,
);

async function loadQueue() {
  try {
    error.value = "";
    const page = await AdminAPI.getGames({
      missing: mode.value,
      limit: PAGE_SIZE,
    });
    queue.value = page;
    hasMore.value = page.length === PAGE_SIZE;
    index.value = 0;
  } catch (e: any) {
    error.value = e.message;
  }
}

/** new game in view: who played it, and try igdb with its name (like !aigdb) */
async function loadGame(g: AdminGame | undefined) {
  igdbResults.value = undefined;
  parentResults.value = undefined;
  mergeArmed.value = undefined;
  players.value = [];
  platforms.value = [];
  imageUrl.value = "";
  igdbSearch++;
  searching.value = false;
  if (!g) return;
  igdbQuery.value = g.name;
  // games are often a dlc or edition of another game, "Name: Subtitle" -> "Name"
  parentQuery.value = g.name.split(/[:\-–(]/)[0].trim();
  searchIGDB();
  try {
    const stats = await Promise.all([
      TimeplayedAPI.getUsersStats({ game: g.id, limit: 5, sort: "playtime" }),
      TimeplayedAPI.getPlatformsStats({ game: g.id, limit: 10 }),
    ]);
    // skipped to another game while loading
    if (game.value?.id !== g.id) return;
    [players.value, platforms.value] = stats;
  } catch {
    // hidden games have no public stats, not a problem
  }
}

// only the newest search counts. An older one finishing late (like the automatic search
// for the previous game) would show results that don't belong to what's on screen
let igdbSearch = 0;

async function searchIGDB() {
  const q = igdbQuery.value.trim();
  if (!q) return;
  const mine = ++igdbSearch;
  try {
    error.value = "";
    searching.value = true;
    const results = await AdminAPI.searchIGDB(q);
    if (mine === igdbSearch) igdbResults.value = results;
  } catch (e: any) {
    if (mine === igdbSearch) error.value = e.message;
  } finally {
    if (mine === igdbSearch) searching.value = false;
  }
}

async function searchParent() {
  const q = parentQuery.value.trim();
  if (!q || !game.value) return;
  try {
    error.value = "";
    const id = game.value.id;
    const found = await AdminAPI.getGames({ search: q, limit: 10 });
    // skipped to another game while searching
    if (game.value?.id !== id) return;
    parentResults.value = found.filter((g) => g.id !== id);
  } catch (e: any) {
    error.value = e.message;
  }
}

/** runs a change on the current game, then it's done and leaves the queue */
async function resolve(change: (id: number) => Promise<unknown>, what: string) {
  const g = game.value;
  if (!g || busy.value) return;
  try {
    busy.value = true;
    error.value = "";
    await change(g.id);
    // public pages in this tab show the new cover (children use the parents)
    clearCachedGame(g.id);
    g.children_ids.forEach(clearCachedGame);
    message.value = `${g.name}: ${what}`;
    queue.value.splice(index.value, 1);
    if (index.value >= queue.value.length) index.value = 0;
    if (queue.value.length === 0 && hasMore.value) await loadQueue();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}

function useIGDB(igdbId: number) {
  resolve((id) => AdminAPI.setIGDBId(id, igdbId), `IGDB ID set to ${igdbId}`);
}

function notOnIGDB() {
  resolve((id) => AdminAPI.setIGDBId(id, 0), "marked as not on IGDB");
}

function setParent(parent: AdminGame) {
  const notOnIGDB = game.value?.igdb_id === 0;
  resolve(async (id) => {
    await AdminAPI.patchGame(id, { parent_id: parent.id });
    // igdb id 0 would stop it from using the parents igdb id (and cover)
    if (notOnIGDB) await AdminAPI.setIGDBId(id, null);
  }, `parent set to ${parent.name}`);
}

// a duplicate (like "warcraft ii" next to "Warcraft II"), needs a second click
const mergeArmed = ref<number>();
function mergeInto(target: AdminGame) {
  if (mergeArmed.value !== target.id) {
    mergeArmed.value = target.id;
    return;
  }
  mergeArmed.value = undefined;
  resolve(async (id) => {
    await AdminAPI.mergeGame(id, target.id);
    clearCachedGame(target.id);
  }, `merged into ${target.name}`);
}

// a pasted IGDB ID instead of a search
const typedIGDBId = computed(() => {
  const q = igdbQuery.value.trim();
  return /^\d+$/.test(q) ? parseInt(q) : null;
});

function setImageUrl() {
  const url = imageUrl.value.trim();
  if (!url) return;
  resolve((id) => AdminAPI.patchGame(id, { image_url: url }), "image set");
}

function skip() {
  message.value = "";
  index.value = (index.value + 1) % queue.value.length;
}

function hasCover(g: AdminGame) {
  return !!(g.igdb_id || g.sgdb_id || g.image_url);
}

watch(game, (g) => loadGame(g));
watch(mode, () => {
  message.value = "";
  loadQueue();
});
onMounted(loadQueue);
</script>

<template>
  <div>
    <div class="btn-group mb-3" role="group">
      <button
        class="btn btn-outline-secondary"
        :class="{ active: mode === 'cover' }"
        @click="mode = 'cover'"
      >
        Missing cover
      </button>
      <button
        class="btn btn-outline-secondary"
        :class="{ active: mode === 'not_on_igdb' }"
        @click="mode = 'not_on_igdb'"
      >
        Not on IGDB
      </button>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
      <a v-if="game" :href="`/admin?tab=games&id=${game.id}`" class="ms-1"
        >Open in editor</a
      >
    </div>
    <div v-if="message" class="alert alert-success py-2">{{ message }}</div>

    <div v-if="!game" class="text-body-secondary">
      {{
        mode === "cover"
          ? "No games without a cover"
          : "No games marked as not on IGDB"
      }}
    </div>

    <div v-else class="card p-0">
      <div class="card-header d-flex align-items-center gap-2">
        <strong class="me-auto">
          {{ game.name }}
          <span v-if="game.release_year" class="text-body-secondary"
            >({{ game.release_year }})</span
          >
        </strong>
        <span class="text-body-secondary small text-nowrap"
          >{{ index + 1 }} / {{ remaining }}</span
        >
      </div>
      <div class="card-body p-2 p-md-3">
        <div class="small mb-2">
          ID {{ game.id }} · {{ game.activity_count }} activities
          <template v-if="game.last_activity">
            · last played {{ iso8601Date(game.last_activity) }}</template
          >
          <span v-if="game.hidden" class="badge text-bg-warning">hidden</span>
        </div>
        <div v-if="game.aliases.length" class="small mb-2">
          Aliases: {{ game.aliases.join(", ") }}
        </div>
        <div
          v-if="platforms.length || players.length"
          class="d-flex flex-wrap align-items-center gap-1 small mb-3"
        >
          <PlatformBadge v-for="p in platforms" :key="p.id" :platform="p" />
          <span v-for="u in players" :key="u.id" class="text-body-secondary">
            · {{ u.display_name }} {{ formatDuration(u.stats.seconds) }}
          </span>
        </div>

        <div class="d-flex flex-wrap gap-2 mb-3">
          <button class="btn btn-outline-secondary" @click="skip">Skip</button>
          <button
            v-if="mode === 'cover'"
            class="btn btn-outline-warning"
            :disabled="busy"
            @click="notOnIGDB"
          >
            Not on IGDB
          </button>
          <a
            class="btn btn-outline-secondary"
            :href="`/admin?tab=games&id=${game.id}`"
            >Editor</a
          >
        </div>

        <h6>IGDB</h6>
        <div class="input-group mb-2">
          <input
            v-model="igdbQuery"
            class="form-control"
            type="search"
            @keydown.enter.prevent="searchIGDB"
          />
          <button
            class="btn btn-outline-primary"
            :disabled="searching"
            @click="searchIGDB"
          >
            Search
          </button>
        </div>
        <div class="d-flex flex-wrap gap-3 small mb-2">
          <a
            :href="`https://www.igdb.com/search?type=1&q=${encodeURIComponent(igdbQuery)}`"
            target="_blank"
            >Search on IGDB.com</a
          >
          <a
            :href="`https://www.google.com/search?q=${encodeURIComponent('igdb ' + igdbQuery)}`"
            target="_blank"
            >Google</a
          >
        </div>
        <button
          v-if="typedIGDBId"
          class="btn btn-primary mb-3"
          :disabled="busy"
          @click="useIGDB(typedIGDBId)"
        >
          Use IGDB ID {{ typedIGDBId }}
        </button>
        <div v-if="searching" class="text-body-secondary mb-3">
          Searching...
        </div>
        <AdminIGDBResults
          v-else-if="igdbResults"
          :results="igdbResults"
          class="mb-3"
          @use="useIGDB"
        />

        <h6>Parent game</h6>
        <div class="input-group mb-2">
          <input
            v-model="parentQuery"
            class="form-control"
            type="search"
            placeholder="Search our games"
            @keydown.enter.prevent="searchParent"
          />
          <button class="btn btn-outline-primary" @click="searchParent">
            Search
          </button>
        </div>
        <ul v-if="parentResults" class="list-group list-group-flush mb-3">
          <li v-if="parentResults.length === 0" class="list-group-item px-0">
            No games found
          </li>
          <li
            v-for="p in parentResults"
            :key="p.id"
            class="list-group-item px-0 d-flex align-items-center gap-2"
          >
            <div class="me-auto">
              {{ p.name }}
              <span v-if="p.release_year" class="text-body-secondary"
                >({{ p.release_year }})</span
              >
              <div class="small text-body-secondary">
                ID {{ p.id }} ·
                {{ hasCover(p) ? "has cover" : "no cover either" }}
              </div>
            </div>
            <div class="d-flex flex-column flex-sm-row gap-1">
              <button
                class="btn btn-outline-primary"
                :disabled="busy"
                @click="setParent(p)"
              >
                Set as parent
              </button>
              <button
                class="btn btn-outline-danger"
                :disabled="busy"
                @click="mergeInto(p)"
              >
                {{
                  mergeArmed === p.id
                    ? `Really merge ${game.activity_count} activities?`
                    : "Merge into"
                }}
              </button>
            </div>
          </li>
        </ul>

        <h6>Image URL</h6>
        <div class="input-group">
          <input
            v-model="imageUrl"
            class="form-control"
            type="url"
            placeholder="https://..."
            @keydown.enter.prevent="setImageUrl"
          />
          <button
            class="btn btn-outline-primary"
            :disabled="busy || !imageUrl.trim()"
            @click="setImageUrl"
          >
            Set
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

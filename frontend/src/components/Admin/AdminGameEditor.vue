<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  AdminAPI,
  type AdminGameDetails,
  type AdminGamePatch,
  type IGDBSearchResult,
  type SGDBSearchResult,
} from "../../admin.client";
import { TimeplayedAPI } from "../../api.client";
import AdminHistory from "./AdminHistory.vue";
import AdminSectionTabs from "./AdminSectionTabs.vue";
import AdminUnsaved from "./AdminUnsaved.vue";
import { unsavedFieldLabels } from "../../utils.admin";

const props = defineProps<{ gameId: number }>();
const emit = defineEmits<{
  close: [];
  changed: [];
  deleted: [];
  select: [id: number];
}>();

const game = ref<AdminGameDetails>();
const error = ref("");
const message = ref("");

// edit form, strings so empty input means null
const form = ref({
  name: "",
  release_year: "",
  image_url: "",
  steam_id: "",
  parent_id: "",
  hidden: false,
});
const igdbId = ref("");
const sgdbId = ref("");
const newAlias = ref("");
const igdbQuery = ref("");
const sgdbQuery = ref("");
const igdbResults = ref<IGDBSearchResult[]>();
const sgdbResults = ref<SGDBSearchResult[]>();

const targetId = ref("");
const mergePreview = ref<{ activity_count: number; new_aliases: string[] }>();
const moveArmed = ref(false);
const deleteArmed = ref(false);
const section = ref("details");

function toNumberOrNull(value: string | number): number | null {
  // v-model on a number input gives a number once it has been edited
  if (typeof value === "number") return value;
  return value.trim() === "" ? null : parseInt(value);
}

function setGame(g: AdminGameDetails) {
  game.value = g;
  form.value = {
    name: g.name,
    release_year: g.release_year?.toString() ?? "",
    image_url: g.image_url ?? "",
    steam_id: g.steam_id?.toString() ?? "",
    parent_id: g.parent_id?.toString() ?? "",
    hidden: g.hidden,
  };
  igdbId.value = g.igdb_id?.toString() ?? "";
  sgdbId.value = g.sgdb_id?.toString() ?? "";
}

/** runs an API call that returns the updated game */
async function run(
  call: () => Promise<AdminGameDetails>,
  successMessage: string,
) {
  try {
    error.value = "";
    message.value = "";
    setGame(await call());
    message.value = successMessage;
    emit("changed");
  } catch (e: any) {
    error.value = e.message;
  }
}

/** fields in the form that differ from the saved game, this is what save sends */
const patch = computed(() => {
  const changed: AdminGamePatch = {};
  const g = game.value;
  if (!g) return changed;
  if (form.value.name !== g.name) changed.name = form.value.name;
  const year = toNumberOrNull(form.value.release_year);
  if (year !== g.release_year) changed.release_year = year;
  const imageUrl = form.value.image_url.trim() || null;
  if (imageUrl !== g.image_url) changed.image_url = imageUrl;
  const steamId = toNumberOrNull(form.value.steam_id);
  if (steamId !== g.steam_id) changed.steam_id = steamId;
  const parentId = toNumberOrNull(form.value.parent_id);
  if (parentId !== g.parent_id) changed.parent_id = parentId;
  if (form.value.hidden !== g.hidden) changed.hidden = form.value.hidden;
  return changed;
});

const FIELD_LABELS: Record<keyof AdminGamePatch, string> = {
  name: "name",
  release_year: "release year",
  image_url: "image URL",
  steam_id: "Steam ID",
  parent_id: "parent",
  hidden: "hidden",
};

// set when refreshing from IGDB renames the game, so the old name still matches
const keepOldNameAsAlias = ref(false);
const aliasToAdd = computed(() => {
  const g = game.value;
  if (!g || !keepOldNameAsAlias.value || !("name" in patch.value)) return null;
  if (g.aliases.includes(g.name)) return null;
  return g.name;
});

const unsavedLabels = computed(() => {
  const labels = unsavedFieldLabels(patch.value, FIELD_LABELS);
  if (aliasToAdd.value) labels.push(`alias "${aliasToAdd.value}"`);
  return labels;
});

function save() {
  if (!game.value) return;
  const id = game.value.id;
  const changes = patch.value;
  const alias = aliasToAdd.value;
  run(async () => {
    // rename first, the old name can't be an alias while it's still the name
    let updated = await AdminAPI.patchGame(id, changes);
    if (alias) updated = await AdminAPI.addAlias(id, alias);
    keepOldNameAsAlias.value = false;
    return updated;
  }, "Saved");
}

async function refreshFromIGDB() {
  const g = game.value;
  if (!g?.igdb_id) return;
  try {
    error.value = "";
    message.value = "";
    const info = await TimeplayedAPI.getIGDBGameInfo(g.igdb_id);
    if (!info) {
      error.value = "Game not found in IGDB";
      return;
    }
    // same as setting the IGDB ID: if the IGDB name is an alias, we keep our name
    if (info.name !== g.name && !g.aliases.includes(info.name)) {
      form.value.name = info.name;
      keepOldNameAsAlias.value = true;
    }
    if (info.first_release_date) {
      form.value.release_year = year(info.first_release_date).toString();
    }
    if (unsavedLabels.value.length === 0) {
      message.value = "Already matches IGDB";
    }
  } catch (e: any) {
    error.value = e.message ?? e.detail ?? "Failed to fetch from IGDB";
  }
}

function setIGDB(id: number | null) {
  run(() => AdminAPI.setIGDBId(props.gameId, id), "IGDB ID set");
  igdbResults.value = undefined;
}

function setSGDB(id: number | null) {
  run(() => AdminAPI.setSGDBId(props.gameId, id), "SGDB ID set");
  sgdbResults.value = undefined;
}

async function searchIGDB() {
  try {
    error.value = "";
    igdbResults.value = await AdminAPI.searchIGDB(igdbQuery.value.trim());
  } catch (e: any) {
    error.value = e.message;
  }
}

async function searchSGDB() {
  try {
    error.value = "";
    sgdbResults.value = await AdminAPI.searchSGDB(sgdbQuery.value.trim());
  } catch (e: any) {
    error.value = e.message;
  }
}

function year(ts: number | null) {
  // IGDB and SGDB give seconds
  return ts ? new Date(ts * 1000).getUTCFullYear() : "?";
}

function addAlias() {
  const alias = newAlias.value.trim();
  if (!alias) return;
  run(() => AdminAPI.addAlias(props.gameId, alias), "Alias added");
  newAlias.value = "";
}

function removeAlias(alias: string) {
  run(() => AdminAPI.removeAlias(props.gameId, alias), "Alias removed");
}

async function previewMerge() {
  moveArmed.value = false;
  try {
    error.value = "";
    mergePreview.value = await AdminAPI.mergePreview(
      props.gameId,
      parseInt(targetId.value),
    );
  } catch (e: any) {
    error.value = e.message;
  }
}

async function merge() {
  const into = parseInt(targetId.value);
  try {
    error.value = "";
    await AdminAPI.mergeGame(props.gameId, into);
    emit("changed");
    emit("select", into);
  } catch (e: any) {
    error.value = e.message;
  }
}

async function moveActivities() {
  mergePreview.value = undefined;
  if (!moveArmed.value) {
    moveArmed.value = true;
    return;
  }
  moveArmed.value = false;
  try {
    error.value = "";
    const res = await AdminAPI.moveActivities(
      props.gameId,
      parseInt(targetId.value),
    );
    setGame(await AdminAPI.getGame(props.gameId));
    message.value = `Moved ${res.moved} activities`;
    emit("changed");
  } catch (e: any) {
    error.value = e.message;
  }
}

async function deleteGame() {
  if (!deleteArmed.value) {
    deleteArmed.value = true;
    return;
  }
  try {
    error.value = "";
    await AdminAPI.deleteGame(props.gameId);
    emit("deleted");
  } catch (e: any) {
    deleteArmed.value = false;
    error.value = e.message;
  }
}

onMounted(async () => {
  try {
    setGame(await AdminAPI.getGame(props.gameId));
    // only on load, so saving doesn't overwrite what's been typed
    igdbQuery.value = game.value?.name ?? "";
    sgdbQuery.value = game.value?.name ?? "";
  } catch (e: any) {
    error.value = e.message;
  }
});
</script>

<template>
  <div class="card">
    <div class="card-header d-flex align-items-center gap-2">
      <strong class="me-auto">
        <template v-if="game">{{ game.name }} ({{ game.id }})</template>
        <template v-else>Game {{ gameId }}</template>
      </strong>
      <button class="btn-close" @click="emit('close')"></button>
    </div>
    <div class="card-body">
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="message" class="alert alert-success py-2">{{ message }}</div>

      <template v-if="game">
        <AdminSectionTabs
          v-model="section"
          :tabs="[
            {
              id: 'details',
              label: 'Details',
              unsaved: unsavedLabels.length,
            },
            { id: 'history', label: `History (${game.history.length})` },
          ]"
        />
        <template v-if="section === 'details'">
          <div class="d-flex flex-wrap gap-2 mb-3">
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/game/${game.id}`"
              >Game page</a
            >
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/admin?tab=activities&game=${game.id}`"
              >Activities ({{ game.activity_count }})</a
            >
            <a
              v-if="game.parent_id"
              class="btn btn-outline-secondary btn-sm"
              href="#"
              @click.prevent="emit('select', game.parent_id)"
              >Parent ({{ game.parent_id }})</a
            >
            <a
              v-for="c in game.children_ids"
              :key="c"
              class="btn btn-outline-secondary btn-sm"
              href="#"
              @click.prevent="emit('select', c)"
              >Child ({{ c }})</a
            >
          </div>

          <h6>Details</h6>
          <div class="row g-2 mb-2">
            <div class="col-12 col-md-6">
              <label class="form-label small mb-0">Name</label>
              <input
                v-model="form.name"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'name' in patch }"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Release year</label>
              <input
                v-model="form.release_year"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'release_year' in patch }"
                type="number"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Parent game ID</label>
              <input
                v-model="form.parent_id"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'parent_id' in patch }"
                type="number"
              />
            </div>
            <div class="col-12 col-md-6">
              <label class="form-label small mb-0">
                Image URL (overrides SGDB/IGDB cover, <code>-</code> disables
                cover)
              </label>
              <input
                v-model="form.image_url"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'image_url' in patch }"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Steam ID</label>
              <input
                v-model="form.steam_id"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'steam_id' in patch }"
                type="number"
              />
            </div>
            <div class="col-6 col-md-3 d-flex align-items-end">
              <div class="form-check">
                <input
                  id="game-hidden"
                  v-model="form.hidden"
                  class="form-check-input"
                  :class="{ 'border-warning': 'hidden' in patch }"
                  type="checkbox"
                />
                <label class="form-check-label" for="game-hidden">Hidden</label>
              </div>
            </div>
          </div>
          <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
            <button class="btn btn-primary btn-sm" @click="save">Save</button>
            <AdminUnsaved :labels="unsavedLabels" />
          </div>

          <h6>IGDB</h6>
          <div class="input-group input-group-sm mb-2">
            <input
              v-model="igdbId"
              class="form-control"
              type="number"
              placeholder="IGDB ID"
            />
            <button
              class="btn btn-outline-primary"
              @click="setIGDB(toNumberOrNull(igdbId))"
            >
              Set
            </button>
            <button
              class="btn btn-outline-secondary"
              :disabled="!game.igdb_id"
              title="Fill in name and release year from IGDB"
              @click="refreshFromIGDB"
            >
              Refresh from IGDB
            </button>
          </div>
          <div class="input-group input-group-sm mb-2">
            <input
              v-model="igdbQuery"
              class="form-control"
              type="search"
              placeholder="Search IGDB"
              @keydown.enter.prevent="searchIGDB"
            />
            <button class="btn btn-outline-secondary" @click="searchIGDB">
              Search
            </button>
          </div>
          <ul v-if="igdbResults" class="list-group list-group-flush small mb-2">
            <li v-if="igdbResults.length === 0" class="list-group-item px-0">
              No results
            </li>
            <li
              v-for="r in igdbResults"
              :key="r.id"
              class="list-group-item px-0 d-flex align-items-center gap-2"
            >
              <span class="me-auto">
                <a :href="r.url" target="_blank">{{ r.name }}</a>
                ({{ year(r.first_release_date) }}) - {{ r.id }}
              </span>
              <button
                class="btn btn-outline-primary btn-sm"
                @click="setIGDB(r.id)"
              >
                Use
              </button>
            </li>
          </ul>

          <h6>SGDB</h6>
          <div class="input-group input-group-sm mb-2">
            <input
              v-model="sgdbId"
              class="form-control"
              type="number"
              placeholder="SGDB ID (0 = not in SGDB)"
            />
            <button
              class="btn btn-outline-primary"
              @click="setSGDB(toNumberOrNull(sgdbId))"
            >
              Set
            </button>
          </div>
          <div class="input-group input-group-sm mb-2">
            <input
              v-model="sgdbQuery"
              class="form-control"
              type="search"
              placeholder="Search SGDB"
              @keydown.enter.prevent="searchSGDB"
            />
            <button class="btn btn-outline-secondary" @click="searchSGDB">
              Search
            </button>
          </div>
          <ul v-if="sgdbResults" class="list-group list-group-flush small mb-2">
            <li v-if="sgdbResults.length === 0" class="list-group-item px-0">
              No results
            </li>
            <li
              v-for="r in sgdbResults"
              :key="r.id"
              class="list-group-item px-0 d-flex align-items-center gap-2"
            >
              <span class="me-auto">
                <a
                  :href="`https://www.steamgriddb.com/game/${r.id}`"
                  target="_blank"
                  >{{ r.name }}</a
                >
                ({{ year(r.release_date) }}) - {{ r.id }}
                <i v-if="r.verified" class="bi bi-patch-check-fill"></i>
              </span>
              <button
                class="btn btn-outline-primary btn-sm"
                @click="setSGDB(r.id)"
              >
                Use
              </button>
            </li>
          </ul>

          <h6 class="mt-3">Aliases</h6>
          <div class="d-flex flex-wrap gap-1 mb-2">
            <span v-if="game.aliases.length === 0" class="text-body-secondary"
              >No aliases</span
            >
            <span
              v-for="a in game.aliases"
              :key="a"
              class="badge text-bg-secondary d-inline-flex align-items-center gap-1"
            >
              {{ a }}
              <button
                class="btn-close btn-close-white"
                aria-label="Remove alias"
                @click="removeAlias(a)"
              ></button>
            </span>
          </div>
          <div class="input-group input-group-sm mb-3">
            <input
              v-model="newAlias"
              class="form-control"
              placeholder="New alias (case sensitive)"
              @keydown.enter.prevent="addAlias"
            />
            <button class="btn btn-outline-primary" @click="addAlias">
              Add
            </button>
          </div>

          <h6>Merge / move activities</h6>
          <div class="input-group input-group-sm mb-2">
            <input
              v-model="targetId"
              class="form-control"
              type="number"
              placeholder="Target game ID"
            />
            <button
              class="btn btn-outline-danger"
              :disabled="!targetId"
              @click="previewMerge"
            >
              Merge into
            </button>
            <button
              class="btn btn-outline-danger"
              :disabled="!targetId"
              @click="moveActivities"
            >
              {{ moveArmed ? "Really move all?" : "Move activities" }}
            </button>
          </div>
          <div v-if="mergePreview" class="alert alert-warning small">
            {{ mergePreview.activity_count }} activities will be moved to game
            {{ targetId
            }}<template v-if="mergePreview.new_aliases.length"
              >, {{ mergePreview.new_aliases.join(", ") }} added as
              alias</template
            >, and this game is deleted.
            <div class="mt-2">
              <button class="btn btn-danger btn-sm" @click="merge">
                Confirm merge
              </button>
            </div>
          </div>

          <div class="mb-3">
            <button class="btn btn-outline-danger btn-sm" @click="deleteGame">
              {{ deleteArmed ? "Really delete?" : "Delete game" }}
            </button>
            <span class="text-body-secondary small ms-2"
              >Only games without activities can be deleted</span
            >
          </div>
        </template>

        <AdminHistory v-else :history="game.history" />
      </template>
    </div>
  </div>
</template>

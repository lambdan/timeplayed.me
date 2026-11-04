<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  AdminAPI,
  type AdminPlatform,
  type AdminPlatformPatch,
} from "../../admin.client";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import { iso8601Date } from "../../utils";
import AdminHistory from "./AdminHistory.vue";
import AdminSectionTabs from "./AdminSectionTabs.vue";
import AdminUnsaved from "./AdminUnsaved.vue";
import {
  confirmDiscard,
  useUnsavedChanges,
} from "../../composables/useUnsavedChanges";
import { unsavedFieldLabels } from "../../utils.admin";
import { clearCachedPlatform } from "../../utils.cache";

const platforms = ref<AdminPlatform[]>([]);
const newAbbreviation = ref("");
const error = ref("");
const message = ref("");

const selectedId = ref<number>();
const selected = computed(() =>
  platforms.value.find((p) => p.id === selectedId.value),
);
const deleteArmed = ref(false);
const section = ref("details");
const form = ref({
  abbreviation: "",
  name: "",
  color_primary: "",
  color_secondary: "",
  icon: "",
});

// how the badge would look with the unsaved form values
const preview = computed(() => {
  if (!selected.value) return undefined;
  return {
    ...selected.value,
    abbreviation: form.value.abbreviation,
    name: form.value.name || null,
    color_primary: form.value.color_primary.replace("#", "") || null,
    color_secondary: form.value.color_secondary.replace("#", "") || null,
    icon: form.value.icon || null,
  };
});

async function fetchPlatforms() {
  try {
    error.value = "";
    platforms.value = await AdminAPI.getPlatforms();
  } catch (e: any) {
    error.value = e.message;
  }
}

function select(p?: AdminPlatform) {
  // another platform (or closing) throws away what's in the form
  if (p?.id !== selectedId.value && !confirmDiscard()) return;
  selectedId.value = p?.id;
  deleteArmed.value = false;
  message.value = "";
  if (!p) return;
  // the editor is above the list
  window.scrollTo({ top: 0, behavior: "smooth" });
  resetForm(p);
}

/** form back to the saved values */
function resetForm(p: AdminPlatform) {
  form.value = {
    abbreviation: p.abbreviation,
    name: p.name ?? "",
    color_primary: p.color_primary ? "#" + p.color_primary : "",
    color_secondary: p.color_secondary ? "#" + p.color_secondary : "",
    icon: p.icon ?? "",
  };
}

function replace(updated: AdminPlatform) {
  platforms.value = platforms.value.map((p) =>
    p.id === updated.id ? updated : p,
  );
}

/** fields in the form that differ from the saved platform, this is what save sends */
const patch = computed(() => {
  const changed: AdminPlatformPatch = {};
  const p = selected.value;
  if (!p) return changed;
  if (form.value.abbreviation !== p.abbreviation)
    changed.abbreviation = form.value.abbreviation;
  if ((form.value.name || null) !== p.name) changed.name = form.value.name;
  if (preview.value?.color_primary !== p.color_primary)
    changed.color_primary = form.value.color_primary || null;
  if (preview.value?.color_secondary !== p.color_secondary)
    changed.color_secondary = form.value.color_secondary || null;
  if ((form.value.icon || null) !== p.icon) changed.icon = form.value.icon;
  return changed;
});

const FIELD_LABELS: Record<keyof AdminPlatformPatch, string> = {
  abbreviation: "abbreviation",
  name: "name",
  color_primary: "primary color",
  color_secondary: "secondary color",
  icon: "icon",
};

const unsavedLabels = computed(() =>
  unsavedFieldLabels(patch.value, FIELD_LABELS),
);
useUnsavedChanges("platform", () => unsavedLabels.value);

function revert() {
  if (selected.value) resetForm(selected.value);
}

async function save() {
  const p = selected.value;
  if (!p) return;
  try {
    error.value = "";
    const updated = await AdminAPI.patchPlatform(p.id, patch.value);
    // so public pages in this tab show the change
    clearCachedPlatform(updated.id);
    replace(updated);
    select(updated);
    message.value = "Saved";
  } catch (e: any) {
    error.value = e.message;
  }
}

async function deletePlatform() {
  const p = selected.value;
  if (!p) return;
  if (!deleteArmed.value) {
    deleteArmed.value = true;
    return;
  }
  try {
    error.value = "";
    await AdminAPI.deletePlatform(p.id);
    select(undefined);
    fetchPlatforms();
  } catch (e: any) {
    deleteArmed.value = false;
    error.value = e.message;
  }
}

async function addPlatform() {
  const abbreviation = newAbbreviation.value.trim();
  if (!abbreviation) return;
  try {
    error.value = "";
    const platform = await AdminAPI.addPlatform(abbreviation);
    newAbbreviation.value = "";
    platforms.value.push(platform);
    select(platform);
  } catch (e: any) {
    error.value = e.message;
  }
}

onMounted(fetchPlatforms);
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="selected && preview" class="card p-0 mb-3">
      <div class="card-header d-flex align-items-center gap-2">
        <strong class="me-auto"
          >{{ selected.display_name }} ({{ selected.id }})</strong
        >
        <button class="btn-close" @click="select(undefined)"></button>
      </div>
      <div class="card-body p-2 p-md-3">
        <AdminSectionTabs
          v-model="section"
          :tabs="[
            { id: 'details', label: 'Details', unsaved: unsavedLabels.length },
            { id: 'history', label: `History (${selected.history.length})` },
          ]"
        />
        <template v-if="section === 'details'">
          <div v-if="message" class="alert alert-success py-2">
            {{ message }}
          </div>
          <div class="mb-3">
            <PlatformBadge :platform="preview" />
          </div>
          <div class="row g-2 mb-2">
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Abbreviation</label>
              <input
                v-model="form.abbreviation"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'abbreviation' in patch }"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Name</label>
              <input
                v-model="form.name"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'name' in patch }"
              />
            </div>
            <div class="col-12 col-md-6">
              <label class="form-label small mb-0">
                Icon (<a href="https://icons.getbootstrap.com/" target="_blank"
                  >Bootstrap icon</a
                >
                name without <code>bi-</code>)
              </label>
              <input
                v-model="form.icon"
                class="form-control form-control-sm"
                :class="{ 'border-warning': 'icon' in patch }"
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Primary color</label>
              <div class="input-group input-group-sm">
                <input
                  v-model="form.color_primary"
                  class="form-control form-control-color"
                  :class="{ 'border-warning': 'color_primary' in patch }"
                  type="color"
                />
                <button
                  class="btn btn-outline-secondary"
                  @click="form.color_primary = ''"
                >
                  Clear
                </button>
              </div>
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Secondary color</label>
              <div class="input-group input-group-sm">
                <input
                  v-model="form.color_secondary"
                  class="form-control form-control-color"
                  :class="{ 'border-warning': 'color_secondary' in patch }"
                  type="color"
                />
                <button
                  class="btn btn-outline-secondary"
                  @click="form.color_secondary = ''"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
          <div class="d-flex flex-wrap gap-2 mb-3">
            <button class="btn btn-primary btn-sm" @click="save">Save</button>
            <AdminUnsaved :labels="unsavedLabels" @revert="revert" />
            <button
              class="btn btn-outline-danger btn-sm"
              @click="deletePlatform"
            >
              {{ deleteArmed ? "Really delete?" : "Delete platform" }}
            </button>
          </div>
        </template>
        <AdminHistory v-else :history="selected.history" />
      </div>
    </div>

    <div class="input-group mb-2">
      <input
        v-model="newAbbreviation"
        class="form-control"
        placeholder="New platform abbreviation"
        @keydown.enter.prevent="addPlatform"
      />
      <button class="btn btn-outline-primary" @click="addPlatform">Add</button>
    </div>

    <div class="table-responsive">
      <table class="table table-hover table-sm align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Platform</th>
            <th>Abbreviation</th>
            <th class="d-none d-md-table-cell">Last played</th>
            <th class="text-end">Activities</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in platforms"
            :key="p.id"
            role="button"
            :class="{ 'table-active': selectedId === p.id }"
            @click="select(p)"
          >
            <td>{{ p.id }}</td>
            <td><PlatformBadge :platform="p" /></td>
            <td>{{ p.abbreviation }}</td>
            <td class="d-none d-md-table-cell text-nowrap">
              {{ p.last_activity ? iso8601Date(p.last_activity) : "-" }}
            </td>
            <td class="text-end">{{ p.activity_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

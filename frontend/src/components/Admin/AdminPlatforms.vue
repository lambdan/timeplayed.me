<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  AdminAPI,
  type AdminPlatform,
  type AdminPlatformPatch,
} from "../../admin.client";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import AdminHistory from "./AdminHistory.vue";
import AdminSectionTabs from "./AdminSectionTabs.vue";

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
  selectedId.value = p?.id;
  deleteArmed.value = false;
  message.value = "";
  if (!p) return;
  // the editor is above the list
  window.scrollTo({ top: 0, behavior: "smooth" });
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

async function save() {
  const p = selected.value;
  if (!p) return;
  const patch: AdminPlatformPatch = {};
  if (form.value.abbreviation !== p.abbreviation)
    patch.abbreviation = form.value.abbreviation;
  if ((form.value.name || null) !== p.name) patch.name = form.value.name;
  if (preview.value?.color_primary !== p.color_primary)
    patch.color_primary = form.value.color_primary || null;
  if (preview.value?.color_secondary !== p.color_secondary)
    patch.color_secondary = form.value.color_secondary || null;
  if ((form.value.icon || null) !== p.icon) patch.icon = form.value.icon;
  try {
    error.value = "";
    const updated = await AdminAPI.patchPlatform(p.id, patch);
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

    <div v-if="selected && preview" class="card mb-3">
      <div class="card-header d-flex align-items-center gap-2">
        <strong class="me-auto"
          >{{ selected.display_name }} ({{ selected.id }})</strong
        >
        <button class="btn-close" @click="select(undefined)"></button>
      </div>
      <div class="card-body">
        <AdminSectionTabs
          v-model="section"
          :tabs="[
            { id: 'details', label: 'Details' },
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
              />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Name</label>
              <input v-model="form.name" class="form-control form-control-sm" />
            </div>
            <div class="col-12 col-md-6">
              <label class="form-label small mb-0">
                Icon (<a href="https://icons.getbootstrap.com/" target="_blank"
                  >Bootstrap icon</a
                >
                name without <code>bi-</code>)
              </label>
              <input v-model="form.icon" class="form-control form-control-sm" />
            </div>
            <div class="col-6 col-md-3">
              <label class="form-label small mb-0">Primary color</label>
              <div class="input-group input-group-sm">
                <input
                  v-model="form.color_primary"
                  class="form-control form-control-color"
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
            <td class="text-end">{{ p.activity_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  AdminAPI,
  type AdminDiscordHistory,
  type AdminUser,
  type AdminUserDetails,
} from "../../admin.client";
import { formatDate } from "../../utils";
import AdminHistory from "./AdminHistory.vue";
import AdminSectionTabs from "./AdminSectionTabs.vue";

const PAGE_SIZE = 100;

const route = useRoute();
const router = useRouter();

const users = ref<AdminUser[]>([]);
const hasMore = ref(false);
const search = ref("");
const allPermissions = ref<string[]>([]);
const error = ref("");

const selected = ref<AdminUserDetails>();
const permissions = ref<string[]>([]);
const discordHistory = ref<AdminDiscordHistory[]>([]);
// only the newest page is fetched, a full page means there's more
const discordHistoryCount = computed(() =>
  discordHistory.value.length === PAGE_SIZE
    ? `${PAGE_SIZE}+`
    : discordHistory.value.length,
);
const deleteArmed = ref(false);
const message = ref("");
const section = ref("details");

async function fetchUsers(append = false) {
  try {
    error.value = "";
    const offset = append ? users.value.length : 0;
    const page = await AdminAPI.getUsers({
      search: search.value.trim(),
      offset,
      limit: PAGE_SIZE,
    });
    users.value = append ? [...users.value, ...page] : page;
    hasMore.value = page.length === PAGE_SIZE;
  } catch (e: any) {
    error.value = e.message;
  }
}

async function loadSelected() {
  const id = parseInt(route.query.id as string);
  deleteArmed.value = false;
  message.value = "";
  if (!id) {
    selected.value = undefined;
    return;
  }
  try {
    error.value = "";
    selected.value = await AdminAPI.getUser(id);
    permissions.value = [...selected.value.permissions];
    discordHistory.value = await AdminAPI.getDiscordHistory(id);
  } catch (e: any) {
    error.value = e.message;
  }
}

function select(id?: number) {
  router.replace({ query: { tab: "users", id } });
}

async function savePermissions() {
  if (!selected.value) return;
  try {
    error.value = "";
    selected.value = await AdminAPI.setPermissions(
      selected.value.id,
      permissions.value,
    );
    message.value = "Permissions saved";
    fetchUsers();
  } catch (e: any) {
    error.value = e.message;
  }
}

async function deleteUser() {
  if (!selected.value) return;
  if (!deleteArmed.value) {
    deleteArmed.value = true;
    return;
  }
  try {
    error.value = "";
    await AdminAPI.deleteUser(selected.value.id);
    select(undefined);
    fetchUsers();
  } catch (e: any) {
    error.value = e.message;
  }
}

let searchTimeout: ReturnType<typeof setTimeout>;
watch(search, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => fetchUsers(), 200);
});
watch(() => route.query.id, loadSelected);

onMounted(async () => {
  fetchUsers();
  loadSelected();
  allPermissions.value = await AdminAPI.getPermissions();
});
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="selected" class="card mb-3">
      <div class="card-header d-flex align-items-center gap-2">
        <strong class="me-auto">
          {{ selected.display_name }}
          <span class="text-body-secondary">({{ selected.name }})</span>
        </strong>
        <button class="btn-close" @click="select(undefined)"></button>
      </div>
      <div class="card-body">
        <AdminSectionTabs
          v-model="section"
          :tabs="[
            { id: 'details', label: 'Details' },
            { id: 'history', label: `History (${selected.history.length})` },
            {
              id: 'discord',
              label: `Discord history (${discordHistoryCount})`,
            },
          ]"
        />

        <template v-if="section === 'details'">
          <dl class="row mb-3">
            <dt class="col-sm-3">ID</dt>
            <dd class="col-sm-9">{{ selected.id }}</dd>
            <dt class="col-sm-3">Discord ID</dt>
            <dd class="col-sm-9">{{ selected.discord_id ?? "-" }}</dd>
            <dt class="col-sm-3">Created</dt>
            <dd class="col-sm-9">{{ formatDate(selected.created) }}</dd>
            <dt class="col-sm-3">Activities</dt>
            <dd class="col-sm-9">
              {{ selected.activity_count }}
              <a :href="`/admin?tab=activities&user=${selected.id}`"
                >(manage)</a
              >
            </dd>
          </dl>
          <div class="d-flex gap-2 mb-3">
            <a
              class="btn btn-outline-secondary btn-sm"
              :href="`/user/${selected.id}`"
              >User page</a
            >
          </div>

          <h6>Permissions</h6>
          <div class="mb-2">
            <div
              v-for="p in allPermissions"
              :key="p"
              class="form-check form-check-inline"
            >
              <input
                :id="`perm-${p}`"
                v-model="permissions"
                class="form-check-input"
                type="checkbox"
                :value="p"
              />
              <label class="form-check-label" :for="`perm-${p}`">{{ p }}</label>
            </div>
          </div>
          <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
            <button class="btn btn-primary btn-sm" @click="savePermissions">
              Save permissions
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="deleteUser">
              {{
                deleteArmed
                  ? `Really delete user and ${selected.activity_count} activities?`
                  : "Delete user"
              }}
            </button>
            <span v-if="message" class="text-success small">{{ message }}</span>
          </div>
        </template>

        <AdminHistory
          v-else-if="section === 'history'"
          :history="selected.history"
        />

        <template v-else-if="section === 'discord'">
          <div class="text-body-secondary small mb-2">
            Last 30 days, newest first
          </div>
          <div v-if="discordHistory.length === 0" class="text-body-secondary">
            No Discord history
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm small">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Event</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in discordHistory" :key="e.id">
                  <td class="text-nowrap">{{ formatDate(e.timestamp) }}</td>
                  <td class="text-nowrap">{{ e.event }}</td>
                  <td class="font-monospace text-break">{{ e.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <input
      v-model="search"
      class="form-control mb-2"
      type="search"
      placeholder="Search users"
    />
    <div class="table-responsive">
      <table class="table table-hover table-sm align-middle">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th class="d-none d-md-table-cell">Discord ID</th>
            <th class="d-none d-sm-table-cell">Permissions</th>
            <th class="text-end">Activities</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in users"
            :key="u.id"
            role="button"
            :class="{ 'table-active': selected?.id === u.id }"
            @click="select(u.id)"
          >
            <td>{{ u.id }}</td>
            <td>
              {{ u.display_name }}
              <span class="text-body-secondary small">{{ u.name }}</span>
            </td>
            <td class="d-none d-md-table-cell">{{ u.discord_id ?? "-" }}</td>
            <td class="d-none d-sm-table-cell">
              <span
                v-for="p in u.permissions"
                :key="p"
                class="badge me-1"
                :class="p === 'admin' ? 'text-bg-danger' : 'text-bg-secondary'"
                >{{ p }}</span
              >
            </td>
            <td class="text-end">{{ u.activity_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <button
      v-if="hasMore"
      class="btn btn-outline-secondary btn-sm"
      @click="fetchUsers(true)"
    >
      Load more
    </button>
  </div>
</template>

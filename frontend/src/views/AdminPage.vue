<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthenticatedUser } from "../composables/useAuthenticatedUser";
import AdminUsers from "../components/Admin/AdminUsers.vue";
import AdminGames from "../components/Admin/AdminGames.vue";
import AdminActivities from "../components/Admin/AdminActivities.vue";
import AdminPlatforms from "../components/Admin/AdminPlatforms.vue";
import AdminMaintenance from "../components/Admin/AdminMaintenance.vue";

const TABS = [
  { id: "users", label: "Users", icon: "bi-people-fill" },
  { id: "games", label: "Games", icon: "bi-controller" },
  { id: "activities", label: "Activities", icon: "bi-clock-history" },
  { id: "platforms", label: "Platforms", icon: "bi-display" },
  { id: "maintenance", label: "Maintenance", icon: "bi-tools" },
];

const route = useRoute();
const router = useRouter();
const { isAdmin, loadingAuthenticatedUser } = useAuthenticatedUser();

const tab = computed(() => {
  const t = route.query.tab;
  return TABS.some((x) => x.id === t) ? (t as string) : "users";
});

function selectTab(id: string) {
  router.replace({ query: { tab: id } });
}
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Admin</h1>
    <div class="card-body">
      <div v-if="loadingAuthenticatedUser" class="text-body-secondary">
        Loading...
      </div>
      <div v-else-if="!isAdmin" class="alert alert-warning mb-0">
        Admin permission required.
        <a href="/authenticate">Authenticate</a> with an admin account.
      </div>
      <template v-else>
        <ul class="nav nav-tabs mb-3 flex-nowrap overflow-x-auto">
          <li v-for="t in TABS" :key="t.id" class="nav-item">
            <a
              class="nav-link text-nowrap"
              :class="{ active: tab === t.id }"
              href="#"
              @click.prevent="selectTab(t.id)"
            >
              <i class="bi" :class="t.icon"></i> {{ t.label }}
            </a>
          </li>
        </ul>
        <AdminUsers v-if="tab === 'users'" />
        <AdminGames v-else-if="tab === 'games'" />
        <AdminActivities v-else-if="tab === 'activities'" />
        <AdminPlatforms v-else-if="tab === 'platforms'" />
        <AdminMaintenance v-else-if="tab === 'maintenance'" />
      </template>
    </div>
  </div>
</template>

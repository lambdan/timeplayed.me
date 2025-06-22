<script setup lang="ts">
import { onMounted, ref } from "vue";

import type { API_Users, User } from "../models/models";
import UserTable from "./UserTable.vue";

const props = withDefaults(
  defineProps<{ limit?: number; showExpand?: boolean }>(),
  {
    limit: 25,
    showExpand: false,
  }
);

const users = ref<User[]>([]);
const offset = ref(0);
const loading = ref(false);
const hasMore = ref(true);

async function fetchUsers(limit?: number, offsetVal = 0) {
  const params = [];

  if (limit) {
    params.push(`limit=${limit}`);
  }
  if (offsetVal) {
    params.push(`offset=${offsetVal}`);
  }
  params.push("sort=last_active");
  params.push("order=desc");

  loading.value = true;
  const res = await fetch(`/api/users?${params.join("&")}`);
  const data: API_Users = await res.json();

  const newUsers = data.data.map((user: User) => ({
    ...user,
  }));

  if (offsetVal === 0) {
    users.value = newUsers;
  } else {
    users.value = [...users.value, ...newUsers];
  }

  hasMore.value = data._total > offsetVal + newUsers.length;
  loading.value = false;
}

function loadMore() {
  offset.value += props.limit;
  fetchUsers(props.limit, offset.value);
}

onMounted(() => {
  fetchUsers(props.limit, 0);
});
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Users</h1>
    <div class="card-body">
      <div class="row table-responsive">
        <UserTable :users="users" :showExpand="props.showExpand" />
      </div>
      <div class="text-center my-2">
        <button v-if="loading" class="btn btn-primary" type="button" disabled>
          <span
            class="spinner-grow spinner-grow-sm"
            role="status"
            aria-hidden="true"
          ></span>
          Loading...
        </button>
        <button
          v-else-if="hasMore"
          class="btn btn-primary"
          :disabled="loading"
          @click="loadMore"
        >
          Load More
        </button>
      </div>
    </div>
  </div>
</template>

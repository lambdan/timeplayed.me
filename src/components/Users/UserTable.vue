<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import ColorSpinners from "../Misc/ColorSpinners.vue";
import { sleep } from "../../utils";
import type { API_Users, Game, UserWithStats } from "../../models/models";
import UserRow from "./UserRow.vue";
const props = withDefaults(
  defineProps<{
    game?: Game;
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    game: undefined,
  }
);

const users = ref<UserWithStats[]>([]);
const loading = ref(false);
const localSort = ref(props.sort);
const localOrder = ref(props.order);

async function fetchUsers() {
  loading.value = true;
  users.value = [];
  const fetchedUsers: UserWithStats[] = [];
  let res = await fetch(`/api/users?limit=1`);
  let data = (await res.json()) as API_Users;
  fetchedUsers.push(...data.data);
  while (fetchedUsers.length < data._total) {
    res = await fetch(`/api/users?offset=${fetchedUsers.length}&limit=1`);
    data = (await res.json()) as API_Users;
    fetchedUsers.push(...data.data);
  }
  users.value = fetchedUsers;
  sort();
  loading.value = false;
}

async function fetchTopPlayers() {
  loading.value = true;
  users.value = [];
  const fetchedUsers: UserWithStats[] = [];
  let res = await fetch(`/api/games/${props.game?.id}/players`);
  let data = (await res.json()) as UserWithStats[];
  await sleep(200); // I like the way it looks
  fetchedUsers.push(...data);
  users.value = fetchedUsers;
  sort();
  loading.value = false;
}

function sort() {
  if (localSort.value === "recency") {
    users.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.last_played - b.last_played
        : b.last_played - a.last_played;
    });
  } else if (localSort.value === "playtime") {
    users.value.sort((a, b) => {
      return localOrder.value === "asc"
        ? a.total_playtime - b.total_playtime
        : b.total_playtime - a.total_playtime;
    });
  } else if (localSort.value === "name") {
    users.value.sort((a, b) => {
      const a_name = a.user.name;
      const b_name = b.user.name;
      return localOrder.value === "asc"
        ? a_name.localeCompare(b_name)
        : b_name.localeCompare(a_name);
    });
  }
}

watch([() => props.sort, () => props.order], ([newSort, newOrder]) => {
  localSort.value = newSort;
  localOrder.value = newOrder;
  sort();
});

onMounted(() => {
  if (props.game) {
    fetchTopPlayers();
  } else {
    fetchUsers();
  }
});
</script>

<template>
  <ColorSpinners v-if="loading" />
  <template v-else-if="users.length > 0">
    <table class="table table-responsive table-hover">
      <thead>
        <tr>
          <th></th>
          <th>Name</th>
          <th>Last played</th>
          <th>Total playtime</th>
        </tr>
      </thead>
      <tbody>
        <UserRow
          v-for="user in users"
          :key="user.user.id"
          :user="user"
          :showExpand="props.showExpand"
        />
      </tbody>
    </table>
  </template>
  <div v-else class="text-center text-muted">No platforms found.</div>
</template>

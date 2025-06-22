<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { User, UserStats } from "../models/models";
import { formatDate, formatDuration, timeAgo } from "../utils";

const FALLBACK_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png";

const props = withDefaults(
  defineProps<{ user: User; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);

const stats = ref<UserStats>();

const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {
  const res = await fetch(`/api/users/${props.user.id}/stats`);
  const data: UserStats = await res.json();
  stats.value = data;
});
</script>

<template>
  <tr class="align-middle">
    <td class="col-lg-1">
      <a :href="`/user/${user.id}`">
        <img
          :src="user.avatar_url ?? FALLBACK_AVATAR"
          class="img-thumbnail img-fluid rounded-circle"
        />
      </a>
    </td>

    <td>
      <a :href="`/user/${user.id}`">{{ user.name }}</a>
    </td>

    <td>
      {{ timeAgo(new Date(user.last_active + "Z")) }}

      <br />
      <small class="text-muted">{{
        formatDate(new Date(user.last_active + "Z"))
      }}</small>
    </td>

    <td>{{ stats?.total.games }}</td>

    <td v-if="stats">{{ formatDuration(stats.total.seconds) }}</td>

    <td>
      <small v-if="expanded" class="text-muted">
        User ID {{ user.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

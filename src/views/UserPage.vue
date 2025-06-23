<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameListCard from "../components/Games/GameListCard.vue";
import UserInfoCard from "../components/UserInfoCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { type UserWithStats } from "../models/models";
import { useRoute } from "vue-router";

const route = useRoute();
const apiUser = ref<UserWithStats>();

onMounted(async () => {
  const userId = route.params.id as string;
  const userRes = await fetch(`/api/users/${userId}`);
  apiUser.value = await userRes.json();
});
</script>

<template>
  <UserInfoCard class="mb-4" v-if="apiUser" :user="apiUser.user" />
  <RecentActivityCard
    v-if="apiUser"
    :limit="5"
    :user="apiUser.user"
    :showExpand="true"
    class="mb-4"
  />
  <GameListCard
    v-if="apiUser"
    class="mb-4"
    :showExpand="false"
    :limit="5"
    :order="'desc'"
    :sort="'playtime'"
    :user="apiUser.user"
  ></GameListCard>
</template>

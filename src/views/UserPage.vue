<script setup lang="ts">
import { onMounted, ref } from "vue";
import GameListCard from "../components/GameListCard.vue";
import UserInfoCard from "../components/UserInfoCard.vue";
import RecentActivityCard from "../components/RecentActivityCard.vue";
import { type User } from "../models/models";
import { useRoute } from "vue-router";

const route = useRoute();
const user = ref<User>();

onMounted(async () => {
  const userId = route.params.id as string;
  const userRes = await fetch(`/api/users/${userId}`);
  user.value = await userRes.json();
});
</script>

<template>
  <UserInfoCard class="mb-4" v-if="user" :user="user" />
  <GameListCard
    v-if="user"
    class="mb-4"
    :showExpand="false"
    :limit="10"
    :order="'desc'"
    :sort="'playtime'"
    :user="user"
  ></GameListCard>
  <RecentActivityCard v-if="user" :limit="10" :user="user" :showExpand="true" />
</template>

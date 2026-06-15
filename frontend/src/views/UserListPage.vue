<script setup lang="ts">
import { useRoute } from "vue-router";

import UserListCard from "../components/Users/UserListCard.vue";

const route = useRoute();
</script>

<template>
  <div class="justify-content-center mx-auto p-0">
    <UserListCard :showExpand="false" :sort="'playtime'"></UserListCard>
  </div>
</template>

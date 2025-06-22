<script setup lang="ts">
import { useRoute } from "vue-router";

import UserListCard from "../components/UserListCard.vue";

const route = useRoute();
</script>

<template>
  <UserListCard :showExpand="false" :limit="25"></UserListCard>
</template>

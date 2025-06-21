<script setup lang="ts">
import { useRoute } from "vue-router";
import RecentActivity from "../components/RecentActivity.vue";

const route = useRoute();
const userId = route.params.id as string;
</script>

<template>
  <RecentActivity :user="userId" />
</template>

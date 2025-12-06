<script setup lang="ts">
import { onMounted, ref } from "vue";
import { type UserWithStats } from "../models/models";
import { useRoute } from "vue-router";

const route = useRoute();

const refYear = ref<number>();
const refUserId = ref<string>();

onMounted(async () => {
  const userId = route.params.id as string;
  const year = parseInt(route.params.year as string);
  refUserId.value = userId;
  refYear.value = year;
});
</script>

<template>
  <h1>Hello</h1>
  <h1>User ID: {{ refUserId }}</h1>
  <h1>Year: {{ refYear }}</h1>
</template>
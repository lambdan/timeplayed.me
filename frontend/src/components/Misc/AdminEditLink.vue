<script setup lang="ts">
import { useAuthenticatedUser } from "../../composables/useAuthenticatedUser";

defineProps<{
  tab: "games" | "users" | "platforms" | "activities";
  id: number;
}>();

const { isAdmin } = useAuthenticatedUser();
</script>

<template>
  <a
    v-if="isAdmin"
    :href="`/admin?tab=${tab}&id=${id}`"
    class="btn btn-sm btn-outline-warning"
    title="Edit in admin"
    ><i class="bi bi-pencil"></i
  ></a>
</template>

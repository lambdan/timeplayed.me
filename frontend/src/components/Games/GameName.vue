<script setup lang="ts">
import { useNsfw } from "../../composables/useNsfw";

defineProps<{ game: { name: string; nsfw?: boolean } }>();

const { gameName } = useNsfw();
</script>

<template>
  {{ gameName(game) }}
</template>

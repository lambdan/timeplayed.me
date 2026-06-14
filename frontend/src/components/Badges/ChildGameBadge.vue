<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";
import { onMounted, ref } from "vue";
import { TimeplayedAPI } from "../../api.client";
import type { Game } from "../../api.models";

const props = defineProps<{
  game: Game;
}>();

const text = ref(props.game.name);

onMounted(async () => {});
</script>

<template>
  <span class="badge bg-secondary me-1 mb-1">
    <a :href="'/game/' + game.id" class="text-white text-decoration-none">
      {{ text }}
    </a>
  </span>
</template>

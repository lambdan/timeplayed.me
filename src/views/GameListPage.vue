<script setup lang="ts">
import { useRoute } from "vue-router";

import GameListCard from "../components/Games/GameListCard.vue";

const route = useRoute();
</script>

<template>
  <GameListCard
    :showExpand="false"
    :limit="0"
    :order="'desc'"
    :sort="'recency'"
  ></GameListCard>
</template>

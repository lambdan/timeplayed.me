<script setup lang="ts">
import { useRoute } from "vue-router";

import GameListCard from "../components/GameListCard.vue";

const route = useRoute();
</script>

<template>
  <GameListCard
    :showExpand="false"
    :limit="25"
    :order="'desc'"
    :sort="'recency'"
  ></GameListCard>
</template>

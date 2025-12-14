<script setup lang="ts">
import { useRoute } from "vue-router";

import GameListCard from "../components/Games/GameListCard.vue";

const route = useRoute();
</script>

<template>
  <div class="justify-content-center mx-auto p-0">
    <GameListCard
      :showExpand="false"
      :limit="0"
      :order="'desc'"
      :sort="'recency'"
    ></GameListCard>
  </div>
</template>

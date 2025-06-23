<script setup lang="ts">
import { useRoute } from "vue-router";

import PlatformListCard from "../components/Platforms/PlatformListCard.vue";

const route = useRoute();
</script>

<template>
  <PlatformListCard
    :showExpand="false"
    :limit="25"
    :order="'desc'"
    :sort="'playtime'"
  ></PlatformListCard>
</template>

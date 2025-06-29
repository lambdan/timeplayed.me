<script setup lang="ts">
import { useRoute } from "vue-router";

import PlatformListCard from "../components/Platforms/PlatformListCard.vue";

const route = useRoute();
</script>

<template>
  <div class="col-lg-8 justify-content-center mx-auto p-0">
    <PlatformListCard
      :showExpand="false"
      :limit="25"
      :order="'desc'"
      :sort="'playtime'"
      :showSortButtons="false"
    ></PlatformListCard>
  </div>
</template>

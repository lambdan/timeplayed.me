<script setup lang="ts">
import { useRoute } from "vue-router";

import UserListCard from "../components/Users/UserListCard.vue";

const route = useRoute();
</script>

<template>
  <div class="col-lg-6 justify-content-center mx-auto p-0">
    <UserListCard
      :showExpand="false"
      :limit="25"
      :sort="'playtime'"
    ></UserListCard>
  </div>
</template>

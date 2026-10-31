<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import TopGamesList from "../components/Games/TopGamesList.vue";
import TopPlayersCard from "../components/Users/TopPlayersCard.vue";
import TopPlatformsList from "../components/Platforms/TopPlatformsList.vue";

// games, players and platforms in one place. most played first, a search narrows all three
const route = useRoute();
const router = useRouter();

const input = ref((route.query.q as string) ?? "");
const search = ref(input.value.trim());

let timeout: ReturnType<typeof setTimeout>;
function searchChanged() {
  clearTimeout(timeout);
  timeout = setTimeout(() => {
    search.value = input.value.trim();
    // in the url, so a search can be linked
    router.replace({ query: search.value ? { q: search.value } : {} });
  }, 300);
}
</script>

<template>
  <div class="row">
    <div class="col-12 p-0 mt-4">
      <div class="card p-0">
        <h1 class="card-header">Browse</h1>
        <div class="card-body">
          <input
            v-model="input"
            @input="searchChanged"
            type="search"
            class="form-control form-control-lg"
            placeholder="Search games, players and platforms"
            autofocus
          />
        </div>
      </div>
    </div>
  </div>

  <div class="row mb-4">
    <div class="col-lg-4 p-0 pe-lg-4 mt-4">
      <div class="card p-0 h-100">
        <div class="card-body">
          <TopGamesList :search="search" :limit="10" />
        </div>
        <div class="card-footer text-end">
          <a href="/games">All games</a>
        </div>
      </div>
    </div>
    <div class="col-lg-4 p-0 pe-lg-4 mt-4">
      <div class="card p-0 h-100">
        <div class="card-body">
          <TopPlayersCard :compact="true" :search="search" :limit="10" />
        </div>
        <div class="card-footer text-end">
          <a href="/users">All players</a>
        </div>
      </div>
    </div>
    <div class="col-lg-4 p-0 mt-4">
      <div class="card p-0 h-100">
        <div class="card-body">
          <TopPlatformsList :search="search" :limit="10" />
        </div>
        <div class="card-footer text-end">
          <a href="/platforms">All platforms</a>
        </div>
      </div>
    </div>
  </div>
</template>

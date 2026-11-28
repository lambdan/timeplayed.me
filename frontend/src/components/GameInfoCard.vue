<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import GameCover from "./Games/GameCover.vue";
import GameName from "./Games/GameName.vue";
import AdminEditLink from "./Misc/AdminEditLink.vue";
import type { Game, GameWithStats } from "../api.models";
import { TimeplayedAPI } from "../api.client";
import GameAliases from "./Games/GameAliases.vue";
import InfoStatTiles from "./Misc/InfoStatTiles.vue";
import GameIds from "./Games/GameIds.vue";

const props = defineProps<{
  game: GameWithStats;
  /** stats including all child games, only for games with children */
  familyStats?: GameWithStats["stats"];
}>();
const parent = ref<Game>();

// games with children show the combined numbers
const stats = computed(() => props.familyStats ?? props.game.stats);

onMounted(async () => {
  if (props.game.parent_id) {
    parent.value = await TimeplayedAPI.getGame(props.game.parent_id);
  }
});
</script>

<template>
  <div class="card">
    <h1 class="card-header d-flex align-items-center gap-2">
      <div class="me-auto">
        <GameName :game="game" />
        <span class="text-muted" v-if="game.release_year">
          ({{ game.release_year }})
        </span>
        <span class="text-muted d-block" style="font-size: 0.5em" v-if="parent">
          Counted in
          <a :href="'/game/' + parent.id"><GameName :game="parent" /></a>
        </span>
      </div>
      <AdminEditLink tab="games" :id="game.id" />
    </h1>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-12 col-sm-auto text-center">
          <GameCover
            :gameId="game.id"
            :clickable="false"
            :maxHeight="300"
            :showCredits="true"
          />
        </div>
        <div class="col">
          <InfoStatTiles
            :stats="stats"
            :counts="[
              { label: 'Users', value: stats.user_count },
              { label: 'Platforms', value: stats.platform_count },
            ]"
          />
          <GameAliases :game="game" class="mt-2" />
        </div>
      </div>
    </div>
    <!-- footer, so it's at the bottom when the card is stretched next to your stats -->
    <GameIds
      :game="game"
      class="card-footer border-0 bg-transparent pt-0 text-center small text-muted"
    />
  </div>
</template>

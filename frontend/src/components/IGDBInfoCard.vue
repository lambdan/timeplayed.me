<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, IGDBGameInfo } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const props = defineProps<{ igdbId: number }>();

const info = ref<IGDBGameInfo>();
const parent = ref<Game | null>(null);
const similarGames = ref<Game[]>([]);
const expansions = ref<Game[]>([]);
const expandedGames = ref<Game[]>([]);

onMounted(async () => {
  const f = await TimeplayedAPI.getIGDBGameInfo(props.igdbId);
  if (!f) {
    return;
  }
  info.value = f;
  const _igdbInfo = f;

  if (_igdbInfo) {
    if (_igdbInfo.parent_game) {
      parent.value = await TimeplayedAPI.getGameByIGDB(_igdbInfo.parent_game);
    }

    for (const similar_id of _igdbInfo.similar_games) {
      const similarGame = await TimeplayedAPI.getGameByIGDB(similar_id);
      if (similarGame) {
        similarGames.value.push(similarGame);
      }
    }

    for (const expansion_id of _igdbInfo.expansions) {
      const expansionGame = await TimeplayedAPI.getGameByIGDB(expansion_id);
      if (expansionGame) {
        expansions.value.push(expansionGame);
      }
    }

    for (const expanded_id of _igdbInfo.expanded_games) {
      const expandedGame = await TimeplayedAPI.getGameByIGDB(expanded_id);
      if (expandedGame) {
        expandedGames.value.push(expandedGame);
      }
    }
  }
});
</script>

<template>
  <div v-if="!info">
    <i class="fa fa-spinner fa-spin"></i>
    <p>Loading...</p>
  </div>

  <div v-if="info">
    <div class="card mt-2 p-0 h-100">
      <div class="card-body">
        <a :href="info.url">
          <h2>{{ info.name }}</h2>
        </a>
        <div v-if="info.summary">
          <h4>Summary</h4>
          <p>{{ info.summary }}</p>
        </div>

        <div v-if="parent">
          <h4>Parent Game</h4>
          <p>
            <a :href="'/game/' + parent.id">{{ parent.name }}</a>
          </p>
        </div>

        <div v-if="similarGames.length > 0">
          <h4>Similar Games</h4>

          <ul>
            <li
              v-for="similar in similarGames.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="similar.id"
            >
              <a :href="'/game/' + similar.id">{{ similar.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="expansions.length > 0">
          <h4>Expansions</h4>

          <ul>
            <li
              v-for="similar in expansions.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="similar.id"
            >
              <a :href="'/game/' + similar.id">{{ similar.name }}</a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

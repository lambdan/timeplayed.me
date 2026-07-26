<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game, IGDBGameInfo } from "../api.models";
import { TimeplayedAPI } from "../api.client";

const props = defineProps<{ igdbId: number }>();

const similarLoading = ref(false);
const expansionsLoading = ref(false);
const expandedLoading = ref(false);
const parentLoading = ref(false);
const portsLoading = ref(false);
const remakesLoading = ref(false);
const remastersLoading = ref(false);
const standaloneExpansionsLoading = ref(false);

const info = ref<IGDBGameInfo>();
const parent = ref<Game | null>(null);
const similarGames = ref<Game[]>([]);
const expansions = ref<Game[]>([]);
const expandedGames = ref<Game[]>([]);
const ports = ref<Game[]>([]);
const remakes = ref<Game[]>([]);
const remasters = ref<Game[]>([]);
const standaloneExpansions = ref<Game[]>([]);

onMounted(async () => {
  const f = await TimeplayedAPI.getIGDBGameInfo(props.igdbId);
  if (!f) {
    return;
  }
  info.value = f;
  const _igdbInfo = f;

  if (_igdbInfo) {
    //parent
    parentLoading.value = true;
    if (_igdbInfo.parent_game) {
      parent.value = await TimeplayedAPI.getGameByIGDB(_igdbInfo.parent_game);
    }
    parentLoading.value = false;

    // similar
    similarLoading.value = true;
    for (const similar_id of _igdbInfo.similar_games) {
      const similarGame = await TimeplayedAPI.getGameByIGDB(similar_id);
      if (similarGame) {
        similarGames.value.push(similarGame);
      }
    }
    similarLoading.value = false;

    // expansions
    expansionsLoading.value = true;
    for (const expansion_id of _igdbInfo.expansions) {
      const expansionGame = await TimeplayedAPI.getGameByIGDB(expansion_id);
      if (expansionGame) {
        expansions.value.push(expansionGame);
      }
    }
    expansionsLoading.value = false;

    // expanded
    expandedLoading.value = true;
    for (const expanded_id of _igdbInfo.expanded_games) {
      const expandedGame = await TimeplayedAPI.getGameByIGDB(expanded_id);
      if (expandedGame) {
        expandedGames.value.push(expandedGame);
      }
    }
    expandedLoading.value = false;

    // ports
    portsLoading.value = true;
    for (const port_id of _igdbInfo.ports) {
      const portGame = await TimeplayedAPI.getGameByIGDB(port_id);
      if (portGame) {
        ports.value.push(portGame);
      }
    }
    portsLoading.value = false;

    // remakes
    remakesLoading.value = true;
    for (const remake_id of _igdbInfo.remakes) {
      const remakeGame = await TimeplayedAPI.getGameByIGDB(remake_id);
      if (remakeGame) {
        remakes.value.push(remakeGame);
      }
    }
    remakesLoading.value = false;

    // remasters
    remastersLoading.value = true;
    for (const remaster_id of _igdbInfo.remasters) {
      const remasterGame = await TimeplayedAPI.getGameByIGDB(remaster_id);
      if (remasterGame) {
        remasters.value.push(remasterGame);
      }
    }
    remastersLoading.value = false;

    // standalone expansions
    standaloneExpansionsLoading.value = true;
    for (const standalone_expansion_id of _igdbInfo.standalone_expansions) {
      const standaloneExpansionGame = await TimeplayedAPI.getGameByIGDB(
        standalone_expansion_id,
      );
      if (standaloneExpansionGame) {
        standaloneExpansions.value.push(standaloneExpansionGame);
      }
    }
    standaloneExpansionsLoading.value = false;
  }
});
</script>

<template>
  <div class="card mt-2 p-0 h-100">
    <div class="card-body">
      <div v-if="!info">
        <span
          class="spinner-border spinner-border mt-4"
          role="status"
          aria-hidden="true"
        ></span>
        <p>Loading...</p>
      </div>

      <div v-if="info">
        <a :href="info.url">
          <h2>{{ info.name }}</h2>
        </a>
        <div v-if="info.summary">
          <h4>Summary</h4>
          <p>{{ info.summary }}</p>
        </div>

        <div v-if="parent">
          <h4>
            Parent Game
            <span
              v-if="parentLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>
          <p>
            <a :href="'/game/' + parent.id">{{ parent.name }}</a>
          </p>
        </div>

        <div v-if="expansions.length > 0">
          <h4>
            Expansions
            <span
              v-if="expansionsLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

          <ul>
            <li
              v-for="ex in expansions.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="ex.id"
            >
              <a :href="'/game/' + ex.id">{{ ex.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="standaloneExpansions.length > 0">
          <h4>
            Standalone Expansions
            <span
              v-if="standaloneExpansionsLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

          <ul>
            <li
              v-for="se in standaloneExpansions.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="se.id"
            >
              <a :href="'/game/' + se.id">{{ se.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="ports.length > 0">
          <h4>
            Ports
            <span
              v-if="portsLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

          <ul>
            <li
              v-for="port in ports.sort((a, b) => a.name.localeCompare(b.name))"
              :key="port.id"
            >
              <a :href="'/game/' + port.id">{{ port.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="remakes.length > 0">
          <h4>
            Remakes
            <span
              v-if="remakesLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

          <ul>
            <li
              v-for="remake in remakes.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="remake.id"
            >
              <a :href="'/game/' + remake.id">{{ remake.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="remasters.length > 0">
          <h4>
            Remasters
            <span
              v-if="remastersLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

          <ul>
            <li
              v-for="remaster in remasters.sort((a, b) =>
                a.name.localeCompare(b.name),
              )"
              :key="remaster.id"
            >
              <a :href="'/game/' + remaster.id">{{ remaster.name }}</a>
            </li>
          </ul>
        </div>

        <div v-if="info.similar_games.length > 0">
          <h4>
            Similar Games
            <span
              v-if="similarLoading"
              class="spinner-border spinner-border-sm"
              role="status"
              aria-hidden="true"
            ></span>
          </h4>

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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { Game } from "../models/models";

import GameCover from "./GameCover.vue";
import { formatDate, formatDuration, timeAgo } from "../utils";

const props = withDefaults(
  defineProps<{ game: Game; showExpand?: boolean }>(),
  {
    showExpand: false,
  }
);

const expanded = ref(false);

function toggleExpand() {
  expanded.value = !expanded.value;
}

onMounted(async () => {});
</script>

<template>
  <tr class="align-middle">
    <td class="col-lg-1">
      <GameCover :game="game" :thumb="true" />
    </td>

    <td>
      <a :href="`/game/${props.game.id}`">{{ game.name }}</a>
    </td>

    <td>
      {{ timeAgo(new Date(props.game.last_played + "Z")) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.game.last_played + "Z"))
      }}</small>
    </td>

    <td>{{ formatDuration(props.game.seconds_played) }}</td>

    <td>
      <small v-if="expanded" class="text-muted">
        Game ID {{ game.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameWithStats } from "../../models/models";
import GameCover from "./GameCover.vue";

import { formatDate, formatDuration, timeAgo } from "../../utils";

const props = withDefaults(
  defineProps<{ game: GameWithStats; showExpand?: boolean }>(),
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
      <GameCover :game="game.game" :thumb="true" />
    </td>

    <td>
      <a :href="`/game/${props.game.game.id}`">{{ game.game.name }}</a>
    </td>

    <td>
      {{ timeAgo(new Date(props.game.last_played || 0)) }}
      <br />
      <small class="text-muted">{{
        formatDate(new Date(props.game.last_played || 0))
      }}</small>
    </td>

    <td>{{ formatDuration(props.game.total_playtime) }}</td>

    <td>
      <small v-if="expanded" class="text-muted">
        Game ID {{ game.game.id }} <br />
      </small>
      <button v-if="showExpand" @click="toggleExpand" class="btn btn-link p-0">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </button>
    </td>
  </tr>
</template>

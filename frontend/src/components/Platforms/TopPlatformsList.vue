<script setup lang="ts">
import { ref, watch } from "vue";
import type { Game, PlatformWithStats, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import PlatformBadge from "../Badges/PlatformBadge.vue";

// compact ranked list of the most played platforms in a date range, one section of the "most played" cards
const props = withDefaults(
  defineProps<{
    game?: Game;
    user?: User;
    after?: Date;
    before?: Date;
    limit?: number;
  }>(),
  { limit: 10 },
);

const platforms = ref<PlatformWithStats[]>([]);
const loading = ref(true);
let latest = 0;

watch(
  () => [props.game, props.user, props.after, props.before],
  async () => {
    const request = ++latest;
    loading.value = true;
    const data = await TimeplayedAPI.getPlatformsStats({
      game: props.game?.id,
      user: props.user?.id,
      after: props.after?.getTime(),
      before: props.before?.getTime(),
      limit: props.limit,
      sort: "playtime",
      order: "desc",
    });
    if (request !== latest) return; // a newer range was picked meanwhile
    // platforms without playtime in the range still come back
    platforms.value = data.filter((p) => p.stats.seconds > 0);
    loading.value = false;
  },
  { immediate: true },
);
</script>

<template>
  <div>
    <h3 class="h5 mb-2">Platforms</h3>
    <div v-if="loading" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </div>
    <p
      v-else-if="!platforms.length"
      class="text-body-secondary text-center mb-0"
    >
      Nothing played
    </p>
    <table v-else class="table table-sm table-hover align-middle mb-0">
      <tbody>
        <tr v-for="(platform, i) in platforms" :key="platform.id">
          <td class="text-body-secondary" style="width: 1%">{{ i + 1 }}</td>
          <!-- same height as the cover/avatar rows of the other lists -->
          <td style="width: 40px; height: 50px">
            <PlatformBadge :platform="platform" :showName="false" />
          </td>
          <td class="text-break">
            <a
              :href="`/platform/${platform.id}`"
              class="link-underline link-underline-opacity-0"
              >{{ platform.display_name }}</a
            >
          </td>
          <td class="text-end text-nowrap">
            {{ formatDuration(platform.stats.seconds) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

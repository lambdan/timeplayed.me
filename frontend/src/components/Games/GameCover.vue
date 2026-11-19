<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import type { GameCoverData, SGDBGrid } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { COVER_MAX_AGE, getCached, setCached } from "../../utils.cache";
import { useNsfw } from "../../composables/useNsfw";

const props = withDefaults(
  defineProps<{
    gameId: number;
    clickable?: boolean;
    maxHeight?: number;
    maxWidth?: number;
    /** the viewer is playing it, so there's nothing to protect them from */
    uncensored?: boolean;
  }>(),
  {
    clickable: true,
    maxWidth: 0,
    maxHeight: 400,
  },
);

const LOADING_COVER = `https://placehold.co/600x900?text=Loading...`;
const NSFW_COVER = `https://placehold.co/600x900?text=Cover+hidden`;
const clickable = ref(props.clickable);
const coverData = ref<GameCoverData>();
const nsfw = ref(false);
const { isCensored } = useNsfw();

// censored here and not when loading, so opting in (or the user loading late) shows it right away
const censored = computed(
  () => !props.uncensored && isCensored({ nsfw: nsfw.value }),
);
const imageUrl = computed(() => {
  if (!coverData.value) return LOADING_COVER;
  return censored.value ? NSFW_COVER : coverData.value.imageUrl;
});
const sourceUrl = computed(() =>
  censored.value ? undefined : coverData.value?.sourceUrl,
);
const creditsText = computed(() => {
  const data = coverData.value;
  if (!data) return "...";
  if (censored.value) return "NSFW";
  return data.credits
    ? `Source: ${data.source}. ${data.credits}`
    : `Source: ${data.source}.`;
});

/** this is a clusterfuck */
async function getGameCoverData(gameId: number): Promise<GameCoverData> {
  const key = `gameCover_${gameId}_GameCoverData8`;

  async function test(gameId: number): Promise<GameCoverData | undefined> {
    function getFromSessionStorage() {
      return getCached<GameCoverData>(key, COVER_MAX_AGE);
    }

    function fromGrid(grid: SGDBGrid): GameCoverData {
      function ret(url: string): GameCoverData {
        return {
          imageUrl: url,
          sourceUrl: `https://www.steamgriddb.com/grid/${grid.id}`,
          source: "SteamGridDB",
          credits: `Grid: ${grid.id}, Author: ${grid.author?.name}`,
        };
      }
      return ret(grid.url!);
    }

    /** a source failing (like a grid removed from SGDB) shouldn't stop us from trying the next one */
    async function orUndefined<T>(promise: Promise<T>): Promise<T | undefined> {
      try {
        return await promise;
      } catch {
        return undefined;
      }
    }

    async function getBest(id: number) {
      const best = await orUndefined(TimeplayedAPI.getBestSGDBGridForGame(id));
      if (best) {
        return fromGrid(best);
      }
      return null;
    }

    let inSS = getFromSessionStorage();
    if (inSS) {
      return inSS;
    }

    let waited = 0;
    const delay = 10;
    while (sessionStorage.getItem(key + "_loading") === "true") {
      //console.log("Waiting for someone else to load the cover...");
      await new Promise((resolve) => setTimeout(resolve, delay));
      inSS = getFromSessionStorage();
      if (inSS) {
        return inSS;
      }
      waited += delay;
      if (waited >= 3000) {
        return;
      }
    }

    sessionStorage.setItem(key + "_loading", "true");

    try {
      const gameData = await TimeplayedAPI.getGame(gameId);

      if (gameData.cover_disabled) {
        return {
          imageUrl: `https://placehold.co/600x900?text=Cover+art+disabled\\nfor+this+game`,
          source: "None",
        };
      }

      // direct image_url?
      if (gameData.image_url) {
        return {
          imageUrl: gameData.image_url,
          source: "Custom",
        };
      }

      // igdb?
      if (gameData.igdb_id) {
        const igdbInfo = await orUndefined(
          TimeplayedAPI.getIGDBGameInfo(gameData.igdb_id),
        );
        if (igdbInfo && igdbInfo.cover) {
          const size = "t_cover_big";
          const imageUrl = `https://images.igdb.com/igdb/image/upload/${size}/${igdbInfo.cover.image_id}.jpg`;
          return {
            imageUrl,
            source: "IGDB",
            sourceUrl: igdbInfo.url,
            credits: `IGDB cover image ID: ${igdbInfo.cover.image_id}`,
          };
        }
      }

      // sgdb as fallback
      if (gameData.sgdb_id) {
        const best = await getBest(gameData.sgdb_id);
        if (best) {
          return best;
        }
      }

      // steam, mostly for games that aren't on igdb
      if (gameData.steam_id) {
        const steam = await orUndefined(
          TimeplayedAPI.getSteamCover(gameData.steam_id),
        );
        if (steam) {
          return {
            imageUrl: steam.url,
            source: "Steam",
            sourceUrl: steam.store_url,
            credits: `Steam app ID: ${gameData.steam_id}`,
          };
        }
      }

      // parent?
      if (gameData.parent_id) {
        return getGameCoverData(gameData.parent_id);
      }

      return undefined;
    } catch (err) {
    } finally {
      sessionStorage.setItem(key + "_loading", "false");
    }
  }
  const coverData = await test(gameId);
  if (coverData) {
    setCached(key, coverData);
    return coverData;
  }
  // fallback to placeholder
  const size = "600x900";
  return {
    imageUrl: `https://placehold.co/${size}?text=No+cover+art\\n...yet`,
    source: "None",
  };
}

onMounted(async () => {
  // both at once, so an nsfw cover is never shown before the game says it's nsfw
  const [game, cover] = await Promise.all([
    TimeplayedAPI.getGame(props.gameId).catch(() => undefined),
    getGameCoverData(props.gameId),
  ]);
  nsfw.value = !!game?.nsfw;
  coverData.value = cover;
});
</script>

<template>
  <div style="display: inline-block; position: relative">
    <template v-if="clickable">
      <a :href="`/game/${props.gameId}`">
        <img
          v-show="imageUrl"
          :title="creditsText"
          :src="`${imageUrl}`"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </a>
    </template>
    <template v-else-if="sourceUrl">
      <a :href="sourceUrl">
        <img
          v-show="imageUrl"
          :src="`${imageUrl}`"
          :title="creditsText"
          class="img-fluid"
          :style="{
            maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
            maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
          }"
        />
      </a>
    </template>
    <template v-else>
      <img
        v-show="imageUrl"
        :src="`${imageUrl}`"
        :title="creditsText"
        class="img-fluid"
        :style="{
          maxHeight: props.maxHeight ? props.maxHeight + 'px' : undefined,
          maxWidth: props.maxWidth ? props.maxWidth + 'px' : undefined,
        }"
      />
    </template>
  </div>
</template>

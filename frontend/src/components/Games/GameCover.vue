<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { GameCoverData, SGDBGrid } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";

const props = withDefaults(
  defineProps<{
    gameId: number;
    thumb?: boolean;
    clickable?: boolean;
    maxHeight?: number;
    maxWidth?: number;
  }>(),
  {
    thumb: false,
    clickable: true,
    maxWidth: 0,
    maxHeight: 400,
  },
);

const LOADING_COVER = `https://placehold.co/600x900?text=Loading...`;
const clickable = ref(props.clickable);
const imageUrl = ref<string>(LOADING_COVER);
const coverData = ref<GameCoverData>();
const creditsText = ref("...");
const sourceUrl = ref<string>();

/** this is a clusterfuck */
async function getGameCoverData(
  gameId: number,
  thumbnail = false,
): Promise<GameCoverData> {
  const key = `gameCover_${gameId}_${thumbnail}_GameCoverData4`;

  async function test(
    gameId: number,
    thumbnail: boolean,
  ): Promise<GameCoverData | undefined> {
    function getFromSessionStorage() {
      const stored = sessionStorage.getItem(key);
      if (stored) {
        return JSON.parse(stored) as GameCoverData;
      }
      return null;
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
      if (grid.thumb && thumbnail) {
        return ret(grid.thumb);
      }
      return ret(grid.url!);
    }

    async function getBest(id: number) {
      const best = await TimeplayedAPI.getBestSGDBGridForGame(id);
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

      // direct image_url?
      if (gameData.image_url) {
        return {
          imageUrl: gameData.image_url,
          source: "Custom",
        };
      }

      // image_url explicitly set to 0 means this game should not have a cover
      if (gameData.image_url === "0") {
        return {
          imageUrl: `https://placehold.co/600x900?text=No+cover`,
          source: "None",
        };
      }

      // direct sgdb grid id?
      if (gameData.sgdb_id && gameData.sgdb_grid_id) {
        const grid = await TimeplayedAPI.getGrid(
          gameData.sgdb_id,
          gameData.sgdb_grid_id,
        );
        if (grid) {
          return fromGrid(grid);
        }
      }

      // sgdb auto?
      if (gameData.sgdb_id) {
        const best = await getBest(gameData.sgdb_id);
        if (best) {
          return best;
        }
      }

      // igdb?
      if (gameData.igdb_id) {
        const igdbInfo = await TimeplayedAPI.getIGDBGameInfo(gameData.igdb_id);
        if (igdbInfo && igdbInfo.cover) {
          const size = thumbnail ? "t_thumb" : "t_cover_big";
          const imageUrl = `https://images.igdb.com/igdb/image/upload/${size}/${igdbInfo.cover.image_id}.jpg`;
          return {
            imageUrl,
            source: "IGDB",
            sourceUrl: igdbInfo.url,
            credits: `IGDB cover image ID: ${igdbInfo.cover.image_id}`,
          };
        }
      }

      // steam?
      if (gameData.steam_id) {
        return {
          imageUrl: `https://shared.steamstatic.com/store_item_assets/steam/apps/${gameData.steam_id}/library_600x900.jpg`,
          source: "Steam",
          sourceUrl: `https://store.steampowered.com/app/${gameData.steam_id}`,
        };
      }

      // parent?
      if (gameData.parent_id) {
        return getGameCoverData(gameData.parent_id, thumbnail);
      }

      return undefined;
    } catch (err) {
    } finally {
      sessionStorage.setItem(key + "_loading", "false");
    }
  }
  const coverData = await test(gameId, thumbnail);
  if (coverData) {
    sessionStorage.setItem(key, JSON.stringify(coverData));
    return coverData;
  }
  // fallback to placeholder
  const size = thumbnail ? "267x400" : "600x900";
  return {
    imageUrl: `https://placehold.co/${size}?text=No+cover+found`,
    source: "None",
  };
}

onMounted(async () => {
  coverData.value = await getGameCoverData(props.gameId, props.thumb);
  imageUrl.value = coverData.value.imageUrl;

  sourceUrl.value = coverData.value.sourceUrl;
  creditsText.value = `Source: ${coverData.value.source}.`;
  if (coverData.value.credits) {
    creditsText.value += " " + coverData.value.credits;
  }
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

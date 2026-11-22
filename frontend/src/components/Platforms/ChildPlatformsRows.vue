<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { PlatformWithStats } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import CalendarBasic from "../CalendarBasic.vue";
import ExpandToggle from "../Misc/ExpandToggle.vue";
// rows for its children are this same component, one level deeper
import ChildPlatformsRows from "./ChildPlatformsRows.vue";
import {
  playedPlatformFamilyRow,
  type PlatformStatsFilters,
} from "../../utils.family";

// table rows for the children of a platform, each with the playtime of its own children
// included, and a row for the platform itself (without children) so the rows add up to
// its total. Platforms with children can be expanded to show them under it.
// Same as ChildGamesRows
const props = defineProps<{
  parent: PlatformWithStats;
  depth: number;
  /** same filters as the list the rows are in, e.g. its date range */
  filters?: PlatformStatsFilters;
  /** for TopPlatformsList: an empty rank cell, name and playtime only, no unplayed platforms */
  compact?: boolean;
}>();

const platforms = ref<PlatformWithStats[]>([]);
const loading = ref(true);
const expanded = ref(new Set<number>());
// compact: child platforms with more than themselves played (see playedPlatformFamilyRow)
const expandable = ref(new Set<number>());
// less in the compact list, it's in a narrow column
const indent = props.compact ? 0.75 : 1.5;

function setExpanded(id: number, value: boolean) {
  if (value) {
    expanded.value.add(id);
  } else {
    expanded.value.delete(id);
  }
}

const error = ref(false);

onMounted(async () => {
  try {
    const [children, parentOnly] = await Promise.all([
      TimeplayedAPI.getPlatformStatsMany(props.parent.children_ids, {
        ...props.filters,
        include_child_platforms: true,
      }),
      // the list endpoint, the single one says 404 when nothing matches the filters
      TimeplayedAPI.getPlatformStatsMany([props.parent.id], props.filters),
    ]);
    let rows = children.sort((a, b) => b.stats.seconds - a.stats.seconds);
    if (props.compact) {
      rows = rows.filter((p) => p.stats.seconds > 0);
      const shown = await Promise.all(
        rows.map((p) =>
          playedPlatformFamilyRow(p, props.filters ?? {}).catch(() => ({
            platform: p,
            expandable: p.children_ids.length > 0,
          })),
        ),
      );
      rows = shown.map((r) => r.platform);
      expandable.value = new Set(
        shown.filter((r) => r.expandable).map((r) => r.platform.id),
      );
    }
    // the parent's own playtime, among the children by playtime
    const own = parentOnly[0];
    if (own && own.stats.seconds > 0) {
      const i = rows.findIndex((p) => p.stats.seconds < own.stats.seconds);
      rows.splice(i === -1 ? rows.length : i, 0, own);
    }
    platforms.value = rows;
  } catch (e) {
    console.error("Loading child platforms failed", e);
    error.value = true;
  } finally {
    loading.value = false;
  }
});

function hasChildRows(platform: PlatformWithStats) {
  // the parent's own row is already expanded, its children are the other rows
  if (platform.id === props.parent.id) return false;
  return props.compact
    ? expandable.value.has(platform.id)
    : platform.children_ids.length > 0;
}
</script>

<template>
  <tr v-if="loading">
    <td :colspan="compact ? 3 : 4" class="text-center">
      <div class="spinner-border spinner-border-sm" role="status"></div>
    </td>
  </tr>
  <tr v-else-if="error">
    <td :colspan="compact ? 3 : 4" class="text-center text-body-secondary">
      Loading failed
    </td>
  </tr>
  <template v-for="platform in platforms" :key="platform.id">
    <tr>
      <td v-if="compact"></td>
      <td :style="{ paddingLeft: `${0.25 + depth * indent}rem` }">
        <div class="d-flex align-items-center gap-2">
          <ExpandToggle
            v-if="hasChildRows(platform)"
            :modelValue="expanded.has(platform.id)"
            @update:modelValue="(value) => setExpanded(platform.id, value)"
          />
          <!-- same width as the button, so badges line up -->
          <span v-else class="flex-shrink-0" style="width: 1em"></span>
          <PlatformBadge
            :platform="platform"
            :showName="false"
            class="flex-shrink-0"
            :class="{ 'opacity-50': expanded.has(platform.id) }"
          />
          <a
            :href="`/platform/${platform.id}`"
            class="link-underline link-underline-opacity-0 text-break"
            :class="{ 'opacity-50': expanded.has(platform.id) }"
            >{{ platform.display_name }}</a
          >
        </div>
      </td>
      <td class="text-end text-nowrap">
        <span :class="{ 'opacity-50': expanded.has(platform.id) }">{{
          formatDuration(platform.stats.seconds)
        }}</span>
      </td>
      <template v-if="!compact">
        <td class="text-end">
          <span :class="{ 'opacity-50': expanded.has(platform.id) }">{{
            platform.stats.user_count
          }}</span>
        </td>
        <td class="text-end text-nowrap d-none d-md-table-cell">
          <span :class="{ 'opacity-50': expanded.has(platform.id) }"
            ><CalendarBasic
              v-if="platform.stats.last_activity"
              :date="platform.stats.last_activity"
              :showIcon="false"
          /></span>
        </td>
      </template>
    </tr>
    <ChildPlatformsRows
      v-if="expanded.has(platform.id)"
      :parent="platform"
      :depth="depth + 1"
      :filters="filters"
      :compact="compact"
    />
  </template>
</template>

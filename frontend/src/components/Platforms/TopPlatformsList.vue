<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { Game, PlatformWithStats, User } from "../../api.models";
import { TimeplayedAPI } from "../../api.client";
import { formatDuration } from "../../utils";
import PlatformBadge from "../Badges/PlatformBadge.vue";
import ExpandToggle from "../Misc/ExpandToggle.vue";
import ChildPlatformsRows from "./ChildPlatformsRows.vue";
import { playedPlatformFamilyRow } from "../../utils.family";

// compact ranked list of the most played platforms in a date range, one section of the "most played" cards
const props = withDefaults(
  defineProps<{
    game?: Game;
    /** with game: also its child games */
    includeChildren?: boolean;
    user?: User;
    /** only platforms with names matching this */
    search?: string;
    after?: Date;
    before?: Date;
    limit?: number;
  }>(),
  { limit: 10 },
);

const platforms = ref<PlatformWithStats[]>([]);
const loading = ref(true);
// child platforms are counted in their parent.
// not when searching, the platform searched for could be a child
const grouped = computed(() => !props.search);
const expanded = ref(new Set<number>());
// platforms with more than themselves played, the rest have no arrow
const expandable = ref(new Set<number>());
let latest = 0;

const filters = computed(() => ({
  game: props.game?.id,
  include_children: props.includeChildren,
  user: props.user?.id,
  after: props.after?.getTime(),
  before: props.before?.getTime(),
}));

function setExpanded(id: number, value: boolean) {
  if (value) {
    expanded.value.add(id);
  } else {
    expanded.value.delete(id);
  }
}

watch(
  () => [filters.value, props.search, grouped.value],
  async () => {
    const request = ++latest;
    loading.value = true;
    const data = await TimeplayedAPI.getPlatformsStats({
      ...filters.value,
      include_child_platforms: grouped.value,
      search: props.search || undefined,
      limit: props.limit,
      sort: "playtime",
      order: "desc",
    });
    if (request !== latest) return; // a newer range was picked meanwhile
    // platforms without playtime in the range still come back
    let rows = data
      .filter((p) => p.stats.seconds > 0)
      .map((platform) => ({
        platform,
        expandable: platform.children_ids.length > 0,
      }));
    if (grouped.value) {
      // a failed check keeps the combined row as it is
      rows = await Promise.all(
        rows.map((row) =>
          playedPlatformFamilyRow(row.platform, filters.value).catch(() => row),
        ),
      );
      if (request !== latest) return;
    }
    platforms.value = rows.map((r) => r.platform);
    expandable.value = new Set(
      rows.filter((r) => r.expandable).map((r) => r.platform.id),
    );
    // the open child rows were for the old filters
    expanded.value.clear();
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
      {{ search ? "No matches" : "Nothing played" }}
    </p>
    <table v-else class="table table-sm table-hover align-middle mb-0">
      <tbody>
        <template v-for="(platform, i) in platforms" :key="platform.id">
          <tr>
            <td class="text-body-secondary" style="width: 1%">{{ i + 1 }}</td>
            <!-- same height as the cover/avatar rows of the other lists -->
            <td style="height: 50px">
              <div class="d-flex align-items-center gap-2">
                <template v-if="grouped">
                  <ExpandToggle
                    v-if="expandable.has(platform.id)"
                    :modelValue="expanded.has(platform.id)"
                    @update:modelValue="
                      (value) => setExpanded(platform.id, value)
                    "
                  />
                  <!-- same width as the button, so badges line up -->
                  <span v-else class="flex-shrink-0" style="width: 1em"></span>
                </template>
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
          </tr>
          <ChildPlatformsRows
            v-if="expanded.has(platform.id)"
            :parent="platform"
            :depth="1"
            :filters="filters"
            :compact="true"
          />
        </template>
      </tbody>
    </table>
  </div>
</template>

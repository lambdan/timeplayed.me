<script setup lang="ts">
import { ref } from "vue";
import type { User } from "../../models/models";
import PlatformTable from "./PlatformTable.vue";

const props = withDefaults(
  defineProps<{
    showExpand?: boolean;
    order?: "asc" | "desc";
    sort?: "recency" | "playtime" | "name";
    user?: User;
  }>(),
  {
    showExpand: false,
    order: "desc",
    sort: "recency",
    user: undefined,
  }
);

const localSort = ref(props.sort);
const localOrder = ref(props.order);

function setSort(newSort: "recency" | "playtime" | "name") {
  localSort.value = newSort;
}
function setOrder(newOrder: "asc" | "desc") {
  localOrder.value = newOrder;
}
</script>

<template>
  <div class="card p-0">
    <h1 class="card-header">Platforms</h1>
    <div class="card-body">
      <!-- Sort Button Group -->
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Sort platforms">
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'name' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setSort('name')"
          >
            Name
          </button>
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'recency' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setSort('recency')"
          >
            Recency
          </button>
          <button
            type="button"
            class="btn"
            :class="
              localSort === 'playtime' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setSort('playtime')"
          >
            Playtime
          </button>
        </div>
      </div>
      <!-- Order Button Group -->
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" aria-label="Order platforms">
          <button
            type="button"
            class="btn"
            :class="
              localOrder === 'asc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setOrder('asc')"
          >
            Ascending
          </button>
          <button
            type="button"
            class="btn"
            :class="
              localOrder === 'desc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setOrder('desc')"
          >
            Descending
          </button>
        </div>
      </div>
      <PlatformTable
        :showExpand="props.showExpand"
        :sort="localSort"
        :order="localOrder"
        :user="props.user"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, ref, onMounted } from "vue";

const currentSort = ref("");

const props = defineProps<{
  sort: string;
  order: string;
  sortOptions: Array<{ value: string; label: string }>;
  sortLabel?: string;
  orderLabel?: string;
}>();

const emit = defineEmits<{
  (e: "update:sort", value: string): void;
  (e: "update:order", value: string): void;
}>();

function setSort(newSort: string) {
  if (newSort === currentSort.value) {
    // If the same sort is clicked, toggle order
    if (props.order === "asc") {
      setOrder("desc");
    } else {
      setOrder("asc");
    }
    return;
  }
  currentSort.value = newSort;

  emit("update:sort", newSort);
  if (newSort === "name") {
    setOrder("asc"); // Default to ascending order for name sort
  }
  if (newSort === "playtime") {
    setOrder("desc"); // Default to descending order for playtime sort
  }
  if (newSort === "recency") {
    setOrder("desc"); // Default to descending order for recency sort
  }
}
function setOrder(newOrder: string) {
  emit("update:order", newOrder);
}

function suffix(sort: string) {
  if (sort !== currentSort.value) {
    // Hide suffix if not active
    return "";
  }
  if (sort === "name") {
    if (props.order === "asc") {
      return '<i class="bi bi-sort-alpha-down"></i>';
    }
    return '<i class="bi bi-sort-alpha-down-alt"></i>';
  }
  if (sort === "playtime") {
    if (props.order === "asc") {
      return '<i class="bi bi-sort-down-alt"></i>';
    }
    return '<i class="bi bi-sort-down"></i>';
  }
  if (sort === "recency") {
    if (props.order === "asc") {
      return '<i class="bi bi-hourglass-bottom"></i>';
    }
    return '<i class="bi bi-hourglass-top"></i>';
  }
  return props.order === "asc" ? "asc" : "desc";
}

onMounted(() => {
  // Initialize labels based on initial sort
  setOrder(props.order);
  setSort(props.sort);
});
</script>

<template>
  <div class="row">
    <div class="col">
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" :aria-label="sortLabel || 'Sort'">
          <button
            v-for="option in sortOptions"
            :key="option.value"
            type="button"
            class="btn"
            :class="
              props.sort === option.value
                ? 'btn-primary'
                : 'btn-outline-primary'
            "
            @click="setSort(option.value)"
          >
            {{ option.label }}
            <span v-html="suffix(option.value)"></span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

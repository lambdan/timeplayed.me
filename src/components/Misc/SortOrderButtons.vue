<script setup lang="ts">
import { defineProps, defineEmits } from "vue";

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
  emit("update:sort", newSort);
}
function setOrder(newOrder: string) {
  emit("update:order", newOrder);
}
</script>

<template>
  <div class="col">
    <!-- Sort Button Group -->
    <div class="row">
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
          </button>
        </div>
      </div>
    </div>
    <!-- Order Button Group -->
    <div class="row">
      <div class="mb-3 text-center">
        <div class="btn-group" role="group" :aria-label="orderLabel || 'Order'">
          <button
            type="button"
            class="btn"
            :class="
              props.order === 'asc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setOrder('asc')"
          >
            Ascending
          </button>
          <button
            type="button"
            class="btn"
            :class="
              props.order === 'desc' ? 'btn-primary' : 'btn-outline-primary'
            "
            @click="setOrder('desc')"
          >
            Descending
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

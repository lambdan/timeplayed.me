<script setup lang="ts">
defineProps<{
  // unsaved: how many unsaved changes are on that tab, so they're noticed from other tabs
  tabs: { id: string; label: string; unsaved?: number }[];
}>();
const section = defineModel<string>({ required: true });
</script>

<template>
  <ul class="nav nav-tabs mb-3">
    <li v-for="t in tabs" :key="t.id" class="nav-item">
      <a
        class="nav-link"
        :class="{ active: section === t.id }"
        href="#"
        @click.prevent="section = t.id"
        >{{ t.label }}
        <span v-if="t.unsaved" class="text-warning-emphasis"
          >({{ t.unsaved }} unsaved)</span
        ></a
      >
    </li>
  </ul>
</template>

<script setup lang="ts">
defineProps<{ tabs: { id: string; label: string }[] }>();
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
        >{{ t.label }}</a
      >
    </li>
  </ul>
</template>

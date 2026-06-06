<script setup lang="ts">
import "bootstrap-icons/font/bootstrap-icons.css";
import { onMounted, ref } from "vue";
import { fetchOrGetCachedGameName } from "../../utils.api";

const props = defineProps<{
  gameId: number;
}>();

const text = ref(props.gameId + "");
const fetched = ref(false);

onMounted(async () => {
  text.value = await fetchOrGetCachedGameName(props.gameId);
  fetched.value = true;
});
</script>

<template>
  <span class="badge bg-secondary me-1 mb-1">
    <a :href="'/game/' + gameId" class="text-white text-decoration-none">
      {{ text }}
    </a>
    <span
      v-if="!fetched"
      class="spinner-border spinner-border-sm ms-2"
      role="status"
      aria-hidden="true"
    ></span>
  </span>
</template>

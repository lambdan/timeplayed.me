<script setup lang="ts">
import { ref } from "vue";

// an image file (opens the photo library on phones) or a URL to download it from,
// the parent does the upload
defineProps<{ busy?: boolean }>();
const emit = defineEmits<{ file: [file: File]; url: [url: string] }>();

const url = ref("");

function pickFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) emit("file", file);
  // so picking the same file again still counts
  input.value = "";
}

function submitUrl() {
  const trimmed = url.value.trim();
  if (!trimmed) return;
  emit("url", trimmed);
  url.value = "";
}
</script>

<template>
  <div>
    <label class="btn btn-outline-primary mb-2" :class="{ disabled: busy }">
      <i class="bi bi-upload"></i> Upload cover
      <input
        type="file"
        accept="image/*"
        class="d-none"
        :disabled="busy"
        @change="pickFile"
      />
    </label>
    <div class="input-group">
      <input
        v-model="url"
        class="form-control"
        type="url"
        placeholder="or an image URL to download"
        @keydown.enter.prevent="submitUrl"
      />
      <button
        class="btn btn-outline-primary"
        :disabled="busy || !url.trim()"
        @click="submitUrl"
      >
        Set
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Platform } from "../../api.models";
import CalendarBasic from "../CalendarBasic.vue";

defineProps<{ platform: Platform }>();
</script>

<template>
  <div class="card p-0">
    <h2 class="card-header">Metadata</h2>
    <div class="card-body">
      <table class="table table-sm table-hover mb-0">
        <tbody>
          <tr>
            <th class="text-nowrap">ID</th>
            <td>{{ platform.id }}</td>
          </tr>
          <tr>
            <th class="text-nowrap">Abbreviation</th>
            <td>{{ platform.abbreviation }}</td>
          </tr>
          <tr v-if="platform.name">
            <th class="text-nowrap">Name</th>
            <td>{{ platform.name }}</td>
          </tr>
          <tr v-if="platform.color_primary">
            <th class="text-nowrap">Colors</th>
            <td>
              <span
                class="badge border me-1"
                :style="{ backgroundColor: `#${platform.color_primary}` }"
                >&nbsp;</span
              >#{{ platform.color_primary }}
              <template v-if="platform.color_secondary">
                <span
                  class="badge border ms-2 me-1"
                  :style="{ backgroundColor: `#${platform.color_secondary}` }"
                  >&nbsp;</span
                >#{{ platform.color_secondary }}
              </template>
            </td>
          </tr>
          <tr v-if="platform.icon">
            <th class="text-nowrap">Icon</th>
            <td>
              <i :class="`bi bi-${platform.icon}`"></i> {{ platform.icon }}
            </td>
          </tr>
          <tr>
            <th class="text-nowrap">Created</th>
            <td>
              <CalendarBasic
                :date="platform.created"
                :showIcon="false"
                :absolute="true"
              />
            </td>
          </tr>
          <tr>
            <th class="text-nowrap">Updated</th>
            <td>
              <CalendarBasic
                :date="platform.updated"
                :showIcon="false"
                :absolute="true"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

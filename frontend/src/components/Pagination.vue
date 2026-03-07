<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center space-x-1 sm:space-x-2">
    <!-- First page -->
    <button
      :disabled="currentPage === 1"
      class="pagination-btn"
      @click="$emit('change', 1)"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
      </svg>
    </button>
    <!-- Prev -->
    <button
      :disabled="currentPage === 1"
      class="pagination-btn"
      @click="$emit('change', currentPage - 1)"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
    </button>
    <!-- Page info -->
    <span class="px-3 py-2 text-sm text-gray-700">
      {{ currentPage }} / {{ totalPages }}
    </span>
    <!-- Next -->
    <button
      :disabled="currentPage === totalPages"
      class="pagination-btn"
      @click="$emit('change', currentPage + 1)"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </button>
    <!-- Last page -->
    <button
      :disabled="currentPage === totalPages"
      class="pagination-btn"
      @click="$emit('change', totalPages)"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  total: { type: Number, required: true },
  pageSize: { type: Number, default: 20 },
})

defineEmits(['change'])

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))
</script>

<style scoped>
.pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.75rem;
  min-height: 2.75rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
}
.pagination-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}
.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>

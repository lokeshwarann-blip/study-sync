<template>
  <span class="inline-flex items-center gap-0.5" :class="readonly ? '' : 'cursor-pointer'" @mouseleave="hover = 0">
    <button
      v-for="n in 5"
      :key="n"
      type="button"
      :disabled="readonly"
      :aria-label="`${n} star${n > 1 ? 's' : ''}`"
      class="leading-none transition-colors disabled:cursor-default"
      :style="{ fontSize: size + 'px', color: n <= shown ? '#f59e0b' : 'rgba(245,158,11,0.25)' }"
      @mouseenter="!readonly && (hover = n)"
      @click="!readonly && $emit('update:modelValue', n)"
    >★</button>
  </span>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  modelValue: { type: Number, default: 0 },   // supports decimals (e.g. 4.2) in readonly mode
  readonly: Boolean,
  size: { type: Number, default: 16 },
});
defineEmits(['update:modelValue']);

const hover = ref(0);
// Readonly shows the rounded average; interactive previews the hovered star.
const shown = computed(() => hover.value || Math.round(props.modelValue));
</script>

<template>
  <div class="stage-head">
    <span class="label"><b>Drum Selector</b> <span class="dim">— scroll, drag, or click name</span></span>
    <span class="chip" style="padding:3px 10px">{{ items.length ? currentIndex + 1 : 0 }} / {{ items.length }}</span>
  </div>

  <div
    id="wheelStageContainer"
    @wheel.prevent="handleWheel"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <div class="wheel-row">
      <div class="photo">
        <img
          v-if="shownImage"
          :src="shownImage"
          :alt="activeItem ? activeItem.label : 'Team preview'"
          :style="{ opacity: fading ? 0 : 1, transform: fading ? 'scale(1.04)' : 'scale(1)' }"
        />
        <div class="cap" v-if="activeItem">
          <span class="label" style="font-size:10px">{{ (activeItem.course || '').split(':')[0] }}</span>
          <b>{{ activeItem.label }}</b>
        </div>
      </div>

      <div class="wheel">
        <div class="marker"></div>
        <div id="radialWheelItems">
          <div
            v-for="(item, index) in items"
            :key="item.id"
            class="team-item"
            :class="{ active: index === currentIndex }"
            :style="itemStyle(index)"
            @click="selectIndex(index)"
          >
            <span>{{ item.label }}</span>
            <span v-if="index === currentIndex" class="dot"></span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="stage-foot">
    <span class="label dim">Use <kbd>↑</kbd> <kbd>↓</kbd> or drag wheel</span>
    <button id="spinRandomBtn" :class="{ busy: spinning }" @click="spinRandom">⚡ Spin Random Team ⤮</button>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({ items: { type: Array, default: () => [] } });
const emit = defineEmits(['active-change']);

const currentIndex = ref(0);
const activeItem = computed(() => props.items[currentIndex.value] || null);

// Photo cross-fade (same 150ms swap as the Stitch design)
const shownImage = ref('');
const fading = ref(false);
let fadeTimer = null;
watch(activeItem, (it) => {
  fading.value = true;
  clearTimeout(fadeTimer);
  fadeTimer = setTimeout(() => {
    shownImage.value = it ? it.image : '';
    fading.value = false;
  }, 150);
}, { immediate: true });

// New list from the API -> start at the first team
watch(() => props.items, (list) => {
  currentIndex.value = 0;
  if (list.length) emit('active-change', list[0]);
});

// Radial arc layout (math copied from the Stitch design)
function itemStyle(index) {
  const n = props.items.length;
  const radius = 220, spacing = 18;
  let offset = index - currentIndex.value;
  while (offset > n / 2) offset -= n;
  while (offset < -n / 2) offset += n;

  const angle = offset * spacing;
  const rad = (angle * Math.PI) / 180;
  const x = radius * (1 - Math.cos(rad));
  const y = radius * Math.sin(rad);
  const selected = Math.abs(offset) < 0.5;
  const dist = Math.min(Math.abs(offset) / 3, 1);
  const opacity = Math.max(0.15, Math.cos((dist * Math.PI) / 2));
  const scale = selected ? 1.08 : 1 - Math.min(Math.abs(offset) * 0.08, 0.4);

  return {
    opacity,
    transform: `translate(${x}px, ${y}px) translateY(-50%) rotate(${angle * 0.45}deg) scale(${scale})`,
  };
}

function selectIndex(i) {
  const n = props.items.length;
  if (!n) return;
  currentIndex.value = ((i % n) + n) % n;
  emit('active-change', props.items[currentIndex.value]);
}
const next = () => selectIndex(currentIndex.value + 1);
const prev = () => selectIndex(currentIndex.value - 1);

// Spin with deceleration
const spinning = ref(false);
let spinTimer = null;
function spinRandom() {
  if (spinning.value || props.items.length <= 1) return;
  spinning.value = true;
  const spins = 12 + Math.floor(Math.random() * 8);
  let step = 0, delay = 40;
  const tick = () => {
    next();
    step++;
    if (step < spins) { delay += 14; spinTimer = setTimeout(tick, delay); }
    else spinning.value = false;
  };
  tick();
}

// Mouse wheel (80ms cooldown)
let cooldown = false;
function handleWheel(e) {
  if (cooldown) return;
  cooldown = true;
  setTimeout(() => { cooldown = false; }, 80);
  e.deltaY > 0 ? next() : prev();
}

// Keyboard
function onKey(e) {
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { e.preventDefault(); next(); }
  else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
}

// Drag
let startY = 0, dragging = false;
function onPointerDown(e) {
  startY = e.clientY; dragging = true;
  e.currentTarget.setPointerCapture(e.pointerId);
}
function onPointerMove(e) {
  if (!dragging) return;
  const d = e.clientY - startY;
  if (Math.abs(d) > 40) { d < 0 ? next() : prev(); startY = e.clientY; }
}
function onPointerUp(e) {
  dragging = false;
  try { e.currentTarget.releasePointerCapture(e.pointerId); } catch (err) { /* noop */ }
}

onMounted(() => {
  window.addEventListener('keydown', onKey);
  if (props.items.length) emit('active-change', props.items[0]);
});
onUnmounted(() => {
  window.removeEventListener('keydown', onKey);
  clearTimeout(fadeTimer);
  clearTimeout(spinTimer);
});

defineExpose({ next, prev });
</script>

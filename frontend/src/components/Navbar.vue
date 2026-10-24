<template>
  <header class="ss-header">
    <div class="brand">
      <span class="wide" style="font-size:18px">✦ StudySync</span>
      <span class="tag">STUDY LAB</span>
    </div>

    <nav class="label">
      <button :class="{ on: currentView === 'dashboard' }" @click="$emit('change-view', 'dashboard')">Dashboard</button>
      <button :class="{ on: currentView === 'teams' }" @click="$emit('change-view', 'teams')">Choose Teams</button>
      <button :class="{ on: currentView === 'chat' }" @click="$emit('change-view', 'chat')">Messages</button>
      <button :class="{ on: currentView === 'profile' }" @click="$emit('change-view', 'profile')">Profile</button>
    </nav>

    <div class="right">
      <div v-if="user" class="user label">
        <span>{{ user.name }}</span><br />
        <span class="dim" style="font-size:10px">{{ user.major }}</span>
      </div>
      <button class="exit label" @click="$emit('logout')">Exit</button>
    </div>
  </header>
</template>

<script setup>
defineProps({ currentView: String, user: Object });
defineEmits(['change-view', 'logout']);
</script>

<style scoped>
.ss-header { height:56px; flex-shrink:0; border-bottom:1px solid var(--line); display:flex; align-items:center; justify-content:space-between; padding:0 32px; background:rgba(0,0,0,.85); backdrop-filter:blur(8px); position:relative; z-index:50; }
.brand { display:flex; align-items:center; gap:12px; }
.wide { font-family:'Syne',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:.01em; }
.tag { border:1px solid var(--line); padding:2px 8px; font-size:10px; letter-spacing:.2em; background:rgba(0,0,0,.6); }
.label { font-size:11px; letter-spacing:.2em; text-transform:uppercase; }
.dim { color:var(--dim); }
nav { display:flex; gap:6px; }
nav button { color:var(--pink); background:transparent; padding:6px 12px; border:1px solid transparent; font:inherit; letter-spacing:inherit; text-transform:inherit; }
nav button.on { background:var(--pink); color:#000; }
nav button:not(.on):hover { border-color:var(--line); }
.right { display:flex; align-items:center; gap:16px; }
.user { text-align:right; line-height:1.3; }
.exit { color:var(--pink); background:transparent; border:1px solid var(--line); padding:6px 12px; }
.exit:hover { background:var(--pink); color:#000; }
@media (max-width:1023px) { nav { display:none; } }
</style>

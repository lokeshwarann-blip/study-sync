<template>
  <!-- No bg-black here: body is black, and the shader sits at -z-10 behind everything -->
  <div class="h-screen w-screen flex flex-col text-[#ffa6e6] overflow-hidden relative">
    <ShaderBackground v-if="user" />

    <Navbar
      v-if="user"
      :current-view="currentView"
      :user="user"
      @change-view="currentView = $event"
      @logout="handleLogout"
    />

    <main class="flex-1 flex overflow-hidden min-h-0">
      <LoginView v-if="!user" @auth-success="initUser" />

      <template v-else>
        <DashboardView v-if="currentView === 'dashboard'" :user="user" />
        <TeamsView v-else-if="currentView === 'teams'" />
        <ChatView v-else-if="currentView === 'chat'" :user="user" />
        <ProfileView v-else-if="currentView === 'profile'" />
      </template>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Navbar from './components/Navbar.vue';
import ShaderBackground from './components/ShaderBackground.vue';
import LoginView from './views/LoginView.vue';
import DashboardView from './views/DashboardView.vue';
import TeamsView from './views/TeamsView.vue';
import ProfileView from './views/ProfileView.vue';
import ChatView from './views/ChatView.vue';
import { getMe } from './api.js';

const currentView = ref('dashboard');
const user = ref(null);

async function initUser() {
  const token = localStorage.getItem('token');
  if (!token) {
    user.value = null;
    return;
  }
  try {
    user.value = await getMe();
  } catch (err) {
    console.error('Session expired', err);
    localStorage.removeItem('token');
    user.value = null;
  }
}

function handleLogout() {
  localStorage.removeItem('token');
  user.value = null;
}

onMounted(() => { initUser(); });
</script>

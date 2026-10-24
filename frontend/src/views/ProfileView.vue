<template>
  <div class="flex-1 p-8 max-w-6xl w-full mx-auto overflow-y-auto font-space text-[#ffa7e4]">
    <div class="border-b border-[#ffa7e4]/60 pb-4 mb-6">
      <span class="border border-[#ffa7e4] bg-[#ffa7e4] text-black font-syne font-bold px-2 py-0.5 text-[10px] tracking-widest uppercase">
        STUDENT IDENTITY & PREFERENCES
      </span>
      <h1 class="font-syne font-extrabold text-3xl uppercase tracking-tight text-[#ffa7e4] mt-1">
        My Profile & Availability
      </h1>
      <p class="text-xs text-[#ffa7e4]/70 mt-0.5">
        Manage your personal dossier, study habits, topic proficiency ratings, and timetable availability.
      </p>
    </div>

    <div v-if="loading" class="text-center py-12 text-[#ffa7e4]/50">
      Loading profile dossier...
    </div>

    <div v-else class="space-y-8">
      <!-- SECTION 1: Personal Dossier & About Me -->
      <section class="border border-[#ffa7e4] bg-[#0c080f]/90 p-6 shadow-[0_0_20px_rgba(255,166,230,0.1)] relative">
        <div class="flex items-center gap-2 mb-4 border-b border-[#ffa7e4]/40 pb-3">
          <span class="w-2.5 h-2.5 bg-[#ffa7e4] inline-block"></span>
          <h2 class="font-syne font-bold text-lg uppercase text-[#ffa7e4]">
            Personal Dossier & Bio
          </h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
          <!-- Avatar Preview & Selector -->
          <div class="md:col-span-3 flex flex-col items-center justify-center p-4 border border-[#ffa7e4]/40 bg-black/60">
            <div class="w-28 h-28 border-2 border-[#ffa7e4] p-1 mb-3 relative overflow-hidden bg-neutral-900 shadow-[0_0_15px_rgba(255,166,230,0.2)]">
              <img :src="avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&q=80'" alt="Avatar" class="w-full h-full object-cover grayscale contrast-105" />
            </div>
            <span class="text-[10px] font-mono tracking-widest uppercase text-[#ffa7e4]/60">CAMPUS BADGE VERIFIED</span>
          </div>

          <!-- Basic Info Fields -->
          <div class="md:col-span-9 space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1">Full Student Name</label>
                <input
                  v-model="name"
                  type="text"
                  placeholder="e.g. Alex Chen"
                  class="w-full bg-black/70 border border-[#ffa7e4]/60 p-2.5 text-xs text-white focus:outline-none focus:border-[#ffa7e4] font-mono"
                />
              </div>

              <div>
                <label class="block text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1">Academic Major & Year</label>
                <input
                  v-model="major"
                  type="text"
                  placeholder="e.g. Computer Science, Senior"
                  class="w-full bg-black/70 border border-[#ffa7e4]/60 p-2.5 text-xs text-white focus:outline-none focus:border-[#ffa7e4] font-mono"
                />
              </div>
            </div>

            <!-- About Me / Bio -->
            <div>
              <label class="block text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1">About Me / Study Goals</label>
              <textarea
                v-model="bio"
                rows="2"
                placeholder="Tell potential cohort members what courses you're taking, target grades, or areas you enjoy tutoring..."
                class="w-full bg-black/70 border border-[#ffa7e4]/60 p-2.5 text-xs text-white focus:outline-none focus:border-[#ffa7e4] font-mono resize-none"
              ></textarea>
            </div>

            <!-- Learning / Study Style -->
            <div>
              <label class="block text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1">Preferred Learning & Study Style</label>
              <select
                v-model="studyStyle"
                class="w-full bg-black/70 border border-[#ffa7e4]/60 p-2.5 text-xs text-[#ffa7e4] focus:outline-none focus:border-[#ffa7e4] font-mono"
              >
                <option value="Collaborative problem-solving & sprint sessions">Collaborative problem-solving & sprint sessions (45m)</option>
                <option value="Quiet focused co-working & virtual whiteboard">Quiet focused co-working & virtual whiteboard</option>
                <option value="Peer tutoring & practice exam walkthroughs">Peer tutoring & practice exam walkthroughs</option>
                <option value="Homework problem sets & discussion">Homework problem sets & discussion</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      <!-- SECTION 2: Topic Skill Sliders -->
      <section class="border border-[#ffa7e4] bg-[#0c080f]/90 p-6 shadow-[0_0_20px_rgba(255,166,230,0.1)]">
        <h2 class="font-syne font-bold text-lg uppercase text-[#ffa7e4] mb-4 flex items-center justify-between">
          <span>Topic Proficiency Ratings</span>
          <span class="text-xs text-[#ffa7e4]/60 font-mono">1–2 = Need Help • 4–5 = Can Tutor</span>
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div
            v-for="topic in allTopics"
            :key="topic.id"
            class="border border-[#ffa7e4]/40 p-4 bg-black/40 flex flex-col justify-between"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-mono font-medium text-sm text-white">{{ topic.name }}</span>
              <span
                :class="[
                  'px-2 py-0.5 text-xs font-syne font-bold',
                  (ratingsMap[topic.id] || 3) <= 2 ? 'bg-rose-950 text-rose-300 border border-rose-500' :
                  (ratingsMap[topic.id] || 3) >= 4 ? 'bg-emerald-950 text-emerald-300 border border-emerald-500' :
                  'bg-neutral-900 text-neutral-300 border border-neutral-600'
                ]"
              >
                {{ ratingsMap[topic.id] || 3 }}/5
                <span v-if="(ratingsMap[topic.id] || 3) <= 2">(Needs Help)</span>
                <span v-else-if="(ratingsMap[topic.id] || 3) >= 4">(Can Tutor)</span>
              </span>
            </div>

            <input
              type="range"
              min="1"
              max="5"
              step="1"
              v-model.number="ratingsMap[topic.id]"
              class="w-full accent-[#ffa7e4] cursor-pointer"
            />
          </div>
        </div>
      </section>

      <!-- SECTION 3: Availability Matrix -->
      <section class="border border-[#ffa7e4] bg-[#0c080f]/90 p-6 shadow-[0_0_20px_rgba(255,166,230,0.1)]">
        <h2 class="font-syne font-bold text-lg uppercase text-[#ffa7e4] mb-2">
          Weekly Free Study Hours
        </h2>
        <p class="text-xs text-[#ffa7e4]/60 mb-4 font-mono">
          Click any block to toggle your open availability. At least 50% group overlap determines consensus matches.
        </p>

        <div class="overflow-x-auto pb-2">
          <div class="min-w-[650px] border border-[#ffa7e4]/40">
            <!-- Header days -->
            <div class="grid grid-cols-8 text-center text-xs border-b border-[#ffa7e4]/40 bg-[#ffa7e4]/10 font-syne font-bold text-[#ffa7e4]">
              <div class="p-2 border-r border-[#ffa7e4]/40">TIME</div>
              <div v-for="d in days" :key="d" class="p-2 border-r border-[#ffa7e4]/40 last:border-r-0">{{ d }}</div>
            </div>

            <!-- Hour rows (10 to 20) -->
            <div
              v-for="h in [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]"
              :key="h"
              class="grid grid-cols-8 text-center text-xs border-b border-[#ffa7e4]/20 last:border-b-0"
            >
              <div class="p-2 text-right pr-3 font-mono text-[#ffa7e4]/60 border-r border-[#ffa7e4]/40 bg-black/40">
                {{ h }}:00
              </div>
              <div
                v-for="d in days"
                :key="d + h"
                @click="toggleSlot(d, h)"
                :class="[
                  'p-2 cursor-pointer border-r border-[#ffa7e4]/20 last:border-r-0 transition-colors font-mono',
                  isSlotSelected(d, h) ? 'bg-[#ffa7e4] text-black font-bold' : 'hover:bg-[#ffa7e4]/20'
                ]"
              >
                {{ isSlotSelected(d, h) ? 'FREE' : '-' }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Save Button & Toast -->
      <div class="flex items-center justify-between pt-2">
        <span class="text-xs text-emerald-400 font-bold font-mono" v-if="saveMessage">{{ saveMessage }}</span>
        <span v-else></span>

        <button
          @click="saveProfile"
          :disabled="saving"
          class="border border-[#ffa7e4] bg-[#ffa7e4] text-black font-syne font-extrabold px-8 py-3 text-xs uppercase tracking-wider hover:bg-white transition-all shadow-[0_0_15px_rgba(255,166,230,0.3)] disabled:opacity-50"
        >
          {{ saving ? 'Saving Profile...' : 'Save & Update Matching' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { getMe, getTopics, updateProfile } from '../api.js';

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const loading = ref(true);
const saving = ref(false);
const saveMessage = ref('');
const allTopics = ref([]);
const ratingsMap = ref({});
const selectedSlots = ref(new Set());

// Student Personal Info
const name = ref('');
const major = ref('');
const bio = ref('');
const studyStyle = ref('Collaborative problem-solving & sprint sessions');
const avatar = ref('');

async function loadData() {
  loading.value = true;
  try {
    const [userData, topicsData] = await Promise.all([getMe(), getTopics()]);
    allTopics.value = topicsData;

    // Load personal info
    name.value = userData.name || '';
    major.value = userData.major || '';
    bio.value = userData.bio || '';
    studyStyle.value = userData.study_style || 'Collaborative problem-solving & sprint sessions';
    avatar.value = userData.avatar || '';

    // Populate ratings
    topicsData.forEach(t => {
      ratingsMap.value[t.id] = 3;
    });
    userData.topics.forEach(ut => {
      ratingsMap.value[ut.topic_id] = ut.rating;
    });

    // Populate availability slots
    selectedSlots.value.clear();
    userData.availability.forEach(a => {
      selectedSlots.value.add(`${a.day}-${a.hour}`);
    });
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
}

function isSlotSelected(day, hour) {
  return selectedSlots.value.has(`${day}-${hour}`);
}

function toggleSlot(day, hour) {
  const key = `${day}-${hour}`;
  if (selectedSlots.value.has(key)) {
    selectedSlots.value.delete(key);
  } else {
    selectedSlots.value.add(key);
  }
}

async function saveProfile() {
  saving.value = true;
  saveMessage.value = '';
  try {
    const topicsPayload = Object.entries(ratingsMap.value).map(([tId, r]) => ({
      topic_id: parseInt(tId),
      rating: r
    }));

    const availPayload = Array.from(selectedSlots.value).map(key => {
      const [d, h] = key.split('-');
      return { day: d, hour: parseInt(h) };
    });

    await updateProfile({
      name: name.value,
      major: major.value,
      bio: bio.value,
      study_style: studyStyle.value,
      avatar: avatar.value,
      topics: topicsPayload,
      availability: availPayload
    });

    saveMessage.value = '✓ Profile & Dossier updated! Matching engine recalculated.';
  } catch (err) {
    saveMessage.value = 'Error: ' + err.message;
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

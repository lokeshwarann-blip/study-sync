<template>
  <div class="ss-dash">
    <div class="titlebar">
      <div>
        <h1 class="wide">Study Team Matcher <em>Synergy</em></h1>
        <p class="dim">Select or spin a high-synergy cohort to review scheduled time slots and complementary competencies.</p>
      </div>
      <div class="chips">
        <span class="chip">{{ teams.length }} Active Cohorts</span>
        <span class="chip">Avg. {{ avgSynergy }}% Synergy</span>
      </div>
    </div>

    <div v-if="toastMessage" class="toast">
      <span>{{ toastMessage }}</span>
      <button class="toast-x" @click="toastMessage = ''">✕</button>
    </div>

    <div class="grid">
      <section>
        <WheelCarousel ref="wheel" :items="teams" @active-change="selectedTeam = $event" />
      </section>

      <section class="detail">
        <TeamDossier
          :team="selectedTeam"
          :joining="joining"
          :user-name="user?.name || ''"
          @join="handleJoin"
          @next="wheel?.next()"
        />
      </section>
    </div>

    <footer>
      <span>● SRM Ramapuram Live Sync Active · Last re-indexed 2m ago</span>
      <span><a href="#rules">Study Honor Code</a><a href="#help">Synergy Algorithm FAQ</a><a href="#v">StudySync v2.4</a></span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import WheelCarousel from '../components/WheelCarousel.vue';
import TeamDossier from '../components/TeamDossier.vue';
import { getWheelSuggestions, joinGroup } from '../api.js';

defineProps({ user: Object });

const wheel = ref(null);
const teams = ref([]);
const selectedTeam = ref(null);
const joining = ref(false);
const toastMessage = ref('');

const avgSynergy = computed(() => {
  if (!teams.value.length) return '0.0';
  const sum = teams.value.reduce((a, t) => a + (Number(t.match_score) || 0), 0);
  return (sum / teams.value.length).toFixed(1);
});

async function loadWheel() {
  try {
    const data = await getWheelSuggestions();
    teams.value = data;
    selectedTeam.value = data[0] || null;
  } catch (err) {
    console.error(err);
  }
}

async function handleJoin(groupId) {
  joining.value = true;
  try {
    const res = await joinGroup(groupId);
    toastMessage.value = res.message || 'Successfully joined group!';
    await loadWheel();
  } catch (err) {
    toastMessage.value = err.message;
  } finally {
    joining.value = false;
  }
}

onMounted(loadWheel);
</script>

<!-- Stitch dashboard styles, scoped under .ss-dash so other views are not affected.
     Not `scoped` on purpose: the wheel + dossier child components use these classes too. -->
<style>
.ss-dash { flex:1; min-width:0; min-height:0; width:100%; max-width:1560px; margin:0 auto; padding:24px 32px 12px; display:flex; flex-direction:column; position:relative; z-index:10; }
.ss-dash .wide { font-family:'Syne',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:.01em; }
.ss-dash .label { font-size:11px; letter-spacing:.2em; text-transform:uppercase; }
.ss-dash .dim { color:var(--dim); }

.ss-dash .titlebar { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; margin-bottom:20px; flex-shrink:0; flex-wrap:wrap; }
.ss-dash .titlebar h1 { font-size:clamp(26px,3.4vw,44px); line-height:1; display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; text-shadow:0 2px 12px rgba(0,0,0,.8); }
.ss-dash .titlebar h1 em { font-family:'Instrument Serif',serif; font-style:italic; font-weight:400; text-transform:none; font-size:1.2em; }
.ss-dash .titlebar p { margin-top:8px; font-size:13px; }
.ss-dash .chips { display:flex; gap:8px; }
.ss-dash .chip { border:1px solid var(--line); padding:6px 12px; font-size:11px; letter-spacing:.14em; text-transform:uppercase; background:rgba(0,0,0,.7); backdrop-filter:blur(4px); }

.ss-dash .toast { margin-bottom:16px; border:1px solid var(--line); background:rgba(0,0,0,.8); padding:10px 14px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center; gap:16px; }
.ss-dash .toast-x { padding:0 6px; border:none; background:transparent; }

.ss-dash .grid { flex:1; min-height:0; display:grid; grid-template-columns:1fr 1fr; gap:24px; position:relative; z-index:10; }
.ss-dash section { border:1px solid var(--line); display:flex; flex-direction:column; min-height:0; position:relative; overflow:hidden; background:rgba(6,4,8,.78); backdrop-filter:blur(10px); }
.ss-dash .stage-head { padding:16px 24px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--line); background:rgba(0,0,0,.5); }
.ss-dash .stage-foot { padding:16px 24px; border-top:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; background:rgba(0,0,0,.5); }
.ss-dash kbd { border:1px solid var(--line); padding:1px 6px; font-family:inherit; font-size:11px; }

.ss-dash #wheelStageContainer { flex:1; min-height:340px; position:relative; display:flex; align-items:center; justify-content:center; padding:16px; overflow:hidden; user-select:none; touch-action:none; }
.ss-dash .wheel-row { position:relative; width:100%; max-width:560px; height:100%; display:flex; align-items:center; justify-content:space-between; }
.ss-dash .photo { position:relative; width:34%; max-width:190px; aspect-ratio:3/4; border:1px solid var(--pink); overflow:hidden; flex-shrink:0; margin-left:8px; background:#111; box-shadow:0 0 20px rgba(0,0,0,.8); }
.ss-dash .photo img { width:100%; height:100%; object-fit:cover; filter:grayscale(1) contrast(1.05); transition:opacity .4s cubic-bezier(.16,1,.3,1), transform .4s cubic-bezier(.16,1,.3,1); display:block; }
.ss-dash .photo::after { content:""; position:absolute; inset:0; background:linear-gradient(to top, rgba(0,0,0,.85), transparent 55%); }
.ss-dash .photo .cap { position:absolute; left:10px; right:10px; bottom:10px; z-index:2; }
.ss-dash .photo .cap b { display:block; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }
.ss-dash .wheel { position:relative; flex:1; height:360px; overflow:hidden; -webkit-mask-image:linear-gradient(to bottom,transparent,#000 18%,#000 82%,transparent); mask-image:linear-gradient(to bottom,transparent,#000 18%,#000 82%,transparent); }
.ss-dash .marker { position:absolute; left:24px; top:50%; transform:translate(-50%,-50%); width:14px; height:14px; background:var(--pink); z-index:2; box-shadow:0 0 0 4px rgba(255,166,230,.25); pointer-events:none; }
.ss-dash .marker::after { content:""; position:absolute; inset:5px; background:#000; }
.ss-dash #radialWheelItems { position:absolute; inset:0; }
.ss-dash .team-item { position:absolute; left:40px; top:50%; cursor:pointer; padding:6px 12px; display:flex; align-items:center; gap:10px; color:var(--dim); font-weight:500; font-size:15px; text-transform:uppercase; letter-spacing:.06em; transform-origin:left center; transition:all .35s cubic-bezier(.16,1,.3,1); white-space:nowrap; }
.ss-dash .team-item:hover { color:var(--pink); }
.ss-dash .team-item.active { color:var(--pink); font-family:'Syne',sans-serif; font-weight:800; font-size:24px; text-shadow:0 0 16px rgba(255,166,230,.4); }
.ss-dash .team-item .dot { width:7px; height:7px; background:var(--pink); animation:ss-pulse 1.4s infinite; }
@keyframes ss-pulse { 50% { opacity:.25; } }

.ss-dash .detail { padding:28px; justify-content:space-between; overflow:auto; }
.ss-dash .detail-top { display:flex; flex-direction:column; gap:22px; }
.ss-dash .head { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; padding-bottom:18px; border-bottom:1px solid var(--line); flex-wrap:wrap; }
.ss-dash .tags { display:flex; align-items:center; gap:10px; margin-bottom:10px; flex-wrap:wrap; }
.ss-dash .tags .box { border:1px solid var(--line); padding:3px 10px; font-size:11px; letter-spacing:.12em; text-transform:uppercase; background:rgba(0,0,0,.5); }
.ss-dash #detailTeamName { font-size:clamp(26px,3.2vw,44px); line-height:1; }
.ss-dash .score { border:1px solid var(--line); padding:8px 14px; font-weight:700; font-size:13px; letter-spacing:.1em; text-transform:uppercase; background:rgba(0,0,0,.6); }
.ss-dash .stats { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; border:1px solid var(--line); padding:12px 16px; background:rgba(0,0,0,.55); }
.ss-dash .stats .grp { display:flex; align-items:center; gap:12px; }
.ss-dash .stats .av { width:32px; height:32px; border:1px solid var(--pink); margin-left:-8px; background:#111; display:flex; align-items:center; justify-content:center; font-family:'Syne',sans-serif; font-weight:800; font-size:12px; }
.ss-dash .stats .av:first-child { margin-left:0; }
.ss-dash .stats b { font-size:13px; display:block; text-transform:uppercase; letter-spacing:.04em; }
.ss-dash .stats small { font-size:11px; color:var(--dim); }
.ss-dash .pills { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px; }
.ss-dash .pill { border:1px solid var(--line); padding:12px 14px; background:rgba(0,0,0,.5); }
.ss-dash .pill .label { font-size:10px; display:block; margin-bottom:6px; }
.ss-dash .pill p { font-weight:600; font-size:14px; text-transform:uppercase; letter-spacing:.03em; }
.ss-dash .why { border:1px solid var(--line); padding:16px 18px; background:rgba(0,0,0,.5); }
.ss-dash .why h4 { font-size:11px; letter-spacing:.2em; text-transform:uppercase; margin-bottom:8px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.ss-dash .why h4 span { border:1px solid var(--line); padding:1px 8px; font-size:10px; background:rgba(0,0,0,.5); }
.ss-dash .why p { font-size:14px; line-height:1.6; }
.ss-dash .why .meta { margin-top:14px; padding-top:12px; border-top:1px solid var(--line); display:flex; justify-content:space-between; gap:10px; font-size:11px; letter-spacing:.1em; text-transform:uppercase; flex-wrap:wrap; }
.ss-dash .empty { margin:auto; }
.ss-dash .cta { display:flex; gap:12px; margin-top:24px; padding-top:20px; border-top:1px solid var(--line); }

.ss-dash button { font-family:inherit; cursor:pointer; text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:12px; padding:14px 22px; border:1px solid var(--pink); background:rgba(0,0,0,.6); color:var(--pink); transition:all .15s; }
.ss-dash button:hover { background:rgba(255,166,230,.2); }
.ss-dash button:active { transform:scale(.98); }
.ss-dash button:disabled { opacity:.5; pointer-events:none; }
.ss-dash #joinTeamBtn { flex:1; background:var(--pink); color:#000; }
.ss-dash #joinTeamBtn:hover { background:#fff; }
.ss-dash #spinRandomBtn.busy { pointer-events:none; opacity:.6; }

.ss-dash footer { margin-top:12px; padding-top:10px; border-top:1px solid var(--line); display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--dim); flex-shrink:0; background:rgba(0,0,0,.8); backdrop-filter:blur(6px); position:relative; z-index:10; }
.ss-dash footer a { color:inherit; text-decoration:none; margin-left:16px; }
.ss-dash footer a:hover { color:var(--pink); }

@media (max-width:1023px) {
  .ss-dash { overflow:auto; }
  .ss-dash .grid { grid-template-columns:1fr; }
  .ss-dash section { min-height:480px; }
}
</style>

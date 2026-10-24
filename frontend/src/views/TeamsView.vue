<template>
  <div class="ss-teams">
    <!-- Page header -->
    <div class="page-head">
      <div>
        <span class="tag-solid">CAMPUS DIRECTORY</span>
        <h1 class="wide">Explore Study Groups</h1>
        <p class="dim">Browse all registered cohorts, join an open study pod, or start your own.</p>
      </div>
      <div class="head-controls">
        <div class="sort-box">
          <label class="sort-label">Sort By:</label>
          <select v-model="sortBy" class="sort-select">
            <option value="synergy">✦ Highest Synergy Score</option>
            <option value="rating">★ Highest Cohort Rating</option>
            <option value="name">A–Z Name</option>
            <option value="openings">Most Open Seats</option>
          </select>
        </div>
        <input v-model="searchQuery" type="text" class="search" placeholder="Filter by course, topic, or cohort..." />
      </div>
    </div>

    <div v-if="toastMessage" class="toast">
      <span>{{ toastMessage }}</span>
      <button class="toast-x" @click="toastMessage = ''">✕</button>
    </div>

    <!-- ───────── PENDING JOIN REQUESTS (FOR COHORT LEADERS) ───────── -->
    <section v-if="incomingRequests.length" class="panel requests-panel">
      <div class="requests-head">
        <div>
          <span class="tag-alert">ACTION REQUIRED</span>
          <h2 class="wide req-title">Incoming Join Requests ({{ incomingRequests.length }})</h2>
          <p class="dim req-sub">Review applicants requesting to join your study cohort.</p>
        </div>
      </div>
      <div class="requests-list">
        <div v-for="req in incomingRequests" :key="req.request_id" class="request-item">
          <div class="req-user-info">
            <div class="req-name-row">
              <span class="req-user-name">{{ req.user_name }}</span>
              <span class="req-group-tag">{{ req.group_name }}</span>
            </div>
            <p class="req-major dim">{{ req.user_major }}</p>
            <div v-if="req.topics && req.topics.length" class="req-topics">
              <span v-for="t in req.topics.slice(0, 3)" :key="t.topic" class="req-topic-badge">
                {{ t.topic }}: <b class="star-gold">★ {{ t.rating }}/5</b>
              </span>
            </div>
          </div>
          <div class="req-actions">
            <button class="btn-req-reject" @click="handleRequestAction(req.request_id, 'reject')">
              ✕ Reject
            </button>
            <button class="btn-req-accept" @click="handleRequestAction(req.request_id, 'accept')">
              ✓ Accept Member
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ───────── CREATE YOUR OWN TEAM ───────── -->
    <section class="panel create">
      <button type="button" class="create-bar" @click="open = !open">
        <span class="wide create-title">✦ Create Your Own Team</span>
        <span class="label dim">{{ open ? 'Close' : 'Set up a new cohort in 1 minute' }}</span>
        <span class="create-plus">{{ open ? '−' : '+' }}</span>
      </button>

      <form v-if="open" class="form" @submit.prevent="submit">
        <div v-if="formError" class="form-error">{{ formError }}</div>

        <div class="grid2">
          <div class="field">
            <label class="label">Team Name *</label>
            <input v-model="form.name" maxlength="40" type="text" placeholder="e.g. Graph Titans" />
          </div>
          <div class="field">
            <label class="label">Course *</label>
            <input v-model="form.course" maxlength="80" type="text" placeholder="e.g. CS 4820: Algorithms" />
          </div>
        </div>

        <div class="field">
          <label class="label">Goal / Description <span class="dim">({{ form.description.length }}/300)</span></label>
          <textarea v-model="form.description" maxlength="300" rows="2" placeholder="What will this team work on? e.g. Prepare for Prelim 2 with weekly problem sets."></textarea>
        </div>

        <div class="field">
          <label class="label">Topics You'll Cover * <span class="dim">(pick at least one)</span></label>
          <div class="chips">
            <button
              v-for="t in allTopics"
              :key="t.id"
              type="button"
              class="chip-btn"
              :class="{ on: form.topic_ids.includes(t.id) }"
              @click="toggle(form.topic_ids, t.id)"
            >{{ t.name }}</button>
            <span v-if="!allTopics.length" class="label dim">Topics could not be loaded.</span>
          </div>
        </div>

        <div class="grid3">
          <div class="field">
            <label class="label">Max Members *</label>
            <div class="stepper">
              <button type="button" @click="form.max_members = Math.max(2, form.max_members - 1)">−</button>
              <span>{{ form.max_members }}</span>
              <button type="button" @click="form.max_members = Math.min(10, form.max_members + 1)">+</button>
            </div>
          </div>
          <div class="field">
            <label class="label">Study Pace / Goal *</label>
            <select v-model="form.pace">
              <option v-for="p in paces" :key="p" :value="p">{{ p }}</option>
            </select>
          </div>
          <div class="field">
            <label class="label">Meeting Mode *</label>
            <div class="seg">
              <button
                v-for="m in modes"
                :key="m.value"
                type="button"
                :class="{ on: form.mode === m.value }"
                @click="form.mode = m.value"
              >{{ m.label }}</button>
            </div>
          </div>
        </div>

        <div class="grid2">
          <div class="field">
            <label class="label">Venue / Platform {{ form.mode === 'online' ? '' : '*' }}</label>
            <input v-model="form.venue" maxlength="120" type="text" placeholder="e.g. Library 3rd Floor / Discord" />
          </div>
          <div class="field">
            <label class="label">Meeting Link <span class="dim">(optional)</span></label>
            <input v-model="form.meeting_link" maxlength="300" type="url" placeholder="https://meet.google.com/..." />
          </div>
        </div>

        <div class="field">
          <label class="label">Study Days * <span class="dim">(pick at least one)</span></label>
          <div class="chips">
            <button
              v-for="d in days"
              :key="d"
              type="button"
              class="chip-btn"
              :class="{ on: form.study_days.includes(d) }"
              @click="toggle(form.study_days, d)"
            >{{ d }}</button>
          </div>
        </div>

        <div class="grid3">
          <div class="field">
            <label class="label">From *</label>
            <select v-model.number="form.start_hour">
              <option v-for="h in hours" :key="'s' + h" :value="h">{{ fmtHour(h) }}</option>
            </select>
          </div>
          <div class="field">
            <label class="label">To *</label>
            <select v-model.number="form.end_hour">
              <option v-for="h in hours" :key="'e' + h" :value="h">{{ fmtHour(h) }}</option>
            </select>
          </div>
          <div class="field summary">
            <label class="label">Preview</label>
            <p>
              <b>{{ form.name || 'Your team' }}</b> · {{ form.max_members }} seats ·
              {{ form.study_days.length ? form.study_days.join('/') : 'no days' }}
              {{ fmtHour(form.start_hour) }}–{{ fmtHour(form.end_hour) }}
            </p>
          </div>
        </div>

        <div class="actions">
          <span class="label dim">You'll be added as the first member automatically.</span>
          <div>
            <button type="button" class="btn-ghost" @click="resetForm">Reset</button>
            <button type="submit" class="btn-solid" :disabled="creating">{{ creating ? 'Creating...' : 'Create Team →' }}</button>
          </div>
        </div>
      </form>
    </section>

    <!-- ───────── EXISTING GROUPS ───────── -->
    <div v-if="loading" class="empty label dim">Loading study groups...</div>
    <div v-else-if="!filteredGroups.length" class="empty label dim">No groups found. Be the first to create one above ✦</div>

    <div v-else class="cards">
      <article v-for="group in filteredGroups" :key="group.id" class="card">
        <div class="card-img">
          <img v-if="group.image" :src="group.image" :alt="group.name" />
          <div v-else class="img-fallback wide">{{ (group.name || '?').charAt(0) }}</div>
          <div class="img-shade"></div>
          <div class="img-cap">
            <div class="flex items-center gap-2">
              <span class="box">{{ group.course }}</span>
              <span v-if="synergyMap[group.id] != null" class="synergy-tag">
                ✦ {{ synergyMap[group.id] }}% Synergy
              </span>
            </div>
            <h3 class="wide">{{ group.name }}</h3>
          </div>
        </div>

        <div class="card-body">
          <div>
            <div class="cap-row label">
              <span class="dim">Members Capacity</span>
              <b>{{ group.members_count }} / {{ group.max_members }}</b>
            </div>

            <div v-if="group.pace || group.mode" class="mini-tags">
              <span v-if="group.pace" class="box">{{ group.pace }}</span>
              <span v-if="group.mode" class="box">{{ group.mode }}</span>
            </div>
            <p v-if="group.description" class="desc">{{ group.description }}</p>
            <p v-if="group.study_days && group.study_days.length" class="meta label dim">
              {{ group.study_days.join(' · ') }}
              <template v-if="group.start_hour != null"> · {{ fmtHour(group.start_hour) }}–{{ fmtHour(group.end_hour) }}</template>
            </p>
            <p v-if="group.venue" class="meta label dim">{{ group.venue }}</p>

            <!-- Cohort 5-star Review Row -->
            <div class="rating-row label">
              <span class="dim">{{ ratingFor(group.id).can_review ? 'RATE THIS COHORT' : 'COHORT RATING' }}</span>
              <span class="star-wrapper">
                <StarRating
                  :model-value="ratingFor(group.id).can_review ? (ratingFor(group.id).my_rating || 0) : ratingFor(group.id).avg"
                  :readonly="!ratingFor(group.id).can_review"
                  :size="16"
                  @update:model-value="handleRateGroup(group.id, $event)"
                />
                <span class="rating-count">
                  {{ ratingFor(group.id).count ? ratingFor(group.id).avg.toFixed(1) + ' (' + ratingFor(group.id).count + ')' : 'No ratings' }}
                </span>
              </span>
            </div>

            <div class="members">
              <button
                v-for="m in group.members"
                :key="m.user_id"
                type="button"
                class="member member-btn"
                title="View / leave reviews for this student"
                @click="reviewTarget = { id: m.user_id, name: m.name, groupId: group.id, isCreator: group.created_by === currentUserId }"
              >
                {{ m.name }} <span class="star-mini">★</span>
              </button>
            </div>
          </div>

          <button
            v-if="isMemberOf(group)"
            class="btn-join btn-joined"
            disabled
          >
            ✓ Already Joined
          </button>
          <button
            v-else-if="outgoingStatuses[group.id] === 'pending'"
            class="btn-join btn-pending"
            disabled
          >
            ⏳ Request Pending Leader Review
          </button>
          <button
            v-else-if="group.members_count >= group.max_members"
            class="btn-join btn-full"
            disabled
          >
            Cohort Full
          </button>
          <button
            v-else
            class="btn-join"
            @click="handleJoin(group.id)"
          >
            Request to Join Cohort
          </button>
        </div>
      </article>
    </div>

    <!-- Peer Review Modal -->
    <ReviewModal
      v-if="reviewTarget"
      :user-id="reviewTarget.id"
      :name="reviewTarget.name"
      :group-id="reviewTarget.groupId"
      :can-remove="reviewTarget.isCreator"
      @close="reviewTarget = null"
      @member-removed="onMemberRemoved"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import {
  getGroups, joinGroup, getTopics, createGroup, getMe,
  getGroupReviewSummary, postGroupReview,
  getMyGroupRequests, respondToJoinRequest, getWheelSuggestions
} from '../api.js';
import StarRating from '../components/StarRating.vue';
import ReviewModal from '../components/ReviewModal.vue';

const groups = ref([]);
const allTopics = ref([]);
const loading = ref(true);
const searchQuery = ref('');
const sortBy = ref('synergy');
const synergyMap = ref({});
const toastMessage = ref('');
const currentUserId = ref(null);
const groupRatings = ref({});
const reviewTarget = ref(null);
const incomingRequests = ref([]);
const outgoingStatuses = ref({});

const open = ref(false);
const creating = ref(false);
const formError = ref('');

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const hours = Array.from({ length: 16 }, (_, i) => i + 7); // 7:00 .. 22:00
const paces = ['Exam prep', 'Project sprint', 'Assignment help', 'Deep dive', 'Casual revision'];
const modes = [
  { value: 'online', label: 'Online' },
  { value: 'in-person', label: 'In-person' },
  { value: 'hybrid', label: 'Hybrid' },
];

const blank = () => ({
  name: '', course: '', description: '', topic_ids: [],
  max_members: 5, pace: 'Exam prep', mode: 'hybrid',
  venue: '', meeting_link: '', study_days: [], start_hour: 14, end_hour: 17,
});
const form = reactive(blank());

const fmtHour = (h) => `${String(h).padStart(2, '0')}:00`;
function toggle(list, value) {
  const i = list.indexOf(value);
  i === -1 ? list.push(value) : list.splice(i, 1);
}
function resetForm() {
  Object.assign(form, blank());
  formError.value = '';
}

function validate() {
  if (form.name.trim().length < 3) return 'Team name must be at least 3 characters.';
  if (form.course.trim().length < 2) return 'Please enter the course.';
  if (!form.topic_ids.length) return 'Pick at least one topic.';
  if (form.mode !== 'online' && !form.venue.trim()) return 'Add a venue for in-person or hybrid teams.';
  if (form.meeting_link.trim() && !/^https?:\/\//i.test(form.meeting_link.trim())) return 'Meeting link must start with http:// or https://';
  if (!form.study_days.length) return 'Pick at least one study day.';
  if (form.end_hour <= form.start_hour) return 'End time must be after start time.';
  return '';
}

async function submit() {
  formError.value = validate();
  if (formError.value) return;

  creating.value = true;
  try {
    await createGroup({
      name: form.name.trim(),
      course: form.course.trim(),
      description: form.description.trim(),
      topic_ids: form.topic_ids,
      max_members: form.max_members,
      pace: form.pace,
      mode: form.mode,
      venue: form.venue.trim(),
      meeting_link: form.meeting_link.trim(),
      study_days: form.study_days,
      start_hour: form.start_hour,
      end_hour: form.end_hour,
    });
    toastMessage.value = `Team "${form.name.trim()}" created. You're the first member!`;
    resetForm();
    open.value = false;
    await loadGroups();
  } catch (err) {
    formError.value = err.message;
  } finally {
    creating.value = false;
  }
}

const filteredGroups = computed(() => {
  const q = searchQuery.value.toLowerCase().trim();
  let list = groups.value;
  if (q) {
    list = list.filter(g =>
      g.name.toLowerCase().includes(q) || (g.course || '').toLowerCase().includes(q)
    );
  }

  return [...list].sort((a, b) => {
    if (sortBy.value === 'synergy') {
      const scoreA = Number(synergyMap.value[a.id]) || 0;
      const scoreB = Number(synergyMap.value[b.id]) || 0;
      return scoreB - scoreA;
    } else if (sortBy.value === 'rating') {
      const ratA = ratingFor(a.id).avg || 0;
      const ratB = ratingFor(b.id).avg || 0;
      return ratB - ratA;
    } else if (sortBy.value === 'openings') {
      const openA = Math.max(a.max_members - a.members_count, 0);
      const openB = Math.max(b.max_members - b.members_count, 0);
      return openB - openA;
    } else if (sortBy.value === 'name') {
      return a.name.localeCompare(b.name);
    }
    return 0;
  });
});

async function loadGroupRatings() {
  try {
    const list = await getGroupReviewSummary();
    const map = {};
    for (const item of list) {
      map[item.group_id] = item;
    }
    groupRatings.value = map;
  } catch (err) {
    console.error('Could not load group ratings', err);
  }
}

function isMemberOf(group) {
  if (!currentUserId.value || !group.members) return false;
  return group.members.some(m => m.user_id === currentUserId.value);
}

function ratingFor(groupId) {
  return groupRatings.value[groupId] || { avg: 0, count: 0, my_rating: null, can_review: false };
}

async function handleRateGroup(groupId, rating) {
  try {
    const updated = await postGroupReview(groupId, rating);
    groupRatings.value[groupId] = {
      ...ratingFor(groupId),
      avg: updated.avg,
      count: updated.count,
      my_rating: updated.my_rating,
    };
    toastMessage.value = `Rated cohort ${rating} stars!`;
  } catch (err) {
    toastMessage.value = err.message;
  }
}

async function onMemberRemoved() {
  reviewTarget.value = null;
  toastMessage.value = "Member updated / removed from group.";
  await loadGroups();
}

async function loadGroups() {
  loading.value = true;
  try { groups.value = await getGroups(); }
  catch (err) { console.error(err); }
  finally { loading.value = false; }
}

async function loadRequests() {
  try {
    const data = await getMyGroupRequests();
    incomingRequests.value = data.incoming_requests || [];
    outgoingStatuses.value = data.my_outgoing_statuses || {};
  } catch (err) {
    console.error("Could not load group requests", err);
  }
}

async function handleRequestAction(requestId, action) {
  try {
    const res = await respondToJoinRequest(requestId, action);
    toastMessage.value = res.message;
    await loadRequests();
    await loadGroups();
  } catch (err) {
    toastMessage.value = err.message;
  }
}

async function handleJoin(groupId) {
  try {
    const res = await joinGroup(groupId);
    toastMessage.value = res.message;
    await loadGroups();
    await loadGroupRatings();
    await loadRequests();
  } catch (err) {
    toastMessage.value = err.message;
  }
}

async function loadSynergyScores() {
  try {
    const list = await getWheelSuggestions();
    const map = {};
    for (const item of list) {
      map[item.id] = item.match_score;
    }
    synergyMap.value = map;
  } catch (err) {
    console.error("Could not load synergy scores", err);
  }
}

onMounted(async () => {
  try {
    const me = await getMe();
    currentUserId.value = me.id;
  } catch (err) {
    console.error(err);
  }
  await loadGroups();
  await loadSynergyScores();
  await loadGroupRatings();
  await loadRequests();
  try { allTopics.value = await getTopics(); } catch (err) { console.error(err); }
});
</script>

<style scoped>
.ss-teams { flex:1; min-width:0; width:100%; max-width:1200px; margin:0 auto; padding:28px 32px 40px; overflow-y:auto; position:relative; z-index:10; }
.wide { font-family:'Syne',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:.01em; }
.label { font-size:11px; letter-spacing:.2em; text-transform:uppercase; }
.dim { color:var(--dim); }
.box { border:1px solid var(--line); padding:2px 8px; font-size:10px; letter-spacing:.14em; text-transform:uppercase; background:rgba(0,0,0,.6); }

.page-head { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; flex-wrap:wrap; padding-bottom:16px; margin-bottom:20px; border-bottom:1px solid var(--line); }
.tag-solid { background:var(--pink); color:#000; font-family:'Syne',sans-serif; font-weight:700; padding:2px 8px; font-size:10px; letter-spacing:.2em; }
.page-head h1 { font-size:clamp(26px,3.2vw,40px); line-height:1.05; margin-top:8px; text-shadow:0 2px 12px rgba(0,0,0,.8); }
.page-head p { font-size:13px; margin-top:6px; }

.head-controls { display:flex; align-items:center; gap:12px; flex-wrap:wrap; }
.sort-box { display:flex; align-items:center; gap:8px; border:1px solid var(--line); background:rgba(0,0,0,.7); padding:4px 10px; }
.sort-label { font-size:10px; letter-spacing:.15em; text-transform:uppercase; color:var(--dim); white-space:nowrap; }
.sort-select { background:transparent; border:none; color:var(--pink); font-family:'Syne',sans-serif; font-size:11px; font-weight:700; text-transform:uppercase; outline:none; cursor:pointer; }
.sort-select option { background:#08080f; color:#fff; }

.synergy-tag { border:1px solid #ffa6e6; background:#ffa6e6; color:#000; font-family:'Syne',sans-serif; font-weight:800; font-size:9px; letter-spacing:.1em; text-transform:uppercase; padding:2px 6px; }

.search { width:100%; max-width:280px; background:rgba(0,0,0,.7); border:1px solid var(--line); color:#fff; padding:10px 12px; font:inherit; font-size:13px; outline:none; }
.search:focus { box-shadow:0 0 0 1px var(--pink); }

.toast { margin-bottom:16px; border:1px solid var(--line); background:rgba(0,0,0,.8); padding:10px 14px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center; gap:16px; }
.toast-x { border:none; background:transparent; color:var(--pink); }

.panel { border:1px solid var(--line); background:rgba(6,4,8,.78); backdrop-filter:blur(10px); margin-bottom:28px; }
.create-bar { width:100%; display:flex; align-items:center; gap:20px; padding:18px 24px; border:none; background:rgba(0,0,0,.5); color:var(--pink); text-align:left; }
.create-bar:hover { background:rgba(255,166,230,.12); }
.create-title { font-size:20px; }
.create-bar .label { flex:1; }
.create-plus { font-family:'Syne',sans-serif; font-size:28px; font-weight:800; line-height:1; }

.form { padding:24px; border-top:1px solid var(--line); display:flex; flex-direction:column; gap:20px; }
.form-error { border:1px solid var(--line); background:rgba(255,166,230,.12); padding:10px 14px; font-size:12px; letter-spacing:.06em; text-transform:uppercase; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.grid3 { display:grid; grid-template-columns:1fr 1fr 1.4fr; gap:16px; }
.field { display:flex; flex-direction:column; gap:8px; min-width:0; }
.field input, .field select, .field textarea { background:rgba(8,8,14,.75); border:1px solid rgba(255,166,230,.4); color:var(--pink); padding:11px 14px; font:inherit; font-size:14px; outline:none; width:100%; }
.field textarea { resize:vertical; }
.field input:focus, .field select:focus, .field textarea:focus { border-color:var(--pink); box-shadow:0 0 0 1px var(--pink); }
.field input::placeholder, .field textarea::placeholder { color:rgba(255,166,230,.3); }
.field select option { background:#000; color:var(--pink); }

.chips { display:flex; flex-wrap:wrap; gap:8px; }
.chip-btn { border:1px solid rgba(255,166,230,.5); background:transparent; color:var(--pink); padding:7px 12px; font-size:12px; letter-spacing:.06em; text-transform:uppercase; }
.chip-btn:hover { border-color:var(--pink); }
.chip-btn.on { background:var(--pink); color:#000; border-color:var(--pink); font-weight:700; }

.stepper { display:flex; align-items:stretch; border:1px solid rgba(255,166,230,.4); }
.stepper button { width:44px; border:none; background:transparent; color:var(--pink); font-size:18px; }
.stepper button:hover { background:rgba(255,166,230,.2); }
.stepper span { flex:1; display:flex; align-items:center; justify-content:center; font-family:'Syne',sans-serif; font-weight:800; font-size:18px; border-left:1px solid rgba(255,166,230,.4); border-right:1px solid rgba(255,166,230,.4); }
.seg { display:flex; border:1px solid rgba(255,166,230,.4); }
.seg button { flex:1; padding:11px 6px; border:none; background:transparent; color:var(--pink); font-size:11px; letter-spacing:.12em; text-transform:uppercase; }
.seg button + button { border-left:1px solid rgba(255,166,230,.4); }
.seg button.on { background:var(--pink); color:#000; font-weight:700; }
.summary p { font-size:13px; line-height:1.5; border:1px dashed rgba(255,166,230,.4); padding:10px 12px; }

.actions { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; padding-top:16px; border-top:1px solid var(--line); }
.actions > div { display:flex; gap:12px; }
.btn-ghost, .btn-solid { padding:13px 24px; font-size:12px; letter-spacing:.16em; text-transform:uppercase; font-weight:700; border:1px solid var(--pink); }
.btn-ghost { background:transparent; color:var(--pink); }
.btn-ghost:hover { background:rgba(255,166,230,.2); }
.btn-solid { background:var(--pink); color:#000; }
.btn-solid:hover:not(:disabled) { background:#fff; }
.btn-solid:disabled { opacity:.5; cursor:default; }

.empty { text-align:center; padding:48px 0; }
.cards { display:grid; grid-template-columns:repeat(3,1fr); gap:24px; }
.card { border:1px solid rgba(255,166,230,.6); background:rgba(6,4,8,.78); backdrop-filter:blur(10px); display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; }
.card:hover { border-color:var(--pink); }
.card-img { height:144px; position:relative; overflow:hidden; background:#111; }
.card-img img { width:100%; height:100%; object-fit:cover; filter:grayscale(1) contrast(1.05); display:block; }
.img-fallback { width:100%; height:100%; display:flex; align-items:center; justify-content:center; font-size:56px; color:rgba(255,166,230,.35); }
.img-shade { position:absolute; inset:0; background:linear-gradient(to top, #000, rgba(0,0,0,.4), transparent); }
.img-cap { position:absolute; left:12px; right:12px; bottom:12px; }
.img-cap h3 { font-size:20px; color:#fff; margin-top:6px; }
.card-body { padding:18px; flex:1; display:flex; flex-direction:column; justify-content:space-between; gap:16px; }
.cap-row { display:flex; justify-content:space-between; margin-bottom:12px; }
.mini-tags { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
.desc { font-size:13px; line-height:1.5; color:rgba(255,255,255,.8); margin-bottom:10px; }
.meta { font-size:10px; margin-bottom:6px; }
.members { display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }
.member { border:1px solid rgba(255,166,230,.4); background:rgba(0,0,0,.6); padding:2px 8px; font-size:11px; color:rgba(255,255,255,.85); }
.member-btn { cursor:pointer; display:inline-flex; align-items:center; gap:4px; transition:border-color .2s, color .2s; }
.member-btn:hover { border-color:var(--pink); color:var(--pink); }
.star-mini { color:#f59e0b; font-size:11px; opacity:.95; }

.rating-row { display:flex; justify-content:space-between; align-items:center; margin-top:12px; margin-bottom:4px; padding-top:10px; border-top:1px dashed rgba(255,166,230,.25); }
.star-wrapper { display:inline-flex; align-items:center; gap:8px; }
.rating-count { font-size:10px; color:rgba(255,166,230,.8); letter-spacing:0; }

.btn-join { width:100%; padding:11px; border:1px solid var(--pink); background:rgba(255,166,230,.1); color:var(--pink); font-family:'Syne',sans-serif; font-weight:700; font-size:12px; letter-spacing:.14em; text-transform:uppercase; transition:all .2s; }
.btn-join:hover:not(:disabled) { background:var(--pink); color:#000; }
.btn-joined { border-color:rgba(255,166,230,.3); background:rgba(255,166,230,.06); color:rgba(255,166,230,.7); cursor:default; }
.btn-full { border-color:rgba(255,255,255,.2); background:rgba(0,0,0,.5); color:rgba(255,255,255,.4); cursor:default; }
.btn-pending { border-color:rgba(245,158,11,.6); background:rgba(245,158,11,.1); color:#f59e0b; cursor:default; }

/* Incoming Requests Panel */
.requests-panel { border-color:#f59e0b; background:rgba(20,14,5,.85); margin-bottom:24px; box-shadow:0 0 20px rgba(245,158,11,.15); }
.requests-head { padding:18px 24px; border-bottom:1px solid rgba(245,158,11,.3); }
.tag-alert { background:#f59e0b; color:#000; font-family:'Syne',sans-serif; font-weight:800; padding:2px 8px; font-size:10px; letter-spacing:.16em; }
.req-title { font-size:22px; color:#f59e0b; margin-top:8px; }
.req-sub { font-size:12px; margin-top:4px; }
.requests-list { padding:16px 24px; display:flex; flex-direction:column; gap:14px; }
.request-item { display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap; border:1px solid rgba(245,158,11,.3); background:rgba(0,0,0,.6); padding:14px 18px; }
.req-name-row { display:flex; align-items:center; gap:10px; }
.req-user-name { font-family:'Syne',sans-serif; font-weight:700; font-size:16px; color:#fff; }
.req-group-tag { border:1px solid var(--pink); color:var(--pink); background:rgba(255,166,230,.1); padding:2px 6px; font-size:10px; text-transform:uppercase; letter-spacing:.1em; }
.req-major { font-size:11px; margin-top:2px; }
.req-topics { display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; }
.req-topic-badge { border:1px solid rgba(255,255,255,.2); background:rgba(0,0,0,.4); padding:2px 6px; font-size:10px; color:rgba(255,255,255,.8); }
.star-gold { color:#f59e0b; }
.req-actions { display:flex; gap:10px; }
.btn-req-accept, .btn-req-reject { font-family:'Syne',sans-serif; font-weight:700; font-size:11px; letter-spacing:.12em; text-transform:uppercase; padding:8px 16px; border:1px solid; cursor:pointer; transition:all .2s; }
.btn-req-accept { background:#f59e0b; color:#000; border-color:#f59e0b; }
.btn-req-accept:hover { background:#fff; border-color:#fff; }
.btn-req-reject { background:transparent; color:#ef4444; border-color:#ef4444; }
.btn-req-reject:hover { background:#ef4444; color:#000; }

@media (max-width:1023px) { .cards { grid-template-columns:1fr 1fr; } .grid3 { grid-template-columns:1fr 1fr; } }
@media (max-width:640px) { .ss-teams { padding:20px 16px 32px; } .cards, .grid2, .grid3 { grid-template-columns:1fr; } .create-bar .label { display:none; } }
</style>

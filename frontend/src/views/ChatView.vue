<template>
  <div class="ss-chat">
    <div class="chat-title">
      <h1 class="wide">Cohort Messages <em>Chat</em></h1>
      <p class="dim">Talk to the teams you've joined. Plan sessions, share notes, stay in sync.</p>
    </div>

    <div v-if="error" class="chat-error">{{ error }}</div>

    <div v-if="loadingGroups" class="empty label dim">Loading your cohorts...</div>

    <div v-else-if="!groups.length" class="empty label dim">
      You haven't joined a cohort yet. Join one from the Dashboard to start chatting.
    </div>

    <div v-else class="chat-grid">
      <!-- Left: my cohorts -->
      <aside class="panel list">
        <div class="panel-head label">Your Cohorts · {{ groups.length }}</div>
        <button
          v-for="g in groups"
          :key="g.id"
          class="row"
          :class="{ on: g.id === activeId }"
          @click="selectGroup(g.id)"
        >
          <span class="row-name wide">{{ g.name }}</span>
          <span class="row-course label">{{ g.course }}</span>
          <span class="row-last">
            <template v-if="g.last_message">{{ g.last_message.user_name.split(' ')[0] }}: {{ g.last_message.text }}</template>
            <template v-else>No messages yet</template>
          </span>
        </button>
      </aside>

      <!-- Right: conversation -->
      <section class="panel convo" v-if="activeGroup">
        <div class="panel-head convo-head">
          <div>
            <div class="wide convo-name">{{ activeGroup.name }}</div>
            <div class="label dim">{{ activeGroup.course }} · {{ activeGroup.members_count }} members</div>
          </div>
          <span class="live label"><i></i> Live</span>
        </div>

        <div ref="listEl" class="messages">
          <div v-if="!messages.length && !loadingMsgs" class="empty label dim">
            No messages yet. Say hi to your cohort ✦
          </div>

          <template v-for="(m, i) in messages" :key="m.id">
            <div v-if="showDay(i)" class="day label dim">{{ dayLabel(m.created_at) }}</div>
            <div class="msg" :class="{ mine: isMine(m) }">
              <div class="meta label">
                <span>{{ isMine(m) ? 'You' : m.user_name }}</span>
                <span class="dim">{{ time(m.created_at) }}</span>
                <button v-if="isMine(m)" class="del" title="Delete message" @click="remove(m)">✕</button>
              </div>
              <div class="bubble">{{ m.text }}</div>
            </div>
          </template>
        </div>

        <div class="composer">
          <textarea
            v-model="draft"
            rows="1"
            maxlength="1000"
            placeholder="Type a message — Enter to send, Shift+Enter for new line"
            @keydown.enter.exact.prevent="send"
          ></textarea>
          <button class="send" :disabled="sending || !draft.trim()" @click="send">
            {{ sending ? '...' : 'Send →' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue';
import { getChatGroups, getMessages, sendMessage, deleteMessage } from '../api.js';

const props = defineProps({ user: Object });

const POLL_MS = 3000;

const groups = ref([]);
const activeId = ref(null);
const messages = ref([]);
const draft = ref('');
const loadingGroups = ref(true);
const loadingMsgs = ref(false);
const sending = ref(false);
const error = ref('');
const listEl = ref(null);
let timer = null;

const activeGroup = computed(() => groups.value.find(g => g.id === activeId.value) || null);
const isMine = (m) => m.user_id === props.user?.id;

// ---------- formatting ----------
const time = (iso) => new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const dayKey = (iso) => new Date(iso).toDateString();
function dayLabel(iso) {
  const d = new Date(iso);
  const today = new Date();
  const yest = new Date(); yest.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yest.toDateString()) return 'Yesterday';
  return d.toLocaleDateString([], { day: 'numeric', month: 'short', year: 'numeric' });
}
const showDay = (i) => i === 0 || dayKey(messages.value[i].created_at) !== dayKey(messages.value[i - 1].created_at);

// ---------- scrolling ----------
function nearBottom() {
  const el = listEl.value;
  return !el || el.scrollHeight - el.scrollTop - el.clientHeight < 80;
}
async function scrollBottom() {
  await nextTick();
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight;
}

// ---------- data ----------
async function loadGroups() {
  try {
    groups.value = await getChatGroups();
    if (groups.value.length && !activeId.value) await selectGroup(groups.value[0].id);
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingGroups.value = false;
  }
}

async function selectGroup(id) {
  activeId.value = id;
  messages.value = [];
  error.value = '';
  loadingMsgs.value = true;
  try {
    const data = await getMessages(id);
    if (activeId.value !== id) return; // switched while loading
    messages.value = data;
    await scrollBottom();
  } catch (err) {
    error.value = err.message;
  } finally {
    loadingMsgs.value = false;
  }
}

function touchPreview(msg) {
  const g = groups.value.find(x => x.id === activeId.value);
  if (g) g.last_message = { text: msg.text, user_name: msg.user_name, created_at: msg.created_at };
}

async function poll() {
  const id = activeId.value;
  if (!id || document.hidden) return;
  const last = messages.value.length ? messages.value[messages.value.length - 1].id : 0;
  try {
    const fresh = await getMessages(id, last);
    if (id !== activeId.value) return;
    const known = new Set(messages.value.map(m => m.id));
    const add = fresh.filter(m => !known.has(m.id));
    if (add.length) {
      const stick = nearBottom();
      messages.value.push(...add);
      touchPreview(add[add.length - 1]);
      if (stick) scrollBottom();
    }
  } catch (err) {
    /* ignore a missed poll; the next one retries */
  }
}

async function send() {
  const text = draft.value.trim();
  if (!text || sending.value || !activeId.value) return;
  sending.value = true;
  error.value = '';
  try {
    const msg = await sendMessage(activeId.value, text);
    draft.value = '';
    if (!messages.value.some(m => m.id === msg.id)) messages.value.push(msg);
    touchPreview(msg);
    scrollBottom();
  } catch (err) {
    error.value = err.message;
  } finally {
    sending.value = false;
  }
}

async function remove(m) {
  try {
    await deleteMessage(m.id);
    messages.value = messages.value.filter(x => x.id !== m.id);
  } catch (err) {
    error.value = err.message;
  }
}

onMounted(() => {
  loadGroups();
  timer = setInterval(poll, POLL_MS);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.ss-chat { flex:1; min-width:0; min-height:0; width:100%; max-width:1560px; margin:0 auto; padding:24px 32px 20px; display:flex; flex-direction:column; position:relative; z-index:10; }
.wide { font-family:'Syne',sans-serif; font-weight:800; text-transform:uppercase; letter-spacing:.01em; }
.label { font-size:11px; letter-spacing:.2em; text-transform:uppercase; }
.dim { color:var(--dim); }

.chat-title { margin-bottom:18px; flex-shrink:0; }
.chat-title h1 { font-size:clamp(26px,3.4vw,44px); line-height:1; display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; text-shadow:0 2px 12px rgba(0,0,0,.8); }
.chat-title h1 em { font-family:'Instrument Serif',serif; font-style:italic; font-weight:400; text-transform:none; font-size:1.2em; }
.chat-title p { margin-top:8px; font-size:13px; }
.chat-error { margin-bottom:12px; border:1px solid var(--line); background:rgba(0,0,0,.8); padding:10px 14px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; }
.empty { margin:auto; text-align:center; padding:24px; }

.chat-grid { flex:1; min-height:0; display:grid; grid-template-columns:320px 1fr; gap:24px; }
.panel { border:1px solid var(--line); background:rgba(6,4,8,.78); backdrop-filter:blur(10px); display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.panel-head { padding:14px 20px; border-bottom:1px solid var(--line); background:rgba(0,0,0,.5); flex-shrink:0; }

.list { overflow-y:auto; }
.row { display:flex; flex-direction:column; gap:4px; text-align:left; padding:14px 20px; border:none; border-bottom:1px solid rgba(255,166,230,.25); background:transparent; color:var(--pink); width:100%; }
.row:hover { background:rgba(255,166,230,.12); }
.row.on { background:var(--pink); color:#000; }
.row-name { font-size:15px; }
.row-course { font-size:10px; opacity:.7; }
.row-last { font-size:12px; opacity:.8; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.convo-head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
.convo-name { font-size:20px; line-height:1.1; }
.live { display:flex; align-items:center; gap:8px; border:1px solid var(--line); padding:3px 10px; }
.live i { width:7px; height:7px; background:var(--pink); animation:ss-blink 1.4s infinite; }
@keyframes ss-blink { 50% { opacity:.25; } }

.messages { flex:1; min-height:0; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:14px; }
.day { text-align:center; padding:4px 0; }
.day::before, .day::after { content:"—"; margin:0 10px; opacity:.5; }
.msg { display:flex; flex-direction:column; gap:4px; max-width:72%; align-self:flex-start; }
.msg.mine { align-self:flex-end; align-items:flex-end; }
.meta { display:flex; align-items:center; gap:10px; font-size:10px; }
.bubble { border:1px solid var(--line); background:rgba(0,0,0,.6); padding:10px 14px; font-size:14px; line-height:1.5; white-space:pre-wrap; word-break:break-word; }
.msg.mine .bubble { background:var(--pink); color:#000; font-weight:500; }
.del { border:none; background:transparent; color:var(--dim); padding:0 2px; font-size:11px; }
.del:hover { color:var(--pink); }

.composer { display:flex; gap:12px; padding:14px 20px; border-top:1px solid var(--line); background:rgba(0,0,0,.5); flex-shrink:0; }
.composer textarea { flex:1; resize:none; background:rgba(8,8,14,.75); border:1px solid rgba(255,166,230,.4); color:var(--pink); padding:12px 14px; font-family:inherit; font-size:14px; outline:none; max-height:120px; }
.composer textarea:focus { border-color:var(--pink); box-shadow:0 0 0 1px var(--pink); }
.composer textarea::placeholder { color:rgba(255,166,230,.35); }
.send { border:1px solid var(--pink); background:var(--pink); color:#000; padding:0 22px; text-transform:uppercase; letter-spacing:.16em; font-weight:700; font-size:12px; }
.send:hover:not(:disabled) { background:#fff; }
.send:disabled { opacity:.45; cursor:default; }

@media (max-width:1023px) {
  .ss-chat { overflow:auto; padding:16px; }
  .chat-grid { grid-template-columns:1fr; }
  .list { max-height:200px; }
  .convo { min-height:480px; }
  .msg { max-width:90%; }
}
</style>

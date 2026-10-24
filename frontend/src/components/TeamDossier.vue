<template>
  <template v-if="team">
    <div class="detail-top">
      <div class="head">
        <div>
          <div class="tags">
            <span class="box">{{ team.course }}</span>
            <span v-if="team.section" class="label dim">{{ team.section }}</span>
          </div>
          <h2 class="wide" id="detailTeamName">{{ team.label }}</h2>
        </div>
        <div class="score">✦ {{ team.match_score }}% Synergy Match</div>
      </div>

      <div class="stats">
        <div class="grp">
          <div style="display:flex">
            <span v-for="m in memberList" :key="m" class="av" :title="m">{{ m.charAt(0).toUpperCase() }}</span>
          </div>
          <div>
            <b>{{ team.members_count }}/{{ team.max_members }} Members Seated</b>
            <small>{{ Math.max(team.max_members - team.members_count, 0) }} openings left in study cohort</small>
          </div>
        </div>
        <div>
          <b>{{ team.overlapping_hours }} shared free hours</b>
          <small>Calculated this week</small>
        </div>
      </div>

      <div>
        <p class="label dim">Skill Synergy Balancing</p>
        <div class="pills">
          <div class="pill"><span class="label">↓ Cohort Needs Help</span><p>{{ team.weak_topic || '—' }}</p></div>
          <div class="pill"><span class="label">↑ Cohort Excels In</span><p>{{ team.strong_topic || '—' }}</p></div>
        </div>
      </div>

      <div class="why">
        <h4>✦ Why Matched With {{ firstName }} <span>Mutual Reciprocity</span></h4>
        <p>{{ team.why_matched }}</p>
        <div class="meta">
          <span>{{ team.venue || 'Olin Library VIP Room / Discord' }}</span>
          <span>● {{ team.pace || 'Prelim 2 Grind Pace' }}</span>
        </div>
      </div>
    </div>

    <div class="cta">
      <button id="joinTeamBtn" :disabled="joining" @click="$emit('join', team.id)">
        ✦ {{ joining ? 'Joining...' : 'Join ' + team.label }}
      </button>
      <button id="nextTeamBtn" @click="$emit('next')">Next / Reroll →</button>
    </div>
  </template>

  <div v-else class="empty label dim">Select a team from the wheel</div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  team: Object,
  joining: Boolean,
  userName: { type: String, default: '' },
});
defineEmits(['join', 'next']);

const firstName = computed(() => (props.userName || 'you').split(' ')[0]);
const memberList = computed(() => (props.team?.members || []).map(m => (typeof m === 'string' ? m : m.name || '?')));
</script>

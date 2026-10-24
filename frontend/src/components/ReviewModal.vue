<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-4" @click.self="$emit('close')">
    <div class="w-full max-w-md max-h-[85vh] flex flex-col border border-[#ffa6e6] bg-[#0c080f] shadow-[0_0_30px_rgba(255,166,230,0.2)]">
      <!-- Header -->
      <div class="flex items-start justify-between border-b border-[#ffa6e6]/60 p-4">
        <div>
          <span class="border border-[#ffa6e6] bg-[#ffa6e6] text-black font-syne font-bold px-2 py-0.5 text-[10px] tracking-widest uppercase">Peer Reviews</span>
          <h3 class="font-syne font-extrabold text-xl uppercase text-white mt-1">{{ name }}</h3>
          <div v-if="data" class="flex items-center gap-2 mt-1 text-xs text-[#ffa6e6]/80">
            <StarRating :model-value="data.avg" readonly :size="14" />
            <span v-if="data.count">{{ data.avg.toFixed(1) }} · {{ data.count }} review{{ data.count === 1 ? '' : 's' }}</span>
            <span v-else>No reviews yet</span>
          </div>
        </div>
        <button class="text-[#ffa6e6] hover:text-white text-lg leading-none" @click="$emit('close')">✕</button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-if="loading" class="text-center text-xs text-[#ffa6e6]/50 py-6">Loading reviews...</div>
        <div v-else-if="error" class="border border-red-400 bg-red-950/60 text-red-200 p-2 text-xs">{{ error }}</div>

        <template v-else-if="data">
          <!-- Write / edit form (backend decides can_review: must share a group, not yourself) -->
          <div v-if="data.can_review" class="border border-[#ffa6e6]/40 p-3 space-y-2">
            <p class="text-[10px] uppercase tracking-widest text-[#ffa6e6]/70">
              {{ data.my_review ? 'Edit your review' : 'Leave a review' }}
            </p>
            <StarRating v-model="rating" :size="22" />
            <textarea
              v-model="comment"
              maxlength="500"
              rows="3"
              placeholder="How are they to study with? (optional)"
              class="w-full bg-black border border-[#ffa6e6]/60 p-2 text-xs text-white focus:outline-none focus:border-[#ffa6e6] resize-none"
            ></textarea>
            <div class="flex items-center justify-between gap-2">
              <span class="text-[10px] text-[#ffa6e6]/50">{{ comment.length }}/500</span>
              <div class="flex gap-2">
                <button
                  v-if="data.my_review"
                  class="border border-[#ffa6e6]/40 px-3 py-1.5 text-[10px] uppercase tracking-wider text-[#ffa6e6]/80 hover:border-[#ffa6e6]"
                  :disabled="saving"
                  @click="remove"
                >Delete</button>
                <button
                  class="border border-[#ffa6e6] bg-[#ffa6e6]/10 text-[#ffa6e6] hover:bg-[#ffa6e6] hover:text-black font-syne font-bold px-4 py-1.5 text-[10px] uppercase tracking-wider disabled:opacity-40"
                  :disabled="!rating || saving"
                  @click="save"
                >{{ saving ? 'Saving...' : 'Submit' }}</button>
              </div>
            </div>
          </div>
          <p v-else class="text-[11px] text-[#ffa6e6]/50">
            You can review people once you share a study group with them.
          </p>

          <!-- Group Leader Action: Remove / Reject member from group -->
          <div v-if="canRemove && groupId" class="border border-red-500/40 bg-red-950/20 p-3 space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-[10px] uppercase tracking-widest text-red-400 font-bold">Team Management</p>
                <p class="text-[11px] text-white/70">Remove this student from the cohort?</p>
              </div>
              <button
                class="border border-red-500 bg-red-500/10 text-red-300 hover:bg-red-500 hover:text-black font-syne font-bold px-3 py-1 text-[10px] uppercase tracking-wider transition-all disabled:opacity-40"
                :disabled="removingMember"
                @click="removeStudentFromGroup"
              >
                {{ removingMember ? 'Removing...' : 'Remove / Reject Member' }}
              </button>
            </div>
          </div>

          <!-- Existing reviews -->
          <div v-if="data.reviews.length" class="space-y-3">
            <div v-for="r in data.reviews" :key="r.id" class="border-t border-[#ffa6e6]/20 pt-3">
              <div class="flex items-center justify-between text-xs">
                <span class="text-white/90">{{ r.is_mine ? 'You' : r.reviewer_name }}</span>
                <StarRating :model-value="r.rating" readonly :size="12" />
              </div>
              <p v-if="r.comment" class="text-xs text-white/70 mt-1 whitespace-pre-wrap">{{ r.comment }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import StarRating from './StarRating.vue';
import { getMemberReviews, postMemberReview, deleteMemberReview, removeGroupMember } from '../api.js';

const props = defineProps({
  userId: Number,
  name: String,
  groupId: { type: Number, default: null },
  canRemove: { type: Boolean, default: false }
});
const emit = defineEmits(['close', 'member-removed']);

const data = ref(null);
const loading = ref(true);
const saving = ref(false);
const removingMember = ref(false);
const error = ref('');
const rating = ref(0);
const comment = ref('');

async function load() {
  loading.value = true;
  error.value = '';
  try {
    data.value = await getMemberReviews(props.userId);
    rating.value = data.value.my_review?.rating || 0;
    comment.value = data.value.my_review?.comment || '';
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  error.value = '';
  try {
    await postMemberReview(props.userId, rating.value, comment.value);
    await load();
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

async function remove() {
  saving.value = true;
  try {
    await deleteMemberReview(props.userId);
    rating.value = 0;
    comment.value = '';
    await load();
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

async function removeStudentFromGroup() {
  if (!confirm(`Are you sure you want to remove ${props.name} from this cohort?`)) return;
  removingMember.value = true;
  try {
    await removeGroupMember(props.groupId, props.userId);
    emit('member-removed');
  } catch (e) {
    error.value = e.message;
  } finally {
    removingMember.value = false;
  }
}

onMounted(load);
</script>

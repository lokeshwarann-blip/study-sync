const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

function getAuthHeader() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

export async function signupUser(name, email, password, major) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, major })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Signup failed");
  }
  return res.json();
}

export async function getMe() {
  const res = await fetch(`${API_BASE}/users/me`, {
    headers: { ...getAuthHeader() }
  });
  if (!res.ok) throw new Error("Failed to fetch user");
  return res.json();
}

export async function getTopics() {
  const res = await fetch(`${API_BASE}/topics`);
  if (!res.ok) throw new Error("Failed to fetch topics");
  return res.json();
}

export async function updateProfile(data) {
  const res = await fetch(`${API_BASE}/users/profile`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader()
    },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to update profile");
  return res.json();
}

export async function getWheelSuggestions() {
  const res = await fetch(`${API_BASE}/suggestions/wheel`, {
    headers: { ...getAuthHeader() }
  });
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function getGroups() {
  const res = await fetch(`${API_BASE}/groups`);
  if (!res.ok) throw new Error("Failed to fetch groups");
  return res.json();
}

export async function joinGroup(groupId) {
  const res = await fetch(`${API_BASE}/groups/${groupId}/join`, {
    method: "POST",
    headers: { ...getAuthHeader() }
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to join group");
  }
  return res.json();
}

// ───────────── Group chat ─────────────
async function chatFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...(options.headers || {})
    }
  });
  if (!res.ok) {
    let detail = "Request failed";
    try { detail = (await res.json()).detail || detail; } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

export const getChatGroups = () => chatFetch("/chat/groups");

export const getMessages = (groupId, afterId = 0) =>
  chatFetch(`/chat/groups/${groupId}/messages?after_id=${afterId}`);

export const sendMessage = (groupId, text) =>
  chatFetch(`/chat/groups/${groupId}/messages`, {
    method: "POST",
    body: JSON.stringify({ text })
  });

export const deleteMessage = (messageId) =>
  chatFetch(`/chat/messages/${messageId}`, { method: "DELETE" });

// ───────────── Create your own team ─────────────
export async function createGroup(data) {
  const res = await fetch(`${API_BASE}/groups`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeader() },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // FastAPI validation errors (422) come back as a list
    const detail = Array.isArray(err.detail)
      ? err.detail.map(d => d.msg).join(", ")
      : err.detail;
    throw new Error(detail || "Failed to create team");
  }
  return res.json();
}

// ───────────── Review System & Member Management ─────────────
async function reviewFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...(options.headers || {})
    }
  });
  if (!res.ok) {
    let detail = "Request failed";
    try { detail = (await res.json()).detail || detail; } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

export const getMemberReviews = (userId) => reviewFetch(`/reviews/members/${userId}`);
export const postMemberReview = (userId, rating, comment) =>
  reviewFetch(`/reviews/members/${userId}`, {
    method: "POST",
    body: JSON.stringify({ rating, comment })
  });
export const deleteMemberReview = (userId) =>
  reviewFetch(`/reviews/members/${userId}`, { method: "DELETE" });

export const getGroupReviewSummary = () => reviewFetch("/reviews/groups/summary");
export const postGroupReview = (groupId, rating) =>
  reviewFetch(`/reviews/groups/${groupId}`, {
    method: "POST",
    body: JSON.stringify({ rating })
  });

export const removeGroupMember = (groupId, userId) =>
  reviewFetch(`/reviews/groups/${groupId}/members/${userId}`, { method: "DELETE" });

export const getMyGroupRequests = () => reviewFetch("/groups/my-requests");
export const respondToJoinRequest = (requestId, action) =>
  reviewFetch(`/groups/requests/${requestId}/respond?action=${action}`, { method: "POST" });

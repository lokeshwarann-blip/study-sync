<template>
  <div class="relative w-full h-full overflow-y-auto flex flex-col justify-between select-none bg-[#050508] text-[#ffa7e4] overflow-x-hidden font-space">
    <!-- BACKGROUND WEBGL ICEY SHARDS SHADER CANVAS -->
    <div class="fixed inset-0 w-full h-full pointer-events-none z-0">
      <canvas ref="shaderCanvas" class="w-full h-full block opacity-60"></canvas>
      <div class="absolute inset-0 bg-black/65 backdrop-blur-[1px] grid-pattern"></div>
    </div>

    <!-- MAIN AUTH INTERACTION AREA -->
    <main class="relative z-10 flex-1 flex items-center justify-center p-6 md:p-12">
      <div class="w-full max-w-5xl border border-[#ffa7e4] bg-black/90 backdrop-blur-xl shadow-2xl relative">
        <!-- Decorative Corner Targets -->
        <div class="absolute -top-1.5 -left-1.5 w-3 h-3 bg-[#ffa7e4]"></div>
        <div class="absolute -top-1.5 -right-1.5 w-3 h-3 bg-[#ffa7e4]"></div>
        <div class="absolute -bottom-1.5 -left-1.5 w-3 h-3 bg-[#ffa7e4]"></div>
        <div class="absolute -bottom-1.5 -right-1.5 w-3 h-3 bg-[#ffa7e4]"></div>

        <div class="grid grid-cols-1 lg:grid-cols-12">
          <!-- LEFT COLUMN: Editorial Branding -->
          <div class="lg:col-span-5 p-8 lg:p-12 border-b lg:border-b-0 lg:border-r border-[#ffa7e4] flex flex-col justify-between bg-black/60">
            <div>
              <div class="flex items-center gap-2 text-[10px] font-mono tracking-widest uppercase mb-4 text-[#ffa7e4]/70">
                <span>✦ STUDY SYNC</span>
                <span>•</span>
                <span class="text-[#ffa7e4]">SRM RAMAPURAM</span>
              </div>

              <h1 class="font-syne text-4xl sm:text-5xl font-extrabold uppercase tracking-tight leading-none text-[#ffa7e4]">
                STUDY<br>
                SYNC<br>
                <span class="font-instrument italic font-normal text-3xl sm:text-4xl text-white tracking-normal lowercase -mt-1 block">
                  srm ramapuram portal
                </span>
              </h1>

              <div class="w-16 h-0.5 bg-[#ffa7e4] my-6"></div>

              <p class="text-xs font-mono leading-relaxed text-[#ffa7e4]/80 mb-6">
                SRM Institute of Science & Technology, Ramapuram campus peer collaboration and study network. Authenticate with your institutional credentials to connect with peers, study groups, and academic tracks.
              </p>
            </div>

            <div class="pt-8 mt-6 border-t border-[#ffa7e4]/20">
              <div class="text-[10px] font-mono tracking-widest text-[#ffa7e4]/60 uppercase mb-1">CAMPUS ACCESS</div>
              <p class="text-[11px] font-mono text-[#ffa7e4]/70 italic">
                Exclusive portal for SRMIST Ramapuram faculty and enrolled students.
              </p>
            </div>
          </div>

          <!-- RIGHT COLUMN: Authentication Interface -->
          <div class="lg:col-span-7 p-8 lg:p-12 flex flex-col justify-center">
            <!-- Mode Switcher Tabs -->
            <div class="flex border border-[#ffa7e4] mb-8 text-xs font-mono tracking-wider uppercase">
              <button
                type="button"
                @click="isSignup = false"
                :class="[!isSignup ? 'bg-[#ffa7e4] text-black' : 'bg-transparent text-[#ffa7e4] hover:bg-[#ffa7e4]/10']"
                class="flex-1 py-3 text-center font-bold transition-all"
              >
                ■ 01 / SIGN IN
              </button>
              <button
                type="button"
                @click="isSignup = true"
                :class="[isSignup ? 'bg-[#ffa7e4] text-black' : 'bg-transparent text-[#ffa7e4] hover:bg-[#ffa7e4]/10']"
                class="flex-1 py-3 text-center font-bold border-l border-[#ffa7e4] transition-all"
              >
                □ 02 / CREATE ACCOUNT
              </button>
            </div>

            <!-- Error Banner -->
            <div v-if="error" class="mb-5 p-3.5 border border-rose-500 bg-rose-950/40 text-rose-300 text-xs font-mono">
              {{ error }}
            </div>

            <!-- FORM 1: SRM Sign In -->
            <form v-if="!isSignup" @submit.prevent="handleSubmit" class="space-y-6">
              <div>
                <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5 flex justify-between">
                  <span>SRM EMAIL / REGISTRATION NUMBER</span>
                  <span class="text-[#ffa7e4]">@SRMIST.EDU.IN</span>
                </div>
                <div class="relative">
                  <input
                    v-model="email"
                    required
                    type="text"
                    placeholder="ra2111003010000@srmist.edu.in or Reg No."
                    class="input-editorial w-full px-4 py-3 text-sm font-mono tracking-wide rounded-none"
                  />
                  <span class="absolute right-3.5 top-3.5 text-xs text-[#ffa7e4]/50 font-mono">SRM ID</span>
                </div>
              </div>

              <div>
                <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5 flex justify-between items-center">
                  <span>PASSWORD / ACCESS KEY</span>
                  <a href="#" class="text-[10px] hover:underline text-[#ffa7e4]">RESET CREDENTIALS?</a>
                </div>
                <div class="relative">
                  <input
                    v-model="password"
                    required
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="Enter your password"
                    class="input-editorial w-full px-4 py-3 text-sm font-mono tracking-wide rounded-none"
                  />
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="absolute right-3 top-3 text-[11px] font-mono text-[#ffa7e4]/70 hover:text-[#ffa7e4] px-1.5 py-0.5 border border-[#ffa7e4]/40"
                  >
                    {{ showPassword ? 'HIDE' : 'SHOW' }}
                  </button>
                </div>
              </div>

              <!-- Remember Me / Session Persistence -->
              <div class="flex items-center justify-between text-xs font-mono text-[#ffa7e4]/80 pt-1">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked class="accent-[#ffa7e4] rounded-none border-[#ffa7e4]" />
                  <span>REMEMBER ME / PERSIST SESSION</span>
                </label>
                <span class="text-[10px] text-[#ffa7e4]/60 font-mono">CAMPUS SSO READY</span>
              </div>

              <!-- Submit Action Button -->
              <div class="pt-2">
                <button
                  type="submit"
                  :disabled="loading"
                  class="btn-solid-editorial w-full py-4 text-sm font-mono tracking-widest uppercase flex items-center justify-center gap-3 disabled:opacity-50"
                >
                  <span>{{ loading ? 'AUTHENTICATING...' : 'LOG IN' }}</span>
                  <span class="text-base">→</span>
                </button>
              </div>

              <!-- SSO Divider -->
              <div class="relative flex items-center justify-center py-2">
                <div class="border-t border-[#ffa7e4]/30 w-full"></div>
                <span class="bg-black px-3 text-[10px] font-mono tracking-widest text-[#ffa7e4]/60 uppercase">
                  OR INSTITUTIONAL ACCESS
                </span>
                <div class="border-t border-[#ffa7e4]/30 w-full"></div>
              </div>

              <!-- SRM Ramapuram SSO Button (Quick Demo Login) -->
              <button
                type="button"
                @click="fillDemoStudent"
                :disabled="loading"
                class="btn-editorial w-full py-3 text-xs font-mono tracking-widest uppercase flex items-center justify-center gap-2"
              >
                <span class="text-sm">✦</span>
                <span>SRM RAMAPURAM SSO LOGIN (DEMO)</span>
              </button>
            </form>

            <!-- FORM 2: Create Account -->
            <form v-else @submit.prevent="handleSubmit" class="space-y-5">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">FULL NAME</div>
                  <input
                    v-model="name"
                    required
                    type="text"
                    placeholder="e.g. Rahul Sharma"
                    class="input-editorial w-full px-4 py-2.5 text-sm font-mono tracking-wide rounded-none"
                  />
                </div>
                <div>
                  <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">REGISTRATION NUMBER / NETID</div>
                  <input
                    type="text"
                    placeholder="RA2111003010..."
                    class="input-editorial w-full px-4 py-2.5 text-sm font-mono tracking-wide rounded-none"
                  />
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">DEPARTMENT / PROGRAM</div>
                  <select v-model="major" class="input-editorial w-full px-4 py-2.5 text-xs font-mono rounded-none">
                    <option value="B.Tech Computer Science & Engg">B.Tech Computer Science &amp; Engg</option>
                    <option value="B.Tech Information Technology">B.Tech Information Technology</option>
                    <option value="B.Tech Electronics & Comm (ECE)">B.Tech Electronics &amp; Comm (ECE)</option>
                    <option value="B.Tech AI & Data Science">B.Tech AI &amp; Data Science</option>
                    <option value="M.Tech Computer Science">M.Tech Computer Science</option>
                  </select>
                </div>
                <div>
                  <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">CAMPUS BATCH</div>
                  <select class="input-editorial w-full px-4 py-2.5 text-xs font-mono rounded-none">
                    <option>SRM Ramapuram · Batch of 2025</option>
                    <option selected>SRM Ramapuram · Batch of 2026</option>
                    <option>SRM Ramapuram · Batch of 2027</option>
                    <option>SRM Ramapuram · Batch of 2028</option>
                  </select>
                </div>
              </div>

              <div>
                <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">OFFICIAL SRM EMAIL</div>
                <input
                  v-model="email"
                  required
                  type="email"
                  placeholder="student@srmist.edu.in"
                  class="input-editorial w-full px-4 py-2.5 text-sm font-mono tracking-wide rounded-none"
                />
              </div>

              <div>
                <div class="text-[11px] font-mono uppercase tracking-widest text-[#ffa7e4]/70 mb-1.5">CREATE PASSWORD</div>
                <input
                  v-model="password"
                  required
                  type="password"
                  placeholder="Minimum 8 characters"
                  class="input-editorial w-full px-4 py-2.5 text-sm font-mono tracking-wide rounded-none"
                />
              </div>

              <div class="text-[11px] font-mono text-[#ffa7e4]/70 leading-relaxed pt-1">
                <label class="flex items-start gap-2 cursor-pointer">
                  <input type="checkbox" checked class="accent-[#ffa7e4] mt-0.5" />
                  <span>I confirm that I am an actively enrolled student at SRMIST Ramapuram campus.</span>
                </label>
              </div>

              <!-- Register Action Button -->
              <div class="pt-2">
                <button
                  type="submit"
                  :disabled="loading"
                  class="btn-solid-editorial w-full py-4 text-sm font-mono tracking-widest uppercase flex items-center justify-center gap-3 disabled:opacity-50"
                >
                  <span>{{ loading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT & ENTER' }}</span>
                  <span class="text-base">→</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { loginUser, signupUser } from '../api.js';

const emit = defineEmits(['auth-success']);

const isSignup = ref(false);
const name = ref('');
const email = ref('ra2111003010000@srmist.edu.in');
const password = ref('password123');
const major = ref('B.Tech Computer Science & Engg');
const showPassword = ref(false);
const loading = ref(false);
const error = ref('');

const shaderCanvas = ref(null);
let animationFrameId = null;

async function fillDemoStudent() {
  isSignup.value = false;
  email.value = 'alex@univ.edu';
  password.value = 'password123';
  await handleSubmit();
}

async function handleSubmit() {
  loading.value = true;
  error.value = '';
  try {
    let res;
    if (isSignup.value) {
      res = await signupUser(name.value || 'Student', email.value, password.value, major.value);
    } else {
      res = await loginUser(email.value, password.value);
    }
    localStorage.setItem('token', res.access_token);
    emit('auth-success');
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

// ------------------- WEBGL ICEY NIGHT BLUE SHADER -------------------
function initShader() {
  const canvas = shaderCanvas.value;
  if (!canvas) return;

  function syncSize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }
  syncSize();
  window.addEventListener('resize', syncSize);

  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  if (!gl) return;

  const vs = `attribute vec2 a_position;
varying vec2 v_texCoord;
void main() {
  v_texCoord = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}`;

  const fs = `precision highp float;
uniform vec2 u_resolution;
uniform float u_time;

float grainHash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec3 palette(float x) {
  vec3 c0 = vec3(0.012, 0.027, 0.071);
  vec3 c1 = vec3(0.059, 0.169, 0.361);
  vec3 c2 = vec3(0.133, 0.827, 0.933);
  vec3 c3 = vec3(0.878, 0.949, 0.996);
  float f = clamp(x, 0.0, 1.0) * 3.0;
  if (f < 1.0) return mix(c0, c1, smoothstep(0.0, 1.0, f));
  if (f < 2.0) return mix(c1, c2, smoothstep(0.0, 1.0, f - 1.0));
  return mix(c2, c3, smoothstep(0.0, 1.0, f - 2.0));
}

vec3 shade(vec2 uv, vec2 p, float t) {
  float k = 2.0 + 0.48 * 6.0;
  float v = sin(p.x * k + t) + sin(p.y * k * 0.8 - t * 0.7)
    + sin((p.x + p.y) * k * 0.6 + t * 0.5)
    + sin(length(p) * k * 1.2 - t);
  return palette(0.5 + 0.5 * sin(v + 7.0));
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution.xy;
  vec2 screenUv = uv;
  vec2 p = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  
  p *= 1.5;
  float t = u_time * 0.86;
  p += 0.156 * vec2(sin(t * 0.31), cos(t * 0.23));
  
  vec3 col = shade(uv, p, t);
  col = (col - 0.5) * 0.924 + 0.5;
  col -= 0.35;
  
  float vd = length(screenUv - 0.5) * 1.4142;
  col *= 1.0 - 0.61 * smoothstep(0.35, 1.0, vd);
  col += (grainHash(gl_FragCoord.xy + vec2(7.0 * 17.0, 7.0 * 31.0)) - 0.5) * 0.25;
  
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

  function cs(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, cs(gl.VERTEX_SHADER, vs));
  gl.attachShader(prog, cs(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(prog, 'a_position');
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

  const uTime = gl.getUniformLocation(prog, 'u_time');
  const uRes = gl.getUniformLocation(prog, 'u_resolution');

  function render(t) {
    syncSize();
    gl.viewport(0, 0, canvas.width, canvas.height);
    if (uTime) gl.uniform1f(uTime, t * 0.001);
    if (uRes) gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    animationFrameId = requestAnimationFrame(render);
  }
  render(0);
}

onMounted(() => {
  initShader();
});

onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
});
</script>

<style scoped>
.font-syne { font-family: 'Syne', sans-serif; }
.font-instrument { font-family: 'Instrument Serif', Georgia, serif; }

.grid-pattern {
  background-size: 32px 32px;
  background-image: 
    linear-gradient(to right, rgba(255, 167, 228, 0.04) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 167, 228, 0.04) 1px, transparent 1px);
}

.input-editorial {
  background: rgba(8, 8, 14, 0.75);
  border: 1px solid rgba(255, 167, 228, 0.35);
  color: #ffa7e4;
  outline: none;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.input-editorial:focus {
  border-color: #ffa7e4;
  background: rgba(15, 15, 26, 0.95);
  box-shadow: 0 0 0 1px #ffa7e4;
}
.input-editorial::placeholder {
  color: rgba(255, 167, 228, 0.3);
}

.btn-solid-editorial {
  background-color: #ffa7e4;
  color: #000000;
  border: 1px solid #ffa7e4;
  font-weight: 700;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}
.btn-solid-editorial:hover {
  background-color: #000000;
  color: #ffa7e4;
}

.btn-editorial {
  background-color: transparent;
  color: #ffa7e4;
  border: 1px solid #ffa7e4;
  transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1);
}
.btn-editorial:hover {
  background-color: #ffa7e4;
  color: #000000;
}
</style>

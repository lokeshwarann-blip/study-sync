<template>
  <div class="fixed inset-0 w-full h-full pointer-events-none -z-10" style="display:block;">
    <canvas ref="canvas" style="display:block;width:100%;height:100%"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const canvas = ref(null);
let raf = null;
let ro = null;

const VS = `attribute vec2 a_position;
void main() { gl_Position = vec4(a_position, 0.0, 1.0); }`;

const FS = `precision highp float;
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

vec3 shade(vec2 p, float t) {
  float k = 2.0 + 0.48 * 6.0;
  float v = sin(p.x * k + t) + sin(p.y * k * 0.8 - t * 0.7)
    + sin((p.x + p.y) * k * 0.6 + t * 0.5)
    + sin(length(p) * k * 1.2 - t);
  return palette(0.5 + 0.5 * sin(v + 7.0));
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution.xy;
  vec2 p = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / min(u_resolution.x, u_resolution.y);
  p *= 1.5;
  float t = u_time * 0.86;
  p += 0.156 * vec2(sin(t * 0.31), cos(t * 0.23));
  vec3 col = shade(p, t);
  col = (col - 0.5) * 0.924 + 0.5;
  col -= 0.35;
  float vd = length(uv - 0.5) * 1.4142;
  col *= 1.0 - 0.61 * smoothstep(0.35, 1.0, vd);
  col += (grainHash(gl_FragCoord.xy + vec2(7.0 * 17.0, 7.0 * 31.0)) - 0.5) * 0.25;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

onMounted(() => {
  const c = canvas.value;
  if (!c) return;

  const sync = () => {
    const w = c.clientWidth || 1280, h = c.clientHeight || 720;
    if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  };
  ro = new ResizeObserver(sync);
  ro.observe(c);
  sync();

  const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
  if (!gl) return;

  const mk = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
  const prog = gl.createProgram();
  gl.attachShader(prog, mk(gl.VERTEX_SHADER, VS));
  gl.attachShader(prog, mk(gl.FRAGMENT_SHADER, FS));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(prog, 'a_position');
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

  const uTime = gl.getUniformLocation(prog, 'u_time');
  const uRes = gl.getUniformLocation(prog, 'u_resolution');

  const render = (t) => {
    gl.viewport(0, 0, c.width, c.height);
    gl.uniform1f(uTime, t * 0.001);
    gl.uniform2f(uRes, c.width, c.height);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    raf = requestAnimationFrame(render);
  };
  render(0);
});

onUnmounted(() => {
  if (raf) cancelAnimationFrame(raf);
  if (ro) ro.disconnect();
});
</script>

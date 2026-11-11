// MCP «pc-control»: control del PC (Windows) para agentes de IA (Claude Code, OpenCode u otro cliente MCP).
// Ratón y teclado con uno de dos backends:
//   - "powershell": entrada.ps1 (Win32 SendInput), sin dependencias. Es el que se usa si no hay otro.
//   - "nativo": el módulo nativo de la app de escritorio de Claude, si está instalada (más rápido).
// Elige con la variable PC_CONTROL_BACKEND=auto|nativo|powershell (por defecto auto) y, si el
// módulo nativo está en otra ruta, PC_CONTROL_NATIVO=<ruta al .node>.
// Captura de pantalla con .NET (captura.ps1). Las coordenadas van SIEMPRE en el espacio de la última captura.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { createRequire } from "node:module";
import { execFile, spawn } from "node:child_process";
import { readFileSync, writeFileSync, readdirSync, existsSync, unlinkSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";
import { crearBackendPS } from "./entrada-ps.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const uiaScript = join(here, "uia.ps1");

// Módulo nativo de la app de escritorio de Claude (opcional; no se redistribuye con este repo).
function cargarNativo() {
  if (process.env.PC_CONTROL_NATIVO) return require(process.env.PC_CONTROL_NATIVO);
  const rel = "app/resources/app.asar.unpacked/node_modules/@ant/claude-native/claude-native-binding.node";
  const base = "C:/Program Files/WindowsApps";
  const dirs = readdirSync(base).filter((d) => /^Claude_[\d.]+_x64__/.test(d))
    .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
  for (const d of dirs) { const p = join(base, d, rel); if (existsSync(p)) return require(p); }
  throw new Error("no está la app de escritorio de Claude");
}
function elegirBackend() {
  const modo = (process.env.PC_CONTROL_BACKEND || "auto").toLowerCase();
  if (modo !== "powershell") {
    try { const n = cargarNativo(); n.nombre = "nativo"; return n; }
    catch (e) { if (modo === "nativo") throw new Error(`Backend nativo no disponible: ${e.message}`); }
  }
  return crearBackendPS(here);
}
const N = elegirBackend();

// --- Aviso visual (marco + aro en el ratón) mientras se controla el PC ---
const BEAT = join(tmpdir(), `pcctl_beat_${process.pid}`);
let overlay = null;
function aviso() {
  writeFileSync(BEAT, String(Date.now()));
  if (overlay && overlay.exitCode === null) return;
  overlay = spawn("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", join(here, "overlay.ps1"),
    "-Beat", BEAT, "-ParentPid", String(process.pid)], { windowsHide: true, stdio: "ignore" });
}
const cerrarAviso = () => { try { overlay?.kill(); } catch {} };
process.on("exit", cerrarAviso);
for (const s of ["SIGINT", "SIGTERM"]) process.on(s, () => { cerrarAviso(); process.exit(0); });
process.stdin.on("close", () => { cerrarAviso(); process.exit(0); });

let escala = null; // { k, ox, oy } de captura -> pantalla real
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

function captura(maxW = 1366) {
  const out = join(tmpdir(), `pcctl_${process.pid}_${Date.now()}.jpg`);
  return new Promise((res, rej) => {
    execFile("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", join(here, "captura.ps1"), "-Out", out, "-MaxW", String(maxW)],
      { windowsHide: true, timeout: 20000 }, (err, stdout) => {
        if (err) return rej(err);
        const [W, H, w, h, ox, oy] = stdout.trim().split(/\s+/).map(Number);
        escala = { k: W / w, ox, oy };
        const data = readFileSync(out).toString("base64");
        try { unlinkSync(out); } catch {}
        res({ data, W, H, w, h });
      });
  });
}
function arbolAccesibilidad(processId, maxDepth = 4, maxNodes = 160) {
  return new Promise((res, rej) => {
    execFile("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", uiaScript,
      "-ProcessId", String(processId), "-MaxDepth", String(maxDepth), "-MaxNodes", String(maxNodes)],
    { windowsHide: true, timeout: 30000, maxBuffer: 2 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err) return rej(new Error(`UI Automation falló: ${stderr || err.message}`));
      try { res(JSON.parse(stdout)); }
      catch { rej(new Error(`Respuesta UI Automation no válida: ${stderr || stdout.slice(0, 300)}`)); }
    });
  });
}
async function real(x, y) {
  if (!escala) await captura();
  return [Math.round(x * escala.k + escala.ox), Math.round(y * escala.k + escala.oy)];
}
async function moverSuave(x, y) {
  aviso();
  const p = await N.mouseLocation();
  const pasos = 8;
  for (let i = 1; i <= pasos; i++) {
    const t = 1 - (1 - i / pasos) ** 3;
    await N.moveMouse(Math.round(p.x + (x - p.x) * t), Math.round(p.y + (y - p.y) * t), false);
    await espera(8);
  }
}
const teclas = (s) => s.split("+").map((k) => k.trim().toLowerCase()).filter(Boolean);
const ok = (t) => ({ content: [{ type: "text", text: t }] });
async function trasAccion(t, ver) {
  if (!ver) return ok(t);
  await espera(400);
  const c = await captura();
  return { content: [{ type: "text", text: t }, { type: "image", data: c.data, mimeType: "image/jpeg" }] };
}

const server = new McpServer({ name: "pc-control", version: "1.1.0" });
const xy = { x: z.number().describe("X en la última captura"), y: z.number().describe("Y en la última captura") };
const ver = z.boolean().optional().describe("Devolver captura tras la acción (por defecto true)");

server.tool("screenshot", "Captura la pantalla completa. Las coordenadas de las demás herramientas van en el espacio de ESTA imagen.",
  { max_width: z.number().optional().describe("Ancho máximo (por defecto 1366)") },
  async ({ max_width }) => {
    const c = await captura(max_width ?? 1366);
    return { content: [{ type: "text", text: `Captura ${c.w}x${c.h} (pantalla real ${c.W}x${c.H})` }, { type: "image", data: c.data, mimeType: "image/jpeg" }] };
  });

server.tool("click", "Clic en (x,y). button: left|right|middle. count: 1 o 2 (doble clic). modifiers: p. ej. 'ctrl' o 'ctrl+shift'.",
  { ...xy, button: z.enum(["left", "right", "middle"]).optional(), count: z.number().int().min(1).max(3).optional(), modifiers: z.string().optional(), screenshot: ver },
  async ({ x, y, button = "left", count = 1, modifiers, screenshot = true }) => {
    const [rx, ry] = await real(x, y);
    await moverSuave(rx, ry);
    const mods = modifiers ? teclas(modifiers) : [];
    if (mods.length) N.validateKeys(mods);
    for (const m of mods) await N.key(m, "press");
    try { await N.mouseButton(button, "click", count); }
    finally { for (const m of mods.reverse()) await N.key(m, "release").catch(() => {}); }
    return trasAccion(`Clic ${button} x${count} en (${x},${y})`, screenshot);
  });

server.tool("move", "Mueve el ratón a (x,y) sin hacer clic.", { ...xy },
  async ({ x, y }) => { const [rx, ry] = await real(x, y); await moverSuave(rx, ry); return ok("Movido."); });

server.tool("drag", "Arrastra con el botón izquierdo de (x1,y1) a (x2,y2).",
  { x1: z.number(), y1: z.number(), x2: z.number(), y2: z.number(), screenshot: ver },
  async ({ x1, y1, x2, y2, screenshot = true }) => {
    const [a, b] = await real(x1, y1); const [c, d] = await real(x2, y2);
    await moverSuave(a, b); await N.mouseButton("left", "press"); await espera(60);
    try { await moverSuave(c, d); await espera(60); } finally { await N.mouseButton("left", "release"); }
    return trasAccion("Arrastrado.", screenshot);
  });

server.tool("scroll", "Rueda del ratón en (x,y). amount positivo = abajo/derecha, negativo = arriba/izquierda (en 'clics' de rueda).",
  { ...xy, amount: z.number().int(), horizontal: z.boolean().optional(), screenshot: ver },
  async ({ x, y, amount, horizontal = false, screenshot = true }) => {
    const [rx, ry] = await real(x, y); await moverSuave(rx, ry);
    await N.mouseScroll(amount, horizontal ? "horizontal" : "vertical");
    return trasAccion(`Scroll ${amount}`, screenshot);
  });

server.tool("type", "Escribe texto en la ventana con el foco.", { text: z.string(), screenshot: ver },
  async ({ text, screenshot = false }) => { aviso(); await N.typeText(text); return trasAccion("Escrito.", screenshot); });

server.tool("key", "Pulsa una tecla o combinación: 'enter', 'ctrl+c', 'alt+tab', 'win+r', 'ctrl+shift+esc'. Nombres: ctrl alt shift win enter tab escape backspace delete up down left right pageup pagedown home end space f1..f12, letras y números.",
  { keys: z.string(), repeat: z.number().int().min(1).max(50).optional(), screenshot: ver },
  async ({ keys, repeat = 1, screenshot = true }) => {
    const ks = teclas(keys); N.validateKeys(ks); aviso();
    for (let i = 0; i < repeat; i++) { await N.keys(ks); if (repeat > 1) await espera(40); }
    return trasAccion(`Tecla ${keys}${repeat > 1 ? " x" + repeat : ""}`, screenshot);
  });

server.tool("cursor_position", "Posición actual del ratón (en coordenadas de la última captura).", {},
  async () => {
    const p = await N.mouseLocation(); if (!escala) await captura();
    return ok(`(${Math.round((p.x - escala.ox) / escala.k)}, ${Math.round((p.y - escala.oy) / escala.k)})`);
  });

server.tool("list_apps", "Lista las aplicaciones abiertas y cuál está en primer plano.", {},
  async () => {
    const apps = await N.cuListRunningApps();
    const front = await N.getFrontmostAppInfo();
    const vistos = new Set(); const lin = [];
    for (const a of apps) { if (vistos.has(a.bundleId)) continue; vistos.add(a.bundleId); lin.push(`${a.displayName} — ${a.bundleId} (pid ${a.pid})`); }
    return ok(`Primer plano: ${front?.appName ?? "?"}\n` + lin.join("\n"));
  });

server.tool("accessibility_tree", "Lee el árbol de accesibilidad de las ventanas de una app, sin interactuar con ellas. Usa el PID devuelto por list_apps. No lee el valor escrito dentro de los campos.",
  { process_id: z.number().int().positive(), max_depth: z.number().int().min(1).max(8).optional(), max_nodes: z.number().int().min(20).max(400).optional() },
  async ({ process_id, max_depth = 4, max_nodes = 160 }) => {
    const result = await arbolAccesibilidad(process_id, max_depth, max_nodes);
    // Pasa los rect de píxeles reales al espacio de la captura, que es el que usan click/move/drag
    if (!escala) await captura();
    for (const w of result.windows ?? []) for (const n of w.nodes ?? []) if (n.rect) {
      n.rect = { x: Math.round((n.rect.x - escala.ox) / escala.k), y: Math.round((n.rect.y - escala.oy) / escala.k),
        width: Math.round(n.rect.width / escala.k), height: Math.round(n.rect.height / escala.k) };
    }
    result.coordenadas = "espacio de la captura (válidas para click/move)";
    return ok(JSON.stringify(result));
  });

server.tool("wait", "Espera N segundos (máx. 30) y opcionalmente devuelve captura.", { seconds: z.number().min(0).max(30), screenshot: ver },
  async ({ seconds, screenshot = true }) => { await espera(seconds * 1000); return trasAccion(`Esperados ${seconds}s`, screenshot); });

await server.connect(new StdioServerTransport());

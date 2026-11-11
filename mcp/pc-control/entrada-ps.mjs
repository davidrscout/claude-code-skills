// Backend de ratón y teclado de pc-control basado en PowerShell + Win32 SendInput (sin binarios).
// Expone la misma interfaz que usa server.mjs con el módulo nativo opcional.
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { join } from "node:path";

export function crearBackendPS(dir) {
  const ps = spawn("powershell.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", join(dir, "entrada.ps1")],
    { windowsHide: true, stdio: ["pipe", "pipe", "pipe"] });
  const pendientes = new Map();
  let siguiente = 1;
  let errores = "";
  ps.stderr.on("data", (d) => { errores = (errores + d.toString()).slice(-2000); });
  createInterface({ input: ps.stdout }).on("line", (linea) => {
    let r;
    try { r = JSON.parse(linea.replace(/^﻿/, "")); } catch { return; }
    const p = pendientes.get(r.id);
    if (!p) return;
    pendientes.delete(r.id);
    if (r.ok) p.res(r); else p.rej(new Error(r.error || "fallo en entrada.ps1"));
  });
  ps.on("exit", (code) => {
    for (const p of pendientes.values()) p.rej(new Error(`entrada.ps1 terminó (código ${code}): ${errores}`));
    pendientes.clear();
  });
  const orden = (op, args = {}) => new Promise((res, rej) => {
    if (ps.exitCode !== null) return rej(new Error(`entrada.ps1 no está en marcha: ${errores}`));
    const id = siguiente++;
    pendientes.set(id, { res, rej });
    ps.stdin.write(JSON.stringify({ id, op, ...args }) + "\n");
  });
  const cerrar = () => { try { ps.kill(); } catch {} };
  process.on("exit", cerrar);

  let ultimaValidacion = null;
  return {
    nombre: "powershell",
    mouseLocation: () => orden("loc").then((r) => ({ x: r.x, y: r.y })),
    moveMouse: (x, y) => orden("move", { x, y }),
    mouseButton: (button, action, count = 1) => orden("button", { button, action, count }),
    mouseScroll: (amount, dir) => orden("scroll", { amount, horizontal: dir === "horizontal" }),
    typeText: (text) => orden("type", { text }),
    key: (k, action) => orden("key", { key: k, action }),
    keys: (ks) => orden("keys", { keys: ks }),
    // La versión nativa valida de forma síncrona; aquí se valida al ejecutar y el error sube igual.
    validateKeys: (ks) => { ultimaValidacion = orden("valid", { keys: ks }); ultimaValidacion.catch(() => {}); },
    cuListRunningApps: () => orden("apps").then((r) =>
      (r.apps || []).map((a) => ({ pid: a.pid, bundleId: a.name, displayName: a.title ? `${a.name} (${a.title})` : a.name }))),
    getFrontmostAppInfo: () => orden("apps").then((r) => ({ appName: r.front })),
  };
}

"""Saca el texto de las transcripciones de Claude Code a un corpus buscable (un .txt por sesión).

Uso:
  python -I extraer_corpus.py <carpeta-salida> [--desde AAAA-MM-DD] [--proyecto <carpeta>] [--raiz <ruta>]

- Solo guarda los mensajes de usuario y asistente (sin resultados de herramientas ni avisos
  del sistema), recortados a 2500 caracteres cada uno.
- --desde: solo sesiones modificadas desde esa fecha (por defecto, los últimos 30 días).
- --proyecto: solo esa carpeta de ~/.claude/projects/ (p. ej. -home-ana-dev-tienda).
- --raiz: otra carpeta de proyectos (por defecto ~/.claude/projects).
Las horas que aparecen están en UTC, como en las transcripciones.
"""
import argparse
import glob
import json
import os
import time


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("salida")
    ap.add_argument("--desde", help="AAAA-MM-DD")
    ap.add_argument("--proyecto", default="*")
    ap.add_argument("--raiz", default=os.path.expanduser("~/.claude/projects"))
    a = ap.parse_args()
    if a.desde:
        desde = time.mktime(time.strptime(a.desde, "%Y-%m-%d"))
    else:
        desde = time.time() - 30 * 86400
    os.makedirs(a.salida, exist_ok=True)
    n = 0
    for f in glob.glob(os.path.join(a.raiz, a.proyecto, "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(f) < desde:
            continue
        sid = os.path.basename(os.path.dirname(f))[:30] + "__" + os.path.basename(f)[:8]
        lineas = []
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for l in fh:
                    try:
                        d = json.loads(l)
                    except ValueError:
                        continue
                    t = d.get("type")
                    if t not in ("user", "assistant"):
                        continue
                    c = (d.get("message") or {}).get("content")
                    if isinstance(c, str):
                        txt = c
                    elif isinstance(c, list):
                        txt = " ".join(x.get("text", "") for x in c
                                       if isinstance(x, dict) and x.get("type") == "text")
                    else:
                        txt = ""
                    txt = " ".join(txt.split())
                    if not txt or txt.startswith("<system-reminder>"):
                        continue
                    lineas.append(f"{d.get('timestamp', '')[:16]} {t[0].upper()}: {txt[:2500]}")
        except OSError:
            continue
        if len(lineas) < 2:
            continue
        nombre = sid.replace(":", "") + ".txt"
        with open(os.path.join(a.salida, nombre), "w", encoding="utf-8") as out:
            out.write("\n".join(lineas))
        n += 1
    print(f"{n} sesiones volcadas en {a.salida}")


if __name__ == "__main__":
    main()

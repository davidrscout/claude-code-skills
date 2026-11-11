"""Vuelca una conversación de un agente de código a markdown legible, SIN resumir.

Formatos que entiende (los detecta solo):
  - Claude Code: la transcripción .jsonl de la sesión
    (~/.claude/projects/<carpeta-del-proyecto>/<id-de-sesión>.jsonl).
  - OpenCode: el JSON de `opencode session export <id> > sesion.json`
    (OpenCode guarda las sesiones en una base SQLite; el export es la forma legible).

Uso:  python -I conversacion.py <sesion.jsonl|sesion.json> [salida.md] [--tool-chars N]

Conserva en orden: mensajes del usuario, texto del asistente, cada llamada a herramienta
(nombre + parámetros) y cada resultado (recortado a N caracteres, 4000 por defecto, para
que el fichero sea manejable; la cabecera dice dónde está el texto completo).
Lo inyectado por el entorno (skills, comandos, avisos) se etiqueta SISTEMA, no USUARIO.
NO vuelca el razonamiento interno del modelo (bloques thinking/reasoning): algunos modelos
rechazan leer el razonamiento de otro. Si no se da salida, imprime por stdout.
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _texto(b):
    if isinstance(b, str):
        return b
    if isinstance(b, list):
        out = []
        for x in b:
            if isinstance(x, dict) and x.get("type") == "text":
                out.append(x.get("text", ""))
            elif isinstance(x, dict) and x.get("type") == "image":
                out.append("[imagen]")
        return "\n".join(out)
    return "" if b is None else str(b)


def _recorta(s, n):
    return s if len(s) <= n else s[:n] + f"\n…[recortado, {len(s)} caracteres en total]"


def _es_sistema(s):
    """Texto que llega como mensaje de usuario pero no lo escribió el usuario."""
    return (s.startswith("<") or s.startswith("Base directory for this skill")
            or s.startswith("[Image:") or s.startswith("Tool loaded"))


def _cabecera(out, src, n, completo):
    print("# Conversación volcada literalmente (sin resumir)", file=out)
    print(f"Origen: {os.path.abspath(src)}", file=out)
    print(f"Resultados de herramienta recortados a {n} caracteres; el texto completo está en {completo}", file=out)
    print("Etiquetas: USUARIO = mensaje escrito por la persona; SISTEMA = texto inyectado por el "
          "entorno (skills, comandos, recordatorios); ASISTENTE = respuesta del modelo.", file=out)


def claude_code(src, out, n):
    tool_results = os.path.join(os.path.dirname(os.path.abspath(src)),
                                os.path.splitext(os.path.basename(src))[0], "tool-results")
    _cabecera(out, src, n, f"el .jsonl de origen y, para ficheros grandes, {tool_results}")
    vistos = set()
    with open(src, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = d.get("type")
            if t not in ("user", "assistant"):
                continue
            uid = d.get("uuid")
            if uid in vistos:
                continue
            vistos.add(uid)
            content = (d.get("message") or {}).get("content")
            ts = (d.get("timestamp") or "")[:16].replace("T", " ")
            if t == "user":
                if isinstance(content, str):
                    s = content.strip()
                    print(f"\n### {'SISTEMA' if _es_sistema(s) else 'USUARIO'} [{ts} UTC]\n{s}", file=out)
                elif isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_result":
                            body = _recorta(_texto(b.get("content")), n)
                            print(f"\n#### resultado de herramienta\n{body.strip()}", file=out)
                        elif b.get("type") == "text":
                            txt = b.get("text", "").strip()
                            if txt.startswith("<system-reminder>"):
                                continue
                            print(f"\n### {'SISTEMA' if _es_sistema(txt) else 'USUARIO'} [{ts} UTC]\n{txt}", file=out)
            elif isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    k = b.get("type")
                    if k == "text":
                        print(f"\n### ASISTENTE [{ts} UTC]\n{b.get('text', '').strip()}", file=out)
                    elif k == "tool_use":
                        inp = json.dumps(b.get("input"), ensure_ascii=False)
                        print(f"\n#### herramienta: {b.get('name')}\n{_recorta(inp, n)}", file=out)
                    # thinking: no se vuelca (ver docstring)


def _hora_ms(ms):
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return ""


def opencode(src, out, n, d):
    _cabecera(out, src, n, "la base de datos de OpenCode (vuelve a exportar la sesión sin --tool-chars)")
    info = d.get("info") or {}
    if info:
        mod = info.get("model") or {}
        print(f"Sesión OpenCode: {info.get('id', '')} · «{info.get('title', '')}» · "
              f"{mod.get('providerID', '')}/{mod.get('id', '')} · carpeta {(info.get('location') or {}).get('directory', '')}",
              file=out)
    for m in d.get("messages") or []:
        tipo = m.get("type")
        ts = _hora_ms((m.get("time") or {}).get("created"))
        if tipo == "user":
            s = (m.get("text") or "").strip()
            if len(s) >= 2 and s[0] == s[-1] == '"':
                s = s[1:-1]
            ficheros = [f.get("filename") or f.get("url") or "" for f in (m.get("files") or []) if isinstance(f, dict)]
            if ficheros:
                s += "\n[adjuntos: " + ", ".join(ficheros) + "]"
            print(f"\n### {'SISTEMA' if _es_sistema(s) else 'USUARIO'} [{ts} UTC]\n{s}", file=out)
        elif tipo == "assistant":
            for c in m.get("content") or []:
                if not isinstance(c, dict):
                    continue
                k = c.get("type")
                if k == "text":
                    print(f"\n### ASISTENTE [{ts} UTC]\n{(c.get('text') or '').strip()}", file=out)
                elif k == "tool":
                    st = c.get("state") or {}
                    inp = json.dumps(st.get("input"), ensure_ascii=False)
                    print(f"\n#### herramienta: {c.get('name')}\n{_recorta(inp, n)}", file=out)
                    res = _texto(st.get("content")) or str(st.get("output") or st.get("error") or "")
                    estado = st.get("status", "")
                    print(f"\n#### resultado de herramienta ({estado})\n{_recorta(res, n).strip()}", file=out)
                # reasoning: no se vuelca (ver docstring)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = 4000
    if "--tool-chars" in sys.argv:
        n = int(sys.argv[sys.argv.index("--tool-chars") + 1])
        args = [a for a in args if a != str(n)]
    if not args:
        sys.exit(__doc__)
    src = args[0]
    out = open(args[1], "w", encoding="utf-8") if len(args) > 1 else sys.stdout
    try:
        with open(src, encoding="utf-8") as fh:
            primero = fh.read(1)
            fh.seek(0)
            d = None
            if primero == "{":
                try:
                    d = json.load(fh)
                except ValueError:
                    d = None  # es un .jsonl: varias líneas JSON
        if isinstance(d, dict) and "messages" in d:
            opencode(src, out, n, d)
        else:
            claude_code(src, out, n)
    finally:
        if out is not sys.stdout:
            out.close()


if __name__ == "__main__":
    main()

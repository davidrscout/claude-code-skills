"""Instala las skills, los agentes y los scripts de este repo en Claude Code y/o OpenCode.

Uso (desde la raíz del repo):
  python instalar.py                       # todo, en Claude Code y en OpenCode
  python instalar.py --opencode            # solo OpenCode
  python instalar.py --claude --skills     # solo las skills, solo Claude Code
  python instalar.py --solo techo,depurar  # solo esas skills (y lo que pidas además)
  python instalar.py --proyecto ~/dev/app  # en <proyecto>/.claude y <proyecto>/.opencode en vez de global
  python instalar.py --simular             # enseña qué haría, sin tocar nada

Opciones de modelo para los agentes:
  --oc-modelo-advisor proveedor/modelo   modelo del agente `estratega` en OpenCode
                                         (sin esta opción hereda el de la sesión)
  --oc-modelo-rapido proveedor/modelo    modelo del agente `rapido` en OpenCode
  --cc-modelo-advisor <modelo>           modelo del `estratega` en Claude Code (por defecto `opus`;
                                         p. ej. el id completo del mejor modelo de tu plan)

Destinos (globales):
  Claude Code: ~/.claude/skills/<skill>/, ~/.claude/agents/<agente>.md, ~/.claude/scripts/
               (o $CLAUDE_CONFIG_DIR si está definida)
  OpenCode:    ~/.config/opencode/skills/<skill>/, ~/.config/opencode/agents/<agente>.md,
               ~/.config/opencode/scripts/   (o $XDG_CONFIG_HOME/opencode)

Si un destino ya existe NO se toca, salvo con --forzar; en ese caso antes se copia lo que
había a ~/.cache/claude-code-skills-respaldo/<fecha>/. Los agentes se copian tal cual a
Claude Code y se convierten al formato V2 de OpenCode (description + mode: subagent +
permissions); los que en Claude Code no tienen Edit/Write quedan con la edición denegada.
"""
import argparse
import json
import os
import shutil
import sys
import textwrap
from datetime import datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def leer_frontmatter(texto):
    """Devuelve (campos, cuerpo). Entiende `clave: valor`, bloques `>`/`>-`/`|`/`|-` y listas `[a, b]`."""
    t = texto.replace("\r\n", "\n")
    if not t.startswith("---\n"):
        return {}, t
    fin = t.find("\n---", 4)
    if fin < 0:
        return {}, t
    cab, cuerpo = t[4:fin], t[fin + 4:].lstrip("\n")
    campos, clave, bloque, estilo = {}, None, [], None
    def cerrar():
        if clave is not None and estilo:
            lineas = [l.strip() for l in bloque]
            campos[clave] = (textwrap.dedent("\n".join(bloque)).strip() if estilo.startswith("|")
                             else " ".join(l for l in lineas if l))
    for linea in cab.split("\n"):
        if estilo and (linea.startswith(" ") or linea.startswith("\t") or not linea.strip()):
            bloque.append(linea)
            continue
        cerrar()
        clave, bloque, estilo = None, [], None
        if ":" not in linea or linea.startswith(" "):
            continue
        k, v = linea.split(":", 1)
        k, v = k.strip(), v.strip()
        if v in (">", ">-", "|", "|-", ">+", "|+"):
            clave, estilo = k, v
        elif v.startswith("[") and v.endswith("]"):
            campos[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                v = v[1:-1]
            campos[k] = v
    cerrar()
    return campos, cuerpo


def skills_del_repo():
    return sorted(d for d in os.listdir(RAIZ)
                  if os.path.isfile(os.path.join(RAIZ, d, "SKILL.md")) and not d.startswith("."))


def agentes_del_repo():
    carpeta = os.path.join(RAIZ, "agentes")
    return sorted(f for f in os.listdir(carpeta) if f.endswith(".md") and f != "README.md")


def herramientas_claude(campos):
    h = campos.get("tools")
    if h is None:
        return None
    if isinstance(h, str):
        h = [x.strip() for x in h.split(",") if x.strip()]
    return h


def a_opencode(texto, modelo=None):
    """Convierte un agente de Claude Code (frontmatter name/description/tools/model) al formato V2 de OpenCode."""
    campos, cuerpo = leer_frontmatter(texto)
    lineas = ["---", "description: " + json.dumps(campos.get("description", ""), ensure_ascii=False),
              "mode: subagent"]
    if modelo:
        lineas.append(f"model: {modelo}")
    h = herramientas_claude(campos)
    if h is not None and not ({"Edit", "Write", "MultiEdit", "NotebookEdit"} & set(h)):
        lineas += ["permissions:", "  - action: edit", '    resource: "*"', "    effect: deny"]
    lineas.append("---")
    return "\n".join(lineas) + "\n\n" + cuerpo


def con_modelo_claude(texto, modelo):
    t = texto.replace("\r\n", "\n")
    fin = t.find("\n---", 4)
    cab, resto = t[:fin], t[fin:]
    nuevas = [l for l in cab.split("\n") if not l.startswith("model:")]
    nuevas.insert(len(nuevas), f"model: {modelo}")
    return "\n".join(nuevas) + resto


class Instalador:
    def __init__(self, forzar, simular):
        self.forzar, self.simular = forzar, simular
        self.respaldo = os.path.join(os.path.expanduser("~"), ".cache", "claude-code-skills-respaldo",
                                     datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.hechos, self.saltados = 0, []

    def _respaldar(self, destino):
        rel = os.path.splitdrive(os.path.abspath(destino))[1].lstrip("\\/")
        copia = os.path.join(self.respaldo, rel)
        os.makedirs(os.path.dirname(copia), exist_ok=True)
        if os.path.isdir(destino):
            shutil.copytree(destino, copia)
            shutil.rmtree(destino)
        else:
            shutil.copy2(destino, copia)

    def _puede(self, destino):
        if not os.path.exists(destino):
            return True
        if not self.forzar:
            self.saltados.append(destino)
            return False
        if not self.simular:
            self._respaldar(destino)
        return True

    def carpeta(self, origen, destino):
        if not self._puede(destino):
            return
        print(f"  {'(simulado) ' if self.simular else ''}{destino}")
        if not self.simular:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "evals"))
        self.hechos += 1

    def fichero(self, contenido, destino):
        if not self._puede(destino):
            return
        print(f"  {'(simulado) ' if self.simular else ''}{destino}")
        if not self.simular:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            with open(destino, "w", encoding="utf-8", newline="\n") as f:
                f.write(contenido)
        self.hechos += 1


def main():
    ap = argparse.ArgumentParser(description="Instala skills, agentes y scripts en Claude Code y/o OpenCode.")
    ap.add_argument("--claude", action="store_true", help="instalar en Claude Code")
    ap.add_argument("--opencode", action="store_true", help="instalar en OpenCode")
    ap.add_argument("--skills", action="store_true", help="solo skills (combinable)")
    ap.add_argument("--agentes", action="store_true", help="solo agentes (combinable)")
    ap.add_argument("--scripts", action="store_true", help="solo scripts (combinable)")
    ap.add_argument("--solo", help="lista de skills separadas por comas")
    ap.add_argument("--proyecto", help="instalar en este proyecto en vez de globalmente")
    ap.add_argument("--forzar", action="store_true", help="sobrescribir lo que exista (con copia de respaldo)")
    ap.add_argument("--simular", action="store_true", help="no tocar nada, solo enseñar qué haría")
    ap.add_argument("--oc-modelo-advisor")
    ap.add_argument("--oc-modelo-rapido")
    ap.add_argument("--cc-modelo-advisor")
    a = ap.parse_args()

    destinos = [d for d, si in (("claude", a.claude), ("opencode", a.opencode)) if si] or ["claude", "opencode"]
    que = [q for q, si in (("skills", a.skills), ("agentes", a.agentes), ("scripts", a.scripts)) if si] \
        or ["skills", "agentes", "scripts"]
    skills = skills_del_repo()
    if a.solo:
        pedidas = [s.strip() for s in a.solo.split(",") if s.strip()]
        faltan = [s for s in pedidas if s not in skills]
        if faltan:
            sys.exit(f"No existen en el repo: {', '.join(faltan)}")
        skills = pedidas

    casa = os.path.expanduser("~")
    claude_global = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(casa, ".claude")
    oc_global = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.join(casa, ".config"), "opencode")
    if a.proyecto:
        p = os.path.abspath(os.path.expanduser(a.proyecto))
        base = {"claude": os.path.join(p, ".claude"), "opencode": os.path.join(p, ".opencode")}
    else:
        base = {"claude": claude_global, "opencode": oc_global}
    scripts_dir = {"claude": os.path.join(claude_global, "scripts"), "opencode": os.path.join(oc_global, "scripts")}

    ins = Instalador(a.forzar, a.simular)
    for d in destinos:
        print(f"== {'Claude Code' if d == 'claude' else 'OpenCode'}")
        if "skills" in que:
            for s in skills:
                ins.carpeta(os.path.join(RAIZ, s), os.path.join(base[d], "skills", s))
        if "agentes" in que:
            for f in agentes_del_repo():
                with open(os.path.join(RAIZ, "agentes", f), encoding="utf-8") as fh:
                    texto = fh.read()
                nombre = f[:-3]
                if d == "claude":
                    if nombre == "estratega" and a.cc_modelo_advisor:
                        texto = con_modelo_claude(texto, a.cc_modelo_advisor)
                    salida = texto.replace("\r\n", "\n")
                else:
                    modelo = {"estratega": a.oc_modelo_advisor, "rapido": a.oc_modelo_rapido}.get(nombre)
                    salida = a_opencode(texto, modelo)
                ins.fichero(salida, os.path.join(base[d], "agents", f))
        if "scripts" in que:
            for f in sorted(os.listdir(os.path.join(RAIZ, "scripts"))):
                if f.endswith(".py"):
                    with open(os.path.join(RAIZ, "scripts", f), encoding="utf-8") as fh:
                        ins.fichero(fh.read(), os.path.join(scripts_dir[d], f))

    print(f"\n{'Simulado' if a.simular else 'Instalado'}: {ins.hechos} elementos.")
    if ins.saltados:
        print(f"Ya existían y NO se han tocado ({len(ins.saltados)}); usa --forzar para sobrescribirlos con copia:")
        for s in ins.saltados[:15]:
            print(f"  {s}")
        if len(ins.saltados) > 15:
            print(f"  … y {len(ins.saltados) - 15} más")
    if a.forzar and not a.simular and os.path.isdir(ins.respaldo):
        print(f"Copia de lo sobrescrito: {ins.respaldo}")
    print("Abre una sesión NUEVA de Claude Code u OpenCode para que cargue los agentes.")


if __name__ == "__main__":
    main()

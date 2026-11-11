"""Valida el repo antes de publicar. Sale con código 1 si encuentra un ERROR.

Uso:  python -I comprobar.py

Comprueba:
  1. Cada carpeta con SKILL.md: frontmatter con `name` y `description`, `name` igual al nombre
     de la carpeta (es el id que usa OpenCode) y `description` de 1024 caracteres como mucho
     (límite del formato SKILL.md).
  2. Cada agente de agentes/: frontmatter con `name` (igual al fichero) y `description`.
     Una descripción de agente de más de 1024 caracteres es solo un AVISO: el límite es del
     formato de skills; ni Claude Code ni OpenCode lo imponen a los agentes.
  3. En TODOS los ficheros de texto del repo: que no queden datos personales (patrones
     genéricos de abajo + tus propias palabras) ni cosas con pinta de secreto.

Tus palabras propias (tu nombre, tus proyectos, tus cuentas, tu usuario del PC) NO se
escriben aquí, porque este fichero se publica: van en `comprobar.local.txt` (una expresión
regular por línea; está en .gitignore) o en la variable COMPROBAR_PALABRAS separadas por «;».
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Patrones genéricos de datos personales (valen para cualquier autor).
PERSONALES = [
    # direcciones de correo reales (se permiten las de ejemplo y las noreply)
    r"[A-Za-z0-9._%+-]+@(?!(?:[a-z0-9-]+\.)*(?:example|ejemplo)\.|users\.noreply\.github\.com|anthropic\.com|github\.com)"
    r"[A-Za-z0-9-]+\.[A-Za-z0-9.-]*[a-z]{2,}",
    # carpeta personal con un nombre de usuario concreto
    r"[A-Za-z]:[\\/]+Users[\\/]+(?![<%$.]|Public\b|Default\b|usuario\b|tu-usuario\b)[A-Za-z0-9_-][A-Za-z0-9._-]*",
    r"/c/Users/(?![<$.])[A-Za-z0-9_-][A-Za-z0-9._-]*",
    r"/(?:home|Users)/(?![<$.]|usuario\b|user\b|runner\b|ana\b)[a-z][a-z0-9._-]+",
    # identificadores de hilos con UUID (p. ej. «mcp:<uuid>»)
    r"mcp:[0-9a-f]{8}-[0-9a-f]{4}-",
    # NIF / NIE españoles
    r"\b[0-9]{8}[A-HJ-NP-TV-Z]\b", r"\b[XYZ][0-9]{7}[A-Z]\b",
    # IPv4 públicas (se permiten locales, privadas, DNS públicos conocidos y rangos de documentación)
    r"\b(?!(?:127|10|0|192\.168|169\.254|172\.(?:1[6-9]|2[0-9]|3[01])|1\.1\.1|8\.8\.[48]|192\.0\.2|198\.51\.100|203\.0\.113)\.)"
    r"(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])(?:\.(?:25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])){3}\b",
]
# Excepciones conocidas: el usuario público de GitHub dueño del repo (sale en las URL del propio
# repo y de sus repos hermanos y en la LICENSE de depurar), la fuente «David Libre» de Google
# Fonts del índice de fuentes de la skill de terceros impeccable y los emails de ejemplo de break-ui.
PERMITIDO = [
    r"github\.com/davidrscout/[a-z0-9._-]+(?:\.git)?", r"\bdavidrscout\b", r"David Libre",
    r"jane@acme\.com", r"a@b\.co\b", r"git@github\.com",
    r"[0-9A-Za-z_-]*-compute@developer\.gserviceaccount\.com",  # cuenta de servicio por defecto de GCP
]
SECRETOS = [
    r"sk-[A-Za-z0-9_-]{20,}", r"sk-ant-[A-Za-z0-9_-]{10,}", r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"xox[baprs]-[A-Za-z0-9-]{10,}",
]
EXT_TEXTO = {".md", ".py", ".ps1", ".mjs", ".js", ".json", ".sh", ".txt", ".example", ".yml", ".yaml", ".toml", ""}
SALTAR_DIRS = {".git", "node_modules", "__pycache__", "datos"}
SALTAR_FICHEROS = {"comprobar.py", "comprobar.local.txt", "package-lock.json"}


def palabras_locales():
    out = [x.strip() for x in os.environ.get("COMPROBAR_PALABRAS", "").split(";") if x.strip()]
    f = os.path.join(RAIZ, "comprobar.local.txt")
    if os.path.isfile(f):
        with open(f, encoding="utf-8") as fh:
            out += [l.strip() for l in fh if l.strip() and not l.lstrip().startswith("#")]
    return out


def frontmatter(texto):
    t = texto.replace("\r\n", "\n")
    if not t.startswith("---\n"):
        return None
    fin = t.find("\n---", 4)
    if fin < 0:
        return None
    campos, clave, bloque = {}, None, []
    for linea in t[4:fin].split("\n"):
        if clave and (linea.startswith((" ", "\t")) or not linea.strip()):
            bloque.append(linea.strip())
            continue
        if clave:
            campos[clave] = " ".join(x for x in bloque if x)
            clave, bloque = None, []
        if ":" in linea and not linea.startswith(" "):
            k, v = linea.split(":", 1)
            v = v.strip()
            if v in (">", ">-", "|", "|-", ">+", "|+"):
                clave = k.strip()
            else:
                campos[k.strip()] = v.strip("'\"")
    if clave:
        campos[clave] = " ".join(x for x in bloque if x)
    return campos


def main():
    errores, avisos = [], []
    n_skills = n_agentes = n_ficheros = 0

    for d in sorted(os.listdir(RAIZ)):
        p = os.path.join(RAIZ, d, "SKILL.md")
        if not os.path.isfile(p):
            continue
        n_skills += 1
        with open(p, encoding="utf-8") as fh:
            c = frontmatter(fh.read())
        if c is None:
            errores.append(f"{d}/SKILL.md: sin frontmatter")
            continue
        if not c.get("name"):
            errores.append(f"{d}/SKILL.md: falta name")
        elif c["name"] != d:
            errores.append(f"{d}/SKILL.md: name «{c['name']}» distinto de la carpeta")
        desc = c.get("description", "")
        if not desc:
            errores.append(f"{d}/SKILL.md: falta description")
        elif len(desc) > 1024:
            errores.append(f"{d}/SKILL.md: description de {len(desc)} caracteres (máximo 1024)")

    carpeta = os.path.join(RAIZ, "agentes")
    for f in sorted(os.listdir(carpeta)) if os.path.isdir(carpeta) else []:
        if not f.endswith(".md") or f == "README.md":
            continue
        n_agentes += 1
        with open(os.path.join(carpeta, f), encoding="utf-8") as fh:
            c = frontmatter(fh.read())
        if c is None:
            errores.append(f"agentes/{f}: sin frontmatter")
            continue
        if c.get("name") != f[:-3]:
            errores.append(f"agentes/{f}: name «{c.get('name')}» distinto del fichero")
        desc = c.get("description", "")
        if not desc:
            errores.append(f"agentes/{f}: falta description")
        elif len(desc) > 1024:
            avisos.append(f"agentes/{f}: description de {len(desc)} caracteres")

    locales = palabras_locales()
    pers = re.compile("|".join(PERSONALES + locales), re.I)
    perm = re.compile("|".join(PERMITIDO), re.I)
    secr = re.compile("|".join(SECRETOS))
    for base, dirs, ficheros in os.walk(RAIZ):
        dirs[:] = [x for x in dirs if x not in SALTAR_DIRS]
        for f in ficheros:
            if os.path.splitext(f)[1].lower() not in EXT_TEXTO or f in SALTAR_FICHEROS:
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, RAIZ).replace("\\", "/")
            try:
                with open(p, encoding="utf-8") as fh:
                    texto = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            n_ficheros += 1
            for i, linea in enumerate(texto.splitlines(), 1):
                limpia = perm.sub("", linea)
                for m in pers.finditer(limpia):
                    errores.append(f"{rel}:{i}: dato personal «{m.group(0)}»")
                for m in secr.finditer(linea):
                    errores.append(f"{rel}:{i}: posible secreto «{m.group(0)[:12]}…»")

    print(f"Revisados: {n_skills} skills, {n_agentes} agentes, {n_ficheros} ficheros de texto "
          f"({len(locales)} palabras propias de comprobar.local.txt / COMPROBAR_PALABRAS).")
    if avisos:
        print(f"AVISOS ({len(avisos)}; no bloquean):")
        for a in avisos[:5]:
            print(f"  {a}")
        if len(avisos) > 5:
            print(f"  … y {len(avisos) - 5} más")
    if errores:
        print(f"ERRORES ({len(errores)}):")
        for e in errores:
            print(f"  {e}")
        sys.exit(1)
    print("OK: sin errores.")


if __name__ == "__main__":
    main()

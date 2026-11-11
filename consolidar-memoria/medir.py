"""Mide la salud de una carpeta de memoria: tamaño del índice, enlaces rotos, huérfanos,
[[enlaces]] colgantes, notas sin frontmatter y ficheros gordos.

Uso:  python -I medir.py <carpeta-de-memoria> [--historico indice_historico.md]

La carpeta tiene un índice MEMORY.md (una línea por recuerdo, con enlaces (fichero.md))
y una nota .md por recuerdo con frontmatter `name:`.
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def leer(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def norm(s):
    return s.strip().replace("_", "-").lower()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--historico", default="indice_historico.md")
    a = ap.parse_args()
    m = a.carpeta
    if not os.path.isfile(os.path.join(m, "MEMORY.md")):
        sys.exit(f"No hay MEMORY.md en {m}")
    indice = leer(os.path.join(m, "MEMORY.md"))
    hist = leer(os.path.join(m, a.historico))
    notas = sorted(f for f in os.listdir(m) if f.endswith(".md"))
    cerrados = os.path.join(m, "_cerrados")
    notas_cerradas = sorted(f for f in os.listdir(cerrados) if f.endswith(".md")) if os.path.isdir(cerrados) else []

    lineas = indice.splitlines()
    print(f"== Índice MEMORY.md: {len(lineas)} líneas, {len(indice.encode('utf-8'))} bytes (objetivo < 12000)")
    for l in lineas:
        visible = re.sub(r"\([^)]*\.md\)", "", l)
        if len(visible) > 160:
            print(f"   línea larga ({len(visible)} car. visibles): {visible[:80]}…")

    print("== Enlaces rotos en los índices")
    enlaces = set(re.findall(r"\(([A-Za-z_0-9.\-]+\.md)\)", indice + "\n" + hist))
    for f in sorted(enlaces):
        if not os.path.isfile(os.path.join(m, f)):
            print(f"   ROTO: {f}")

    print("== Huérfanos (nota sin enlace en ningún índice)")
    for f in notas:
        if f in ("MEMORY.md", a.historico):
            continue
        if f"({f})" not in indice and f"({f})" not in hist:
            print(f"   {f}")

    print("== [[enlaces]] a nombres que no existen")
    conocidos = set()
    for carpeta, lista in ((m, notas), (cerrados, notas_cerradas)):
        for f in lista:
            conocidos.add(norm(f[:-3]))
            mm = re.search(r"^name:\s*(.+)$", leer(os.path.join(carpeta, f)), re.M)
            if mm:
                conocidos.add(norm(mm.group(1)))
    colgantes = set()
    for f in notas:
        texto = re.sub(r"`[^`]*`", "", leer(os.path.join(m, f)))
        for n in re.findall(r"\[\[([^\]]+)\]\]", texto):
            if norm(n) not in conocidos:
                colgantes.add(n)
    for n in sorted(colgantes):
        print(f"   [[{n}]]")

    print("== Sin frontmatter name:")
    for f in notas:
        if f in ("MEMORY.md", a.historico):
            continue
        if not re.search(r"^name:", leer(os.path.join(m, f)), re.M):
            print(f"   {f}")

    print("== Ficheros > 15 KB (candidatos a resumir)")
    gordos = [(os.path.getsize(os.path.join(m, f)) // 1024, f) for f in notas
              if os.path.getsize(os.path.join(m, f)) > 15 * 1024]
    for kb, f in sorted(gordos, reverse=True):
        print(f"   {kb} KB  {f}")

    log = leer(os.path.join(m, "_consolidacion.log")).strip().splitlines()
    print(f"== Última pasada: {log[-1] if log else 'ninguna'}")


if __name__ == "__main__":
    main()

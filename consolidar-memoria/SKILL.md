---
name: consolidar-memoria
description: >-
  Pasada de consolidación («dreaming») de la memoria persistente de Claude Code (~/.claude/projects/<proyecto>/memory/), según el artículo de Anthropic «The components of agent memory». Contrasta las notas con las transcripciones reales, cierra los pendientes resueltos, corrige notas erróneas u obsoletas, arregla enlaces rotos, huérfanos y [[enlaces]] colgantes, fusiona duplicados y mantiene MEMORY.md como un índice pequeño. Úsala SOLO cuando el usuario invoque /consolidar-memoria o pida «consolida la memoria», «sueña», «dreaming», «limpia la memoria» o «revisa la memoria». En OpenCode no hay memoria automática: sirve igual sobre una carpeta de notas con el mismo formato.
---

# /consolidar-memoria — pasada de «dreaming» sobre la memoria

## Dónde está cada cosa

- **Memoria (Claude Code):** `~/.claude/projects/<carpeta-del-proyecto>/memory/`, con
  `MEMORY.md` como índice (una línea por recuerdo) y un fichero `.md` por recuerdo con
  frontmatter `name` / `description`. La carpeta del proyecto es la ruta del proyecto con
  los separadores cambiados por guiones (p. ej. `~/dev/tienda` → `-home-ana-dev-tienda`).
  Si el usuario no dice cuál, usa la del proyecto actual; si hay varias, pregunta cuál.
- **Transcripciones (la verdad de referencia):** `~/.claude/projects/*/*.jsonl`.
- **Reglas de escritura:** si la memoria tiene una nota de reglas (p. ej.
  `feedback_reglas_memoria.md`), léela primero y cúmplela.
- **OpenCode:** no tiene memoria persistente automática. Si el usuario guarda notas en una
  carpeta con este mismo formato (índice `MEMORY.md` + una nota por fichero), la pasada
  de estructura e índice (pasos 2-4) vale igual pasando esa carpeta a `medir.py`. Para el
  paso 1, exporta las sesiones con `opencode session export <id> > sesion.json` y
  conviértelas con `conversacion.py` (en `scripts/` del repo); `extraer_corpus.py` solo
  lee transcripciones de Claude Code.

Los scripts de esta skill están junto a este fichero (`~/.claude/skills/consolidar-memoria/`
o `~/.config/opencode/skills/consolidar-memoria/`).

## 0. Copia y medida

1. Copia `MEMORY.md` (y el índice histórico si existe, p. ej. `indice_historico.md`) a una
   carpeta temporal.
2. Ejecuta `python -I medir.py <carpeta-de-memoria>` y guarda la salida: es la línea base.

## 1. Corregir contra las transcripciones (lo más importante)

Saca el texto de las transcripciones a un corpus buscable (solo mensajes de usuario y
asistente, sin resultados de herramientas):

`python -I extraer_corpus.py <carpeta-temporal>/corpus --desde AAAA-MM-DD [--proyecto <carpeta-del-proyecto>]`

Usa como `--desde` la fecha de la pasada anterior (última línea de `_consolidacion.log`);
por defecto, los últimos 30 días.

⚠️ **Trampa:** los timestamps de las transcripciones están en **UTC**. Antes de escribir una
fecha u hora en una nota, pásala a la zona horaria del usuario. Si no, «corriges» fechas
que estaban bien.

Una nota errónea u obsoleta se lee y se da por buena en cada sesión. Aquí se contrasta con
lo que pasó de verdad.
- **Prioriza lo que cambia:** primero los pendientes vivos del índice, después las notas
  modificadas desde la última pasada. No revises todas las notas.
- Para cada nota, busca en el corpus por términos distintivos de la nota (`grep -l`) en las
  sesiones posteriores a su fecha y lee solo los fragmentos relevantes. Para búsquedas en
  volumen usa subagentes baratos (el agente `rapido` de este repo): uno por grupo de notas,
  y cada uno devuelve hallazgos, no edita.
- Por cada hallazgo:
  - Si el pendiente ya se resolvió → ciérralo: la línea sale de los pendientes y pasa al
    índice histórico con la fecha de cierre.
  - Si la nota dice algo que la transcripción contradice → corrígela y añade
    `[corregido DD/MM: qué decía y por qué estaba mal]`.
  - Si se confirmó → marca `[confirmado DD/MM: cómo]`.
  - Si no hay evidencia en ninguna dirección → no la toques. No inventes estados.
- Lo que se puede comprobar en vivo (un servicio, una URL, un saldo) no se «corrige» de
  memoria: si importa, compruébalo o deja `[sin comprobar]`.

## 2. Estructura

- **Huérfanos** → enlázalos en el índice que corresponda (activo o histórico).
- **Enlaces rotos** → apúntalos al fichero existente que cubre ese tema, o quítalos.
- **[[enlaces]] colgantes** → si existe una nota con otro nombre que cubre el tema,
  redirígelo. Si es algo que merece nota, apúntalo en el informe (no crees notas vacías).
- **Duplicados** (dos notas del mismo tema) → fusiona en la más reciente y deja la otra en
  `_cerrados/` con una línea que apunte a la buena. Nunca borres sin dejar copia.
- **Ficheros > 15 KB** → como máximo 3 por pasada: resume arriba el estado actual (qué es,
  estado, qué falta) y mueve el historial detallado a `_cerrados/<nombre>_historial.md`.
  No se pierde información.

## 3. Índice (la capa que se inyecta en cada sesión)

- `MEMORY.md` < 12 KB, una línea por recuerdo, ≤ 160 caracteres, sin detalle: el detalle
  está en el fichero.
- Antes de recortar una línea, comprueba con `grep` que su dato está en el fichero
  enlazado. Si no está, pásalo al fichero primero.
- Nada del índice se pierde: compara los conjuntos de enlaces antes y después (todo enlace
  antiguo tiene que seguir en `MEMORY.md` o en el índice histórico).

## 4. Cierre

1. Vuelve a ejecutar `medir.py` y compara con la línea base.
2. Añade una línea a `_consolidacion.log` en la memoria:
   `AAAA-MM-DD HH:MM | pendientes cerrados N | corregidas N | confirmadas N | fusionadas N | índice X→Y KB`.
3. Informa al usuario punto por punto: qué se cerró, qué se corrigió (con lo que decía
   antes), qué no se pudo comprobar y qué decisiones le tocan a él.

## Reglas

- Trabajo en paralelo: cada subagente escribe solo sus propios ficheros; los cambios en
  `MEMORY.md` los hace solo el orquestador.
- No cierres un pendiente sin evidencia en una transcripción o sin comprobarlo en vivo.
- No borres temporales ni lances diálogos de confirmación si la pasada es desatendida.
- No mezcles memorias de proyectos distintos.

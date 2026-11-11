# Skills para Claude Code y OpenCode

Colección de skills, agentes y servidores MCP: método de trabajo con agentes, vídeo y motion
en código y diseño de interfaces.
Cada carpeta de la raíz con un `SKILL.md` es una skill en formato estándar (cabecera `name` +
`description` y el cuerpo con las instrucciones), así que funciona igual en **Claude Code** y
en **OpenCode** (gratis, [opencode.ai](https://opencode.ai)). Aunque el texto de algunas diga
«Claude Code», el agente las usa igual; las skills propias traen una tabla de equivalencias
con OpenCode donde hace falta.

| Carpeta | Qué hay |
|---|---|
| `<skill>/` | Una skill por carpeta (propias y de terceros). |
| `agentes/` | 236 agentes: el advisor `estratega`, el ayudante barato `rapido` y la plantilla `equipo-*` de `super-equipo`. |
| `scripts/` | `conversacion.py`: vuelca una conversación de Claude Code u OpenCode a markdown (lo usa el `estratega`). |
| `mcp/` | Servidores MCP: `pc-control` (controlar Windows) y `centro-ia` (repartir tareas entre IAs, experimental). |
| `instalar.py` | Instala skills, agentes y scripts en Claude Code y/o OpenCode. |
| `comprobar.py` | Valida el repo (frontmatter, longitud de descripciones, datos personales). |

## Instalación

Lo más cómodo es el instalador (Python 3.8+), que copia las skills, los agentes (convertidos
al formato de OpenCode cuando toca) y los scripts, y **no sobrescribe nada que ya tengas**
salvo con `--forzar` (y entonces guarda copia):

```bash
git clone https://github.com/davidrscout/claude-code-skills.git
cd claude-code-skills
python instalar.py                 # todo, en Claude Code y en OpenCode
python instalar.py --opencode      # solo OpenCode
python instalar.py --solo techo,depurar --skills   # solo esas skills
python instalar.py --proyecto ~/dev/mi-app         # en el proyecto, no global
python instalar.py --simular       # enseña qué haría
```

`python instalar.py --help` explica todas las opciones.

### A mano

**OpenCode** (lee las skills de `~/.config/opencode/skills/`, de `.opencode/skills/` dentro del
proyecto y también de `~/.claude/skills/`; ver [docs](https://opencode.ai/docs/skills)).
Copia solo las carpetas que tienen `SKILL.md` (las demás, como `agentes/` o `mcp/`, no son
skills):

```bash
git clone https://github.com/davidrscout/claude-code-skills.git
mkdir -p ~/.config/opencode/skills
for d in claude-code-skills/*/; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.config/opencode/skills/; done
```

En Windows (PowerShell):

```powershell
git clone https://github.com/davidrscout/claude-code-skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.config\opencode\skills" | Out-Null
Get-ChildItem claude-code-skills -Directory | Where-Object { Test-Path "$($_.FullName)\SKILL.md" } |
  Copy-Item -Recurse -Force -Destination "$env:USERPROFILE\.config\opencode\skills"
```

Para instalar solo algunas, copia solo esas carpetas. Para que una skill valga solo en un
proyecto, cópiala en `<proyecto>/.opencode/skills/`.

**Claude Code**: igual, pero en `~/.claude/skills/` (global) o `.claude/skills/` (proyecto).

Comprueba que carga pidiéndole al agente, por ejemplo, «usa la skill techo» o escribiendo
`/techo` (en OpenCode también vale `@techo` en el mensaje).

## Skills propias

| Skill | Qué hace | Cuándo se usa |
|---|---|---|
| `depurar` | Arreglar errores por la causa con evidencia (fichero:línea + valor observado), no por el síntoma, y no meter fallos tontos. Trae `AGENTS-snippet.md` para agentes que leen AGENTS.md. | Siempre que haya un error o un test que falla. |
| `orquestador` | El agente principal trocea el encargo, reparte cada trozo a subagentes u otras IAs con briefs autocontenidos, elige modelo por capacidad, verifica y avisa con evidencia; incluye cuándo es obligatorio consultar al `estratega` y cómo pasarle la conversación volcada. | Proyectos con varias tareas a la vez; «orquesta», «repártelo», «hazlo con subagentes». |
| `techo` | Dictamina si un proyecto está en un techo estructural (cada mejora es otro parche) o si el camino actual aún da de sí, con evidencia y caminos alternativos con coste. | «¿Sigo mejorando esto o cambio de enfoque?», el mismo síntoma por tercera vez. |
| `perfeccionista` | Bucle de mejora con contrato, rúbrica congelada y jurado adversarial que puntúa de 0 a 10. | Solo bajo petición, cuando algo tiene que quedar perfecto. |
| `super-equipo` | Orquesta un equipo de 24 leads de área y 210 especialistas con contextos aislados: arquitecto con contratos, implementación en paralelo, revisión adversarial e integración. Usa los agentes de `agentes/`. | Solo bajo petición, en encargos grandes y multi-dominio. |
| `consolidar-memoria` | Pasada de limpieza de la memoria persistente de Claude Code: contrasta notas con las transcripciones, cierra pendientes, arregla enlaces y mantiene pequeño el índice. Con `medir.py` y `extraer_corpus.py`. | De vez en cuando, o cuando la memoria se llena de notas viejas. En OpenCode, sobre una carpeta de notas propia. |
| `codex-image` | Genera o edita imágenes con la app OpenAI Codex y una suscripción de ChatGPT, sin API key (Windows). | Solo bajo petición. |

## Agentes

En `agentes/` (detalle en [agentes/README.md](agentes/README.md)):

- `estratega`: advisor de solo lectura con el modelo que mejor razona; devuelve un dictamen
  (decisión, pasos, cómo conseguirlo, qué no hacer). Por defecto `model: opus`; cámbialo por
  el mejor modelo que tengas.
- `rapido`: subagente barato para trabajo mecánico (resumir, buscar, contar, comprobar).
- `equipo-*`: los 234 miembros de `super-equipo`.

`python instalar.py --agentes` los copia a `~/.claude/agents/` y los convierte al formato de
OpenCode (`mode: subagent`, `permissions`) en `~/.config/opencode/agents/`. Para el volcado
de conversaciones que necesita el `estratega`, el instalador deja `conversacion.py` en
`~/.claude/scripts/` y en `~/.config/opencode/scripts/`:

```bash
# Claude Code: la sesión es un .jsonl en ~/.claude/projects/<carpeta-del-proyecto>/
python -I ~/.claude/scripts/conversacion.py ~/.claude/projects/<carpeta>/<sesión>.jsonl conversacion.md
# OpenCode: guarda las sesiones en SQLite; se exportan a JSON y se vuelcan igual
opencode session export <id> > sesion.json
python -I ~/.config/opencode/scripts/conversacion.py sesion.json conversacion.md
```

## MCP

| Servidor | Qué hace | Estado |
|---|---|---|
| [`mcp/pc-control`](mcp/pc-control/README.md) | Ver la pantalla y usar ratón y teclado en Windows; árbol de accesibilidad de una app. Node, sin binarios propios. | Probado en Windows 11. |
| [`mcp/centro-ia`](mcp/centro-ia/README.md) | Delegar tareas en otras IAs por su CLI o API (Claude Code, Codex, Kimi, OpenCode, Experiential Labs) con cadenas `auto:<tipo>` que saltan al siguiente motor si uno falla y aprenden de las notas. Python sin dependencias. | **Experimental**: hay que configurar cuentas y cadenas. |

Cómo añadirlos (detalle en cada README):

- **OpenCode**, en `opencode.json`:
  ```jsonc
  { "mcp": { "servers": {
      "pc-control": { "type": "local", "command": ["node", "/ruta/al/repo/mcp/pc-control/server.mjs"] },
      "centro-ia":  { "type": "local", "command": ["python", "-I", "/ruta/al/repo/mcp/centro-ia/mcp_ias.py"] }
  } } }
  ```
- **Claude Code**:
  ```bash
  claude mcp add pc-control -s user -- node /ruta/al/repo/mcp/pc-control/server.mjs
  claude mcp add centro-ia -s user -- python -I /ruta/al/repo/mcp/centro-ia/mcp_ias.py
  ```

## Otros repos míos relacionados

- [depurar-skill](https://github.com/davidrscout/depurar-skill): la skill `depurar` con instaladores propios (`install.sh` / `install.ps1`).
- [clips-automaticos-skill](https://github.com/davidrscout/clips-automaticos-skill): clips verticales automáticos y subida a TikTok y YouTube Shorts, multi-cuenta.
- [claude-multicuenta](https://github.com/davidrscout/claude-multicuenta): varias cuentas de Claude Code en el mismo PC con Windows, compartiendo memoria, skills y agentes (`centro-ia` lee su `cuentas.json` si existe).
- [super-equipo-skill](https://github.com/davidrscout/super-equipo-skill) y [codex-image-skill](https://github.com/davidrscout/codex-image-skill): versiones sueltas de `super-equipo` y `codex-image`.

## Skills de terceros (redistribuidas según su licencia)

Copias sin cambios; cada carpeta incluye la licencia original (`LICENSE`) y su origen (`ORIGEN.md`). Todo el mérito es de sus autores.

| Skills | Origen | Licencia |
|---|---|---|
| `animated-chart`, `apple-launch-film`, `brand-intake`, `launch-video`, `loop-cover`, `milestone-reveal`, `model-showdown`, `motion-brief-writer`, `motion-effects`, `newsletter-promo`, `reel-export`, `title-sequence-3d`, `vox-explainer` | [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) | MIT |
| `after-effects`, `animation-principles`, `beat-sync-editing`, `color-motion`, `logo-animation`, `motion-art-direction`, `motion-background`, `remotion-video`, `shot-composition` | [iart-ai/motion-design-skills](https://github.com/iart-ai/motion-design-skills) | MIT |
| `animation-vocabulary`, `break-ui`, `emil-design-eng`, `find-animation-opportunities`, `improve-animations`, `review-animations` | [emilkowalski/skill](https://github.com/emilkowalski/skill) | MIT |
| `context-budget`, `design-system`, `search-first` | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | MIT |
| `business-motion-film` | [echris6/motion-video-kit](https://github.com/echris6/motion-video-kit) | MIT |
| `impeccable` | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | Apache-2.0 |
| `pixel2motion` | [nolangz/pixel2motion](https://github.com/nolangz/pixel2motion) | MIT |

## No incluidas por licencia

- `remotion-* (13)`: remotion-dev/skills no publica licencia: todos los derechos reservados.
- `onetake`: PolyForm Noncommercial: solo uso no comercial.
- `guizang-product-video`: AGPL-3.0 con recursos bajo BUSL-1.1.
- `security-audit` (y el resto del plugin Claude Security): propiedad de Anthropic, su licencia prohíbe redistribuirla.

## Antes de publicar cambios

`python -I comprobar.py` tiene que terminar en `OK`: revisa el frontmatter de skills y
agentes, que ninguna descripción de skill pase de 1024 caracteres y que no se cuelen datos
personales ni secretos.

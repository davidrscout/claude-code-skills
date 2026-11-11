# Skills para Claude Code y OpenCode

Colección de skills: vídeo y motion en código, diseño de interfaces y método de trabajo.
Cada carpeta es una skill en formato estándar `SKILL.md` (cabecera `name` + `description` y el cuerpo con las instrucciones), así que funciona igual en **Claude Code** y en **OpenCode** (gratis, [opencode.ai](https://opencode.ai)). Aunque el texto de algunas diga «Claude Code», el agente las usa igual.

## Instalación

**OpenCode** (lee las skills de `~/.config/opencode/skills/`, de `.opencode/skills/` dentro del proyecto y también de `~/.claude/skills/`; ver [docs](https://opencode.ai/docs/skills)):

```bash
git clone https://github.com/davidrscout/claude-code-skills.git
mkdir -p ~/.config/opencode/skills
cp -r claude-code-skills/*/ ~/.config/opencode/skills/
```

En Windows (PowerShell):

```powershell
git clone https://github.com/davidrscout/claude-code-skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.config\opencode\skills" | Out-Null
Get-ChildItem claude-code-skills -Directory | Copy-Item -Recurse -Force -Destination "$env:USERPROFILE\.config\opencode\skills"
```

Para instalar solo algunas, copia solo esas carpetas. Para que una skill valga solo en un proyecto, cópiala en `<proyecto>/.opencode/skills/`.

**Claude Code**: igual, pero en `~/.claude/skills/` (global) o `.claude/skills/` (proyecto).

Comprueba que carga pidiéndole al agente, por ejemplo, «usa la skill techo» o escribiendo `/techo`.

## Skills propias

| Skill | Qué hace |
|---|---|
| `techo` | Dictamina si un proyecto está en un techo estructural o si el camino actual aún da de sí. |
| `perfeccionista` | Bucle de mejora con contrato, rúbrica y jurado adversarial que puntúa de 0 a 10. Solo bajo petición. |
| `super-equipo` | Orquesta un equipo de jefes de área y especialistas con contextos aislados. Solo bajo petición; necesita los agentes `equipo-*` (no incluidos). |
| `codex-image` | Genera imágenes con la app OpenAI Codex y una suscripción de ChatGPT (Windows). Solo bajo petición. |

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

## No incluidas por ser personales

- `orquestador` y `consolidar-memoria`: dependen de la configuración concreta de un PC (T3 Code, cuentas y rutas de memoria); no sirven fuera de ese entorno.

# Agentes

236 agentes en formato de Claude Code (un `.md` con frontmatter `name`, `description` y,
en algunos, `tools` y `model`; el cuerpo es su system prompt):

| Agente | Qué es |
|---|---|
| `estratega` | Advisor de solo lectura con el modelo que mejor razona. Lee la conversación volcada (`scripts/conversacion.py`), el código y las notas, y devuelve un dictamen accionable. Lo usa la skill `orquestador`. |
| `rapido` | Subagente barato (modelo pequeño) para trabajo mecánico de volumen: resumir, buscar, contar, comprobar estados. Solo lee. |
| `equipo-*` (234) | La plantilla de la skill `super-equipo`: 24 leads de área y transversales (`equipo-arquitecto`, `equipo-integrador`, `equipo-revisor`…) y 210 especialistas por tecnología (`equipo-backend-python`, `equipo-revisor-seguridad`…). El roster completo está en `super-equipo/references/roster.md`. |

## Instalación

Desde la raíz del repo:

```bash
python instalar.py --agentes              # Claude Code y OpenCode
python instalar.py --agentes --opencode   # solo OpenCode
```

- **Claude Code**: se copian tal cual a `~/.claude/agents/`.
- **OpenCode**: se convierten al formato V2 en `~/.config/opencode/agents/`:
  `description` + `mode: subagent` y, en los que en Claude Code no tienen `Edit`/`Write`
  (`estratega`, `rapido`, `equipo-revisor*`), `permissions` con la edición denegada. El
  `model` de Claude Code (`opus`, `haiku`) no vale en OpenCode y se quita: el agente hereda el
  modelo de la sesión. Para fijarlo:
  `python instalar.py --agentes --opencode --oc-modelo-advisor proveedor/modelo --oc-modelo-rapido proveedor/modelo`
  (mira los ids con `opencode models`).

Abre una sesión nueva para que se carguen. En OpenCode se lanzan con la herramienta
`subagent` (o pidiéndolo: «usa el subagente `equipo-revisor`»); en Claude Code, con `Agent`.

## Modelo del advisor

`estratega.md` trae `model: opus`. Si tu plan tiene un modelo que razona mejor, cámbialo
(por ejemplo con `python instalar.py --agentes --claude --cc-modelo-advisor <id-del-modelo> --forzar`).

## Descripciones largas

157 descripciones de `equipo-*` pasan de 1024 caracteres. Es a propósito: el
orquestador elige a quién contratar leyendo esa descripción (qué hace y qué NO hace), y
ni Claude Code ni OpenCode limitan la descripción de un agente. El límite de 1024 es del
formato de skills, y `comprobar.py` lo aplica solo a las skills.

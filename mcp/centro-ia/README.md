# centro-ia — repartir tareas entre varias IAs (MCP) · EXPERIMENTAL

Servidor MCP local (stdio, Python sin dependencias) que deja al agente de tu sesión delegar
trabajo en **otras IAs a través de sus CLIs o APIs** y aprender cuál rinde mejor en cada tipo
de tarea:

| Motor | Qué lanza | Tipo |
|---|---|---|
| `claude:<cuenta>` | Claude Code (`claude -p`) con la cuenta configurada | agéntico (lee, edita, ejecuta en `cwd`) |
| `codex` | Codex CLI (`codex exec`) | agéntico |
| `kimi` | Kimi Code CLI (`kimi -p`) | agéntico |
| `opencode:<proveedor/modelo>` | OpenCode (`opencode run -m …`) | agéntico |
| `exp:<modelo>` | Experiential Labs por API (OpenAI-compatible) | solo texto, rápido |
| `auto:<tipo>` | una **cadena** de los anteriores con respaldo automático | — |

Las cadenas `auto:<tipo>` (texto, sencillo, front, codigo, investigacion, lote, largo,
revision, pensar y los tipos que añadas) prueban los motores en orden y pasan al siguiente
si uno falla, se queda sin cupo o devuelve vacío. El orden se reordena solo con las notas
que el agente pone tras revisar cada trabajo (`ia_valorar`).

> **Experimental.** Nació para un PC con varias suscripciones y está pensado sobre todo para
> Windows (en Linux/macOS debería funcionar, pero no está probado). Lee «Qué hay que
> configurar» antes de usarlo. Si solo tienes una IA, no te hace falta: usa los subagentes de
> tu herramienta.

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `ias_estado` | Cupos de las cuentas (Claude Code, Codex, Kimi), modelos gratis ahora, saldo de APIs y el ranking de cada cadena. |
| `ia_delegar` | Encarga una tarea a un motor o a una cadena `auto:<tipo>`. `esperar=false` devuelve un id para recoger después. |
| `ia_resultado` | Recoge un trabajo lanzado con `esperar=false`. |
| `ia_comparar` | Manda el mismo prompt a varios motores en paralelo y devuelve todas las respuestas. |
| `ia_valorar` | Nota 1-5 a un trabajo ya revisado; con esto se reordenan las cadenas. |
| `ia_cancelar` | Cancela un trabajo en curso. |

Al conectarse, el servidor entrega al agente las instrucciones de `politica.md` (cómo y
cuándo delegar). Edítalas a tu gusto.

## Requisitos

- Python 3.10 o superior (solo biblioteca estándar).
- Las CLIs que quieras usar, instaladas y con sesión iniciada: `claude`, `codex`, `kimi`,
  `opencode`. Las que no tengas simplemente fallan y la cadena pasa a la siguiente.

## Instalación

1. Copia `config.json.example` como `config.json` (en esta misma carpeta) y ajústalo.
2. Comprueba que arranca:
   ```bash
   python -I mcp_ias.py
   ```
   Se queda esperando JSON-RPC por stdin (sal con Ctrl+C). Es lo normal en un MCP.
3. Regístralo en tu agente:

   **OpenCode** (`~/.config/opencode/opencode.json` o el `opencode.json` del proyecto):
   ```jsonc
   {
     "$schema": "https://opencode.ai/config.json",
     "mcp": {
       "servers": {
         "centro-ia": {
           "type": "local",
           "command": ["python", "-I", "C:/ruta/a/claude-code-skills/mcp/centro-ia/mcp_ias.py"]
         }
       }
     }
   }
   ```
   O: `opencode mcp add centro-ia --global -- python -I C:/ruta/a/claude-code-skills/mcp/centro-ia/mcp_ias.py`.

   **Claude Code**:
   ```bash
   claude mcp add centro-ia -s user -- python -I C:/ruta/a/claude-code-skills/mcp/centro-ia/mcp_ias.py
   ```

## Qué hay que configurar (`config.json`)

Todas las claves son opcionales; lo que falte toma el valor de serie (`CONFIG_DEFECTO` en
`nucleo.py`). **Ninguna clave de API va en el fichero.**

| Clave | Para qué |
|---|---|
| `cuentas_claude` | Lista de cuentas de Claude Code: `id`, `dir` (carpeta de configuración; `~/.claude` es la normal, otra carpeta se pasa como `CLAUDE_CONFIG_DIR`), `etiqueta` y opcionalmente `solo_para` (la cuenta solo se usa para eso y se marca en `ias_estado`). Sin esta clave se lee `~/.claude-cuentas/cuentas.json` si existe y, si no, hay una sola cuenta `principal`. |
| `cadenas` | Cadenas propias por tipo: `"tipo": ["motor|modelo", …]`. Sustituyen a las de serie para ese tipo. Comodines: `opencode:@ocgratis` (el primer modelo gratis de OpenCode sondeado) y `exp:@expgratis` (lo mismo en Experiential). |
| `tipos` | Tipos de tarea nuevos o descripciones propias (un tipo nuevo necesita su entrada en `cadenas`). |
| `claude_modelos`, `codex_modelos` | Modelos que se ofrecen para esos motores. |
| `exp_vigilar` | Modelos de Experiential Labs cuyo precio se sondea con una llamada mínima. Vacío por defecto: **sondear un modelo de pago gasta saldo**. |
| `sondeo_horas` | Cada cuánto se vuelve a comprobar qué modelos son gratis (en segundo plano, al llamar a `ias_estado`). Los de OpenCode (`opencode/*-free`) se sondean con `opencode run`, gratis. |
| `renovar_tokens_auto` | Si un token OAuth de Claude Code ha caducado, lanza una llamada mínima con Haiku para que la CLI lo renueve. |
| `timeout_agentico_min`, `timeout_exp_min` | Límites de tiempo por trabajo. |
| `aviso_comando` | Comando opcional para avisarte cuando un modelo pasa de gratis a pago o al revés (p. ej. `["python", "/ruta/avisar.py"]`; se le añaden título y mensaje). |
| `trabajo_dir` | Carpeta de trabajo por defecto si no se pasa `cwd`. |

Variables de entorno opcionales: `EXPLABS_API_KEY` (Experiential Labs) y `FAL_KEY` (saldo de
fal.ai en `ias_estado`). En Windows también se leen de las variables de usuario.

### Cómo lee los cupos (y sus límites)

- **Claude Code**: lee el token OAuth de `<dir>/.credentials.json` y consulta el uso en la
  API de Anthropic. Es un endpoint interno no documentado: puede cambiar o dejar de
  funcionar sin aviso; entonces `ias_estado` dirá `error` y lo demás sigue funcionando.
- **Codex**: lee los `rate_limits` del último registro de sesión en `~/.codex/sessions/`.
- **Kimi**: lee sus credenciales en `~/.kimi-code/credentials/` y consulta su API de uso.
- Ningún token sale del proceso salvo hacia el servicio al que pertenece.

### Seguridad

Los motores agénticos se lanzan **sin pedir permisos** (`--dangerously-skip-permissions` en
Claude Code, `--dangerously-bypass-approvals-and-sandbox` en Codex, `--auto` en OpenCode):
pueden editar y ejecutar lo que quieran dentro de `cwd`. Úsalo solo en tu máquina y con
carpetas de trabajo que puedas perder. Una IA delegada puede volver a delegar una vez como
mucho (profundidad máxima 2).

## Datos que guarda

Todo en `datos/` (está en `.gitignore`): `historial.jsonl` (cada trabajo, con la respuesta
recortada), `valoraciones.jsonl` (las notas), `trabajos/<id>.jsonl` (eventos de cada
trabajo), `gratis.json` (último sondeo) y cachés de uso. Bórralo para empezar de cero.

## Calibrar (opcional)

`calibrar.py` lanza tareas de prueba con corrector objetivo (`calib_tareas.py`) contra los
motores de `CANDIDATOS` y guarda los resultados en `datos/calibracion/<fecha>/`.
`analizar_calibracion.py <carpeta> --aplicar` los convierte en `datos/orden_inicial.json`, el
orden de partida de cada cadena. Edita `CANDIDATOS` con los motores que tengas antes de
lanzarlo: cada ejecución gasta cupo de esas IAs.

## Qué se ha comprobado

- Arranca desde una copia limpia con `config.json.example`, responde a `initialize` y
  `tools/list`, y delega de verdad en `opencode:opencode/<modelo>-free`.
- `ias_estado` con las cuentas de ejemplo y sin sesiones iniciadas devuelve el estado y las
  cadenas sin errores.
- No probado: Linux/macOS, Kimi, y varias cuentas reales de Claude Code a la vez fuera del
  equipo original.

# pc-control — controlar Windows desde un agente de IA (MCP)

Servidor MCP local (stdio) que deja a Claude Code, OpenCode o cualquier cliente MCP ver la
pantalla y usar el ratón y el teclado de un PC con **Windows 10/11**.

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `screenshot` | Captura la pantalla completa (JPEG reducido, 1366 px de ancho por defecto). |
| `click`, `move`, `drag`, `scroll` | Ratón. Las coordenadas van en el espacio de la **última captura**. |
| `type`, `key` | Escribe texto o pulsa teclas y combinaciones (`enter`, `ctrl+c`, `alt+tab`, `win+r`…). |
| `cursor_position`, `list_apps`, `wait` | Posición del ratón, aplicaciones abiertas y espera. |
| `accessibility_tree` | Árbol de UI Automation de una app por PID: tipo, nombre accesible, AutomationId, rectángulo (ya en coordenadas de la captura), estado y patrones. No lee lo escrito en los campos. |

Flujo recomendado: `list_apps` → `accessibility_tree` para localizar controles →
`screenshot` → `click`.

Mientras actúa, se muestra un marco naranja y un aviso «Un agente de IA está usando tu
ordenador» (`overlay.ps1`); no sale en las capturas.

## Requisitos

- Windows 10/11 con PowerShell 5.1 (viene de serie).
- Node.js 18 o superior.

## Instalación

```bash
cd mcp/pc-control
npm ci
npm run prueba      # handshake MCP + herramientas + captura, sin hacer clic en nada
```

Debe terminar en `PRUEBA OK`.

### En OpenCode

Añádelo a `~/.config/opencode/opencode.json` (o al `opencode.json` del proyecto), con la
ruta absoluta donde lo hayas dejado:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "pc-control": {
        "type": "local",
        "command": ["node", "C:/ruta/a/claude-code-skills/mcp/pc-control/server.mjs"]
      }
    }
  }
}
```

O desde la terminal: `opencode mcp add pc-control --global -- node C:/ruta/a/claude-code-skills/mcp/pc-control/server.mjs`.
Comprueba con `opencode mcp list` que sale `connected`.

### En Claude Code

```bash
claude mcp add pc-control -s user -- node C:/ruta/a/claude-code-skills/mcp/pc-control/server.mjs
```

Abre una sesión nueva y comprueba con `/mcp` que está conectado.

## Backends de ratón y teclado

| Backend | Cuándo se usa | Notas |
|---|---|---|
| `powershell` | Siempre que no haya otro. | `entrada.ps1`: un proceso PowerShell persistente con Win32 `SendInput`. Sin binarios ni dependencias. |
| `nativo` | Si está instalada la app de escritorio de Claude (Microsoft Store). | Usa su módulo nativo de entrada, algo más rápido. No se incluye en este repo (no es redistribuible): se carga de la instalación de la app. |

Variables de entorno:
- `PC_CONTROL_BACKEND=auto|nativo|powershell` (por defecto `auto`: nativo si existe, si no PowerShell).
- `PC_CONTROL_NATIVO=<ruta al .node>` si el módulo nativo está en otra ruta.

En OpenCode se pasan con `"environment": { "PC_CONTROL_BACKEND": "powershell" }` dentro del
servidor; en Claude Code, con `claude mcp add pc-control -s user -e PC_CONTROL_BACKEND=powershell -- node …`.

## Personalización

- `server.mjs`: herramientas, descripciones, parámetros, límites y valores por defecto.
- `entrada.ps1`: nombres de teclas y cómo se envían ratón y teclado.
- `uia.ps1`: profundidad, número máximo de nodos y metadatos del árbol de accesibilidad.
- `captura.ps1`: captura y tamaño máximo de imagen.
- `overlay.ps1`: aviso visual mientras se controla el PC.

Después de cambiar el servidor, abre una sesión nueva del agente para que lo recargue.

## Seguridad

El agente puede hacer en tu PC todo lo que harías tú con ratón y teclado. Úsalo en una
máquina tuya, vigila lo que hace y no lo dejes solo con sesiones abiertas de banca, correo
o administración.

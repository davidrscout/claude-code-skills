// Prueba de humo de pc-control sin tocar nada: handshake MCP, lista de herramientas,
// posición del ratón, "mover" al mismo sitio en que está, lista de apps y una captura.
// Uso: node prueba.mjs   (con PC_CONTROL_BACKEND=powershell para forzar el backend sin binarios)
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const client = new Client({ name: "pc-control-prueba", version: "1.0.0" });
const transport = new StdioClientTransport({ command: process.execPath, args: [join(here, "server.mjs")], env: { ...process.env } });
const texto = (r) => r.content.filter((c) => c.type === "text").map((c) => c.text).join(" ");
try {
  await client.connect(transport);
  const { tools } = await client.listTools();
  console.log("herramientas:", tools.map((t) => t.name).join(", "));
  const pos = texto(await client.callTool({ name: "cursor_position", arguments: {} }));
  console.log("cursor_position:", pos);
  const [x, y] = pos.replace(/[()\s]/g, "").split(",").map(Number);
  console.log("move (mismo sitio):", texto(await client.callTool({ name: "move", arguments: { x, y } })));
  const apps = texto(await client.callTool({ name: "list_apps", arguments: {} }));
  console.log("list_apps:", apps.split("\n").length - 1, "apps;", apps.split("\n")[0]);
  const cap = await client.callTool({ name: "screenshot", arguments: { max_width: 800 } });
  console.log("screenshot:", texto(cap), "| imagen base64:", (cap.content.find((c) => c.type === "image")?.data.length ?? 0), "caracteres");
  console.log("PRUEBA OK");
} catch (e) {
  console.error("PRUEBA FALLIDA:", e.message);
  process.exitCode = 1;
} finally {
  await client.close().catch(() => {});
}

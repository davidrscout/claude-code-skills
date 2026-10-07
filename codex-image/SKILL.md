---
name: codex-image
description: >-
  Genera o edita imágenes GRATIS desde Claude Code usando la app OpenAI Codex (Microsoft Store) y una suscripción ChatGPT de pago, sin API key y sin coste por imagen. Solo Windows. Úsala SOLO cuando el usuario invoque /codex-image o pida explícitamente generar la imagen con Codex/ChatGPT; nunca por iniciativa propia.
---

# codex-image — generación de imágenes gratis vía Codex CLI

Genera imágenes con la herramienta interna `image_gen` de la app **OpenAI Codex**
(Microsoft Store), usando el login de una suscripción **ChatGPT de pago**.
**Sin API key y sin coste por imagen.** ~30–60 s cada una.

## Requisitos

- Windows 10/11.
- App **OpenAI Codex** instalada desde la Microsoft Store.
- `codex login` hecho con una cuenta ChatGPT de pago (Plus o superior).

## Cuándo usarla

- Se pide una imagen/ilustración/gráfico/mockup/icono/logo nuevos, o **editar** una existente.
- **NO** usar para vídeo ni audio, ni cuando se pida explícitamente otro modelo o proveedor.

## Cómo invocarla

Ejecuta el motor y luego **lee el PNG** con `Read`:

```
powershell -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\.claude\skills\codex-image\gen-image.ps1" -Prompt "<descripción detallada>" -Out "C:\ruta\salida.png" [-Size "1024x1024"] [-Ref "C:\ref1.png","C:\ref2.png"]
```

- stdout termina en `RESULT_OK <ruta> <bytes>` o `RESULT_FAIL <motivo>`.
- Tras `RESULT_OK`, usa **Read** sobre `<ruta>` para ver la imagen.
- Para **EDITAR**: pasa la imagen base con `-Ref` y describe el cambio en `-Prompt`.
- Tamaños: cuadrado `1024x1024`, horizontal `1536x1024`, vertical `1024x1536`.

### Parámetros

| Parámetro | Obligatorio | Descripción |
|---|---|---|
| `-Prompt` | sí | Descripción de la imagen o del cambio a aplicar. |
| `-Out` | sí | Ruta absoluta del PNG de salida. |
| `-Ref` | no | Una o varias imágenes de referencia/base (para editar). |
| `-Size` | no | Pista de lienzo: `1024x1024`, `1536x1024`, `1024x1536`. |
| `-Model` | no | Modelo de Codex (por defecto `gpt-5.6-luna`). |
| `-Reasoning` | no | `low` (por defecto), `medium`, `high`. |

## Notas y límites

- El modelo son las **imágenes de OpenAI (gpt-image)**: look propio, distinto al de otros generadores.
- Consume **cuota de la suscripción ChatGPT**; los lotes grandes pueden topar límites.
- **Gotchas ya resueltos en el motor** (no los reintroduzcas al editarlo):
  1. El prompt va por **stdin**, no como argumento posicional: el flag `-i` es variadic
     y se lo comería, y además stdin aporta el EOF que `codex exec` necesita para no colgarse.
  2. Nada de `--approve-for-me`: en un Windows con `sandbox="elevated"` pide UAC y se cuelga.
     Se usa `--dangerously-bypass-approvals-and-sandbox` (asume máquina propia y de confianza).

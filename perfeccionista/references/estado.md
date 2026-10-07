# Estado persistente y formatos

El estado en disco es lo que permite que el bucle sobreviva a compactaciones de
contexto, cierres de sesión y días distintos. Regla de oro: **si no está en disco,
no ha pasado**. Cada fase escribe su resultado antes de pasar a la siguiente.
Meta-regla de toda la skill: ante dos lecturas de cualquier regla, vale la que hace
más difícil inflar la nota.

Ubicación: `_perfeccionista\<slug>\` en la raíz LOCAL del proyecto (nunca solo en
un VPS remoto). Si no hay carpeta de proyecto clara, la raíz del proyecto pasa a
ser `~/Desktop/<slug>\` (con el entregable dentro), y el estado queda
exactamente en `~/Desktop/<slug>\_perfeccionista\<slug>\`. Nunca un
`_perfeccionista\` suelto en `la carpeta del usuario`. En ese fallback, el contrato fija
como raíz del entregable una subcarpeta (p. ej. `Desktop\<slug>\src\`), nunca
`Desktop\<slug>\` entera — los jueces no deben recibir una raíz que contenga
`_perfeccionista\`. El slug sale del encargo: corto,
kebab-case sin acentos (`api-facturas-cliente`, `web-tienda`).

Contenido del directorio de estado:

| Elemento | Qué es |
|---|---|
| `contrato.md`, `rubrica.md`, `historial.md`, `siguiente_prompt.md` | Los cuatro ficheros de fase (abajo). |
| `auditoria-rubrica-prompt.md` / `-respuesta.md` | Rastro obligatorio de la auditoría de la rúbrica (Fase 1). Sin ellos, la rúbrica NO está congelada. |
| `evidencia\vuelta-N\` | Evidencia de la vuelta N, con subcarpeta `jueces\`. |
| `evidencia\vuelta-N-confirmacion\` | Evidencia propia de la pasada de confirmación tras el 10.000 de la vuelta N (re-verificación + su `jueces\`). |
| `evidencia_actual\` | Copia neutra que ven los jueces (sin número de vuelta), sobrescrita en cada pasada. |
| `snapshots\` | Copias del entregable pre-jurado (si no hay git). Fuera de la evidencia: los jueces no la reciben. |

**Contador N:** arranca a 0 al crear el estado y se incrementa al entrar en Fase 2
— la primera vuelta es N=1. N no vive en tu memoria: es el mayor `vuelta-N`
existente en `evidencia\`.

## Reglas de escritura (Windows)

- Los ficheros de estado se escriben SIEMPRE con las herramientas Write/Edit
  (UTF-8), nunca con `Out-File` ni redirección `>` de PowerShell 5.1 (escriben
  UTF-16 con BOM y rompen a quien los lea). Para capturar salida de comandos en
  `evidencia\`: vuelca la salida capturada con Write, o si no hay más remedio,
  `comando | Out-File -Encoding utf8`.
- **Secretos:** antes de guardar evidencia, sustituye tokens, contraseñas y cookies
  por `[REDACTED]` — el juez necesita el código de estado y el resultado, no la
  credencial. Si el proyecto es un repo git, añade `_perfeccionista/` a `.gitignore`
  en la primera vuelta.

## contrato.md

```markdown
# Contrato — <título del encargo>
Fecha: <YYYY-MM-DD> · Estado: aprobado por el usuario <fecha> | headless (sin aprobar)

## Objetivo
<Qué se construye y qué problema resuelve, en 2-4 frases.>

## Qué es un 10 para el usuario
<Sus palabras de la entrevista, casi literales. Esto ancla la rúbrica.>

## Entregable
<Ruta(s) ABSOLUTA(s) del entregable y comando para arrancarlo/probarlo. Es la raíz
que reciben TODOS los jueces y lo que verifica la reanudación.>

## Alcance
- <punto entregable 1>
## No-alcance
- <explícitamente fuera>

## Entorno y restricciones
<Stack, dónde corre, credenciales, límites de dinero/producción, idioma.>

## Casos límite acordados
- <entrada rara → comportamiento esperado>

## Suposiciones
<Todo lo no preguntado/no respondido. En headless, cada decisión que tomaste tú
(las más exigentes defendibles) y cada punto `NO verificado en real — bloqueado
por <X>`.>
```

Con el OK de el usuario el contrato queda CONGELADO: solo él lo modifica, y cada cambio
se apunta con fecha en la sección "Aclaraciones (contrato y rúbrica)" de
`rubrica.md`.

## rubrica.md

```markdown
# Rúbrica — congelada <YYYY-MM-DD> · auditoría en auditoria-rubrica-respuesta.md
| # | Dimensión | Peso | Un 10 significa | Descuentos típicos |
|---|---|---|---|---|
| 1 | ... | 25 | ... | −1.000 si ... |
Total pesos: 100

## Dimensiones de plantilla eliminadas/fusionadas
<Justificación escrita de cada una; el auditor y la confirmación lo revisan.>

## Aclaraciones (contrato y rúbrica)
<Solo se añade si el usuario resolvió una ambigüedad a mitad de bucle (con fecha), o en
headless con la marca HEADLESS y la lectura más estricta, citando lo que la
justifica: los dos descuentos contradictorios (si nace de la salvaguarda de
jurado.md) o el criterio literal que resultó imposible (si nace de la Fase 1). La
tabla de arriba NUNCA se edita.>
```

## historial.md

**La primera línea es siempre la línea canónica de estado** (es la que lee la
reanudación; el Cierre la ACTUALIZA, no añade otra al final):
`ESTADO: en-curso | pendiente-confirmacion | CERRADO <fecha> — 10.000 confirmado`.

Después, una fila por pasada de jurado. `Tipo ∈ {normal, confirmación}` — el modo
del jurado (workflow | subagentes | claude-p | degradado-secuencial | mixto (juez X
degradado)) NO va en Tipo: va en la línea "Modo jurado" del detalle. Toda nota
—final y por dimensión— se escribe en disco con 3 decimales; solo el informe-latido
a el usuario puede abreviar. El Δ lleva su signo real (también negativo) y siempre se
calcula contra la pasada inmediatamente anterior, sea del tipo que sea; la fila de
confirmación usa el siguiente número de Pasada.

```markdown
ESTADO: en-curso
# Historial — <slug>
| Pasada | Vuelta | Tipo | Fecha | Nota | Δ | Peor dimensión | Resumen |
|---|---|---|---|---|---|---|---|
| 1 | 1 | normal | 2026-08-25 | 7.412 | — | Robustez 5.800 | Sin manejo de errores de red |
| 2 | 2 | normal | 2026-08-25 | 8.907 | +1.495 | Tests 8.100 | Faltan 3 casos límite. PIVOTE: Robustez — reescrito cliente HTTP |
| 3 | 3 | normal | 2026-08-26 | 10.000 | +1.093 | — | — |
| 4 | 3 | confirmación | 2026-08-26 | 10.000 | +0.000 | — | Cierre |

## Pasada 2 — detalle
Notas: Funcionalidad 9.500×25 · Tests 8.100×20 · Robustez 9.000×15 · ...
Suma exacta: 890.760 milésimas ponderadas → truncada: 8.907
Modo jurado: workflow
Relanzamientos: <ninguno | juez X, motivo, prueba, salida descartada en jueces\...>
PARA EL 10 consolidado (incluye FUERA DE DIMENSIÓN asignados):
- [Tests] caso límite IBAN con espacios internos sin cubrir
- [Docs] falta ejemplo de uso en README
```

## siguiente_prompt.md

El autoprompt de la vuelta siguiente. Redáctalo como un encargo completo para un
agente que no ha visto nada: contexto mínimo, lista concreta de cambios, y qué
verificación debe pasar. Si hay un bloqueo pendiente de el usuario, va en la primera
línea. Se sobrescribe cada vuelta (el historial guarda el resumen de las
anteriores).

## evidencia\vuelta-N\ (y vuelta-N-confirmacion\)

- **Cabecera obligatoria** en cada fichero de evidencia (primeras líneas):
  `# cmd: <comando exacto> · cwd: <directorio> · fecha: <YYYY-MM-DD HH:MM> · exit: <código>`.
  Evidencia sin cabecera reproducible = evidencia inexistente para el jurado. La
  fecha debe cuadrar con el mtime real del fichero — los jueces lo comprueban.
- **Solo salidas crudas** (logs, capturas, outputs de comando) — prohibida la prosa
  valorativa del implementador; única excepción: una línea factual de anotación de
  sandbox/dry-run. Los jueces tienen orden de ignorar texto valorativo.
- **Se genera entera en su pasada**: prohibido copiar o enlazar de vueltas
  anteriores; lo que no cambió se re-ejecuta (la cabecera y el mtime lo
  demuestran).
- Nombres autodescriptivos: `tests_salida.txt`, `lint.txt`, `web_movil_390px.png`,
  `curl_webhook_200.txt`, `servicio_revive_tras_kill.txt`,
  `verificacion_intento_K.txt` (intentos fallidos de Fase 3),
  `limitaciones.txt` (qué no se pudo verificar y por qué).
- Subcarpeta `jueces\`: prompt y respuesta cruda de cada juez
  (`juez-<dimension-kebab>-prompt.md` / `-respuesta.md`), más descartados de
  relanzamientos (`-descartado-K`).
- La pasada de confirmación de un 10.000 de la vuelta N escribe SOLO en
  `evidencia\vuelta-N-confirmacion\` (su re-verificación de Fase 3 y su `jueces\`);
  la carpeta `vuelta-N\` del 10.000 no se toca.

### Copia neutra para el jurado

Antes de cada pasada, genera el **manifiesto** (nombre, tamaño, hash SHA-256 y
mtime de cada fichero) **recorriendo la carpeta ORIGEN** (`evidencia\vuelta-N\` o
`...-confirmacion\`) con su cabecera de comando, y DESPUÉS copia carpeta +
manifiesto a `evidencia_actual\` (sobrescribiéndola), dejando `manifiesto.txt` en
ambas. El orden importa: un manifiesto generado sobre la copia coincidiría con ella
aunque estuviera curada. Los jueces reciben solo `evidencia_actual\` y contrastan
contenido contra manifiesto: un fichero listado y ausente (omitir
`limitaciones.txt` o los intentos fallidos) invalida la pasada. En confirmación,
copia además los veredictos y la tabla de agregación de la pasada del 10.000 a
`evidencia_actual\veredictos-a-auditar\` (con los relanzamientos y descartados) —
la tabla SIN números de pasada/vuelta, sin fechas y sin Δ: solo dimensión × nota ×
peso, suma en milésimas y nota truncada.

## snapshots\

Copia del entregable antes de cada pasada de jurado si no hay git
(`snapshots\pre-pasada-P\`); con git, commit + tag `perfeccionista/snap-<YYYYMMDD-HHMM>`
(sin número de vuelta en el nombre). Permite revertir si una mejora sale peor. La
pasada de confirmación no necesita snapshot nuevo: el entregable no ha cambiado.

## Informe por vuelta a el usuario (formato canónico)

Tras cada pasada de jurado, UN bloque corto en la conversación (el detalle está en
disco):

```
VUELTA N — NOTA: X.XXX / 10.000 (Δ ±X.XXX)
Peor dimensión: <nombre> X.XXX — <motivo en una frase>
Siguiente: <la mejora principal de la próxima vuelta en una frase>
```

Para la confirmación, el encabezado es `VUELTA N (confirmación) — NOTA: ...`. Si la
pasada fue degradada o mixta, se dice en esa misma línea. Sin párrafos de contexto,
sin celebrar subidas: el informe es un latido, no un ensayo. El cierre (10.000
confirmado) sí lleva informe completo.

## Protocolo de reanudación

Al invocarte con `_perfeccionista\<slug>\` existente (o si el usuario dice "continúa"):

1. Lee `contrato.md` y compara su objetivo con el encargo actual.
   - Coincide y `ESTADO: CERRADO` → no hay nada que retomar: trabajo nuevo sobre
     ese entregable = encargo nuevo (en interactivo pregunta a el usuario; en headless
     crea `<slug>-YYYYMMDD`). El 10.000 antiguo jamás se hereda.
   - No coincide → es otro encargo: slug nuevo con sufijo (`-2` o fecha).
   - Coincide y no cerrado → reanuda (pasos siguientes).
2. Lee la primera línea de `historial.md`:
   - `ESTADO: pendiente-confirmacion` → verifica con hashes/mtimes que entregable
     y evidencia de la pasada del 10.000 no cambiaron desde entonces. Intactos →
     lanza la pasada de confirmación. Cambiaron → el 10.000 queda invalidado
     (regístralo) y vuelve a Fase 3 con pasada normal. Esta es la ÚNICA excepción
     a "ninguna nota del historial es vigente al reanudar".
   - `ESTADO: en-curso` → lee la última pasada y `siguiente_prompt.md` (¿trabajo
     pendiente?).
   - Si historial o siguiente_prompt no existen, la interrupción fue en la vuelta
     1: deduce la fase por el último fichero escrito (¿solo contrato.md? → Fase 1;
     ¿rubrica.md + auditoría? → Fase 2; ¿evidencia\vuelta-1\? → Fase 3/4) y retoma
     ahí.
   - Si hay veredictos en `jueces\` de una pasada a medias, valen: relanza solo
     los jueces que falten.
3. Verifica el estado real del entregable en la ruta del contrato (¿la última
   mejora llegó a aplicarse? contrasta con la evidencia) — no te fíes de la
   memoria.
4. Retoma en la fase que toque. La entrevista y la rúbrica NO se repiten, y salvo
   la excepción del punto 2, ninguna nota del historial es vigente: toda
   reanudación pasa por Fase 3 + jurado antes de reportar nota alguna.

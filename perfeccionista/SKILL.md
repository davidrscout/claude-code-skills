---
name: perfeccionista
description: >-
  Loop de perfeccionamiento hasta la nota perfecta: entrevista a fondo al usuario, congela un contrato y una rúbrica, implementa, verifica todo en real, un jurado adversarial e independiente puntúa de 0.000 a 10.000 (3 decimales) y el ciclo se repite con prompts de mejora autogenerados hasta alcanzar y confirmar el 10.000. Úsala SOLO cuando el usuario invoque /perfeccionista o pida explícitamente este bucle con nota ("pásale el perfeccionista", "loop hasta el 10"). Nunca por iniciativa propia: pedir que algo quede bien o probarlo todo no basta para activarla.
---

# Perfeccionista — loop de mejora hasta el 10.000

Recibes un encargo (código, integración, web, bot, documento… cualquier entregable).
Tu trabajo no es "hacerlo y entregarlo": es llevarlo en bucle —implementar, verificar,
puntuar, mejorar— hasta que un jurado independiente le dé un **10.000 confirmado**.

## Principio rector: la nota solo vale si es verdad

Todo el sistema se sostiene sobre una única cosa: que la nota sea honesta. Si la nota
se infla para terminar antes, la skill entera pierde su sentido — el usuario pidió
explícitamente que el bucle NO acabe hasta el 10 real. De ahí las reglas duras:

- **Evidencia sobre afirmación.** Nada cuenta como hecho si no se ha ejecutado,
  medido o visto, con rastro reproducible en disco. "Debería funcionar" puntúa como
  "no funciona".
- **Contrato y rúbrica se congelan antes de implementar.** El listón no se mueve:
  ni la rúbrica se ablanda ni el alcance del contrato se encoge para abaratar el 10.
  Solo el usuario puede cambiarlos.
- **Puntúan jueces que no han escrito el código**, ciegos al historial y con
  mandato adversarial. Sus prompts y respuestas crudas quedan guardados para
  auditoría.
- **La nota se trunca, no se redondea.** Una media de 9.9996 es 9.999, no 10.000.
- **El primer 10.000 no cierra el bucle.** Se confirma con una segunda pasada de
  jurado fresco. Solo dos 10.000 seguidos terminan el trabajo, y ninguno de los dos
  puede venir de un jurado en modo degradado o mixto (ver Fase 4).
- **Meta-regla de desempate:** ante dos lecturas razonables de cualquier regla de
  esta skill (este fichero o sus referencias), la correcta es siempre la que hace
  más difícil inflar la nota.

## Estado persistente (lo primero de todo)

El bucle puede durar muchas vueltas y sobrevivir a compactaciones de contexto o a
sesiones nuevas. Regla de oro: **si no está en disco, no ha pasado**. Cada fase
escribe su resultado antes de pasar a la siguiente.

Dónde: `_perfeccionista\<slug>\` en la raíz LOCAL del proyecto (la máquina donde
corres tú, aunque el entregable viva en un VPS — el estado nunca vive solo en el
servidor). Si el encargo no tiene carpeta de proyecto clara, la raíz del proyecto
pasa a ser `~/Desktop/<slug>\` (entregable dentro, estado en
`...\<slug>\_perfeccionista\<slug>\`); nunca un `_perfeccionista\` suelto en
`la carpeta del usuario`. Confirma la ubicación en el resumen del contrato (Fase 0).

| Fichero | Contenido |
|---|---|
| `contrato.md` | El encargo destilado: objetivo, alcance, criterios de éxito, ruta del entregable, suposiciones. Congelado con el OK de el usuario. |
| `rubrica.md` | Dimensiones, pesos y qué es un 10 en cada una. Congelada tras auditoría. |
| `historial.md` | Línea `ESTADO:` + una fila por pasada de jurado, con notas de 3 decimales. |
| `siguiente_prompt.md` | El autoprompt de mejora para la vuelta siguiente. |
| `evidencia\vuelta-N\` | Salidas crudas de verificación + prompts/respuestas de jueces de cada vuelta. |

**Definición de vuelta:** una vuelta es un ciclo completo Fase 2→Fase 5. El
contador N arranca a 0 al crear el estado y se incrementa al entrar en Fase 2 (la
primera vuelta es N=1); en ese momento se crea `evidencia\vuelta-N\`. N no vive en
tu memoria: es el mayor `vuelta-N` existente en `evidencia\`. La pasada de
confirmación del cierre no incrementa N: escribe en
`evidencia\vuelta-N-confirmacion\` y cuenta como una pasada más del historial,
marcada como `confirmación`.

El formato exacto de cada fichero, las reglas de escritura (encoding, secretos,
cabeceras de evidencia) y el protocolo de reanudación están en
`references/estado.md` — léelo al crear el estado por primera vez y al reanudar.

Si al invocarte ya existe `_perfeccionista\` (o el usuario dice "continúa"), sigue el
protocolo de reanudación de `references/estado.md`: compara el contrato existente
con el encargo actual, respeta la línea `ESTADO:` (un encargo cerrado jamás se
reabre ni hereda su 10.000), y retoma sin repetir entrevista ni rúbrica. Ninguna
nota del historial es vigente al reanudar: antes de reportar nota alguna se pasa
por Fase 3 + jurado.

## Fase 0 — Interrogatorio

No empieces a trabajar con un encargo ambiguo: cada ambigüedad que no preguntes ahora
se convertirá en una vuelta extra del bucle (o en un 10 falso sobre un contrato pobre).

1. **Investiga antes de preguntar.** Lee el repo/carpeta, la memoria y lo que haya
   del proyecto. Preguntar algo que podías averiguar tú queda mal y gasta una ronda.
2. **Pregunta en rondas.** Con AskUserQuestion si existe en la sesión (máx. 4
   preguntas por llamada; el usuario siempre puede responder texto libre). Si la
   herramienta no existe pero el usuario está disponible, haz las mismas preguntas como
   mensaje normal —numeradas, con 2-3 opciones sugeridas por pregunta— y TERMINA tu
   turno esperando su respuesta: la ausencia de la herramienta nunca es motivo para
   saltar al modo headless. Cubre como mínimo:
   - Objetivo real y para quién es (¿qué problema resuelve?).
   - **Qué es un 10 para el usuario en ESTE encargo** — literal, pídele que lo describa.
     Esto ancla la rúbrica.
   - Alcance y no-alcance explícitos.
   - Stack, entorno, dónde vivirá el entregable, integraciones, credenciales.
   - Casos límite y qué debe pasar cuando algo falla.
   - Restricciones: dinero, servicios de pago, VPS, plazos, idioma.
3. **Criterio de parada de la entrevista:** si dos implementaciones razonables del
   encargo serían distintas, aún falta una pregunta. Cuando ya no queden ambigüedades
   materiales, para — no preguntes por preguntar.
4. **Checkpoint del contrato.** Escribe `contrato.md` y enséñale a el usuario un resumen
   corto (incluida la ubicación del estado y del entregable). TERMINA TU TURNO y
   espera su OK explícito; si responde con cambios, actualiza y vuelve a enseñar —
   el OK es sobre la versión final. Avísale en ese mismo mensaje de que el bucle
   ejecutará comandos repetidamente y conviene aprobar permisos ahora (allowlist
   del proyecto) para que no se pause a mitad. Con su OK, **el contrato queda
   CONGELADO** igual que la rúbrica: solo el usuario lo modifica, y cada cambio se
   registra con fecha en "Aclaraciones". Este es el único checkpoint obligatorio:
   después, el bucle es autónomo.

**Modo headless** — SOLO si de verdad no hay usuario (corres como subagente, en CI,
o el usuario dijo que no estará): deriva del encargo las respuestas **más exigentes
defendibles** — ante dos lecturas razonables, la que pide más calidad o más alcance,
nunca la que abarata el 10; una suposición headless jamás rebaja el estándar
profesional del tipo de entregable. Apúntalas TODAS en "Suposiciones" del contrato
y sigue sin bloquearte. En headless, además, trabaja SIEMPRE de forma síncrona:
lanzar algo en background y terminar tu turno "a la espera de notificaciones" mata
el bucle, porque como subagente nadie te despierta — espera los resultados dentro
del turno o ejecuta el mecanismo síncrono equivalente.

## Fase 1 — Rúbrica congelada

Antes de escribir una línea del entregable, escribe `rubrica.md`:

- 6–8 dimensiones con pesos que suman 100. Parte de la plantilla del tipo de
  entregable en `references/rubrica.md` (léelo ahora) y ajústala al contrato. Toda
  dimensión de la plantilla que elimines lleva justificación escrita en `rubrica.md`.
- Para cada dimensión, define **qué es un 10 en términos verificables** ("todos los
  tests pasan y cubren los casos límite del contrato", no "buen testing").
- **Auditoría independiente antes de congelar:** un agente con contexto limpio
  audita la rúbrica con la plantilla VERBATIM de `references/rubrica.md` (sección
  "Auditoría de la rúbrica"), usando la misma cadena de mecanismos del jurado. Su
  prompt y respuesta se guardan como `auditoria-rubrica-prompt.md` y
  `-respuesta.md` junto al contrato: sin esos ficheros la rúbrica NO está
  congelada. Veredicto "no-apta" → aplica las objeciones y reaudita. Existe porque
  quien escribe la rúbrica es quien será puntuado con ella.
- Congelada significa congelada. Solo se toca con aprobación de el usuario; si un
  criterio resulta contradictorio o imposible, consúltale (en headless: aplica la
  lectura más estricta y anótala en "Aclaraciones" como `HEADLESS`). Nunca se
  elimina ni ablanda en silencio.

## Fase 2 — Implementación

Incrementa N, crea `evidencia\vuelta-N\` y ejecuta: el encargo entero (vuelta 1) o
`siguiente_prompt.md` (vueltas posteriores). Sigue las convenciones del proyecto.
No marques nada como hecho sin haberlo comprobado.

**Equipo de especialistas (opcional, recomendado en encargos multi-área).** La
implementación no tiene por qué hacerse en un solo contexto. Si el entregable toca
varias disciplinas (frontend + backend + BD + infra…), delega en la skill
`super-equipo`: monta un equipo de especialistas por área, cada uno en contexto
limpio, coordinados por contratos de interfaz y con revisión adversarial. Es solo el
brazo de implementación — la verificación (Fase 3) y el jurado (Fase 4) siguen siendo
tuyos e independientes: el equipo construye, el jurado externo puntúa; nunca se
autopuntúa ni relaja la rúbrica. Escala el equipo al encargo (no montes una empresa
para un cambio de una línea).

## Fase 3 — Verificación total

Nada llega al jurado sin estar verde. Verifica TODO en real, según el tipo de
entregable (guía completa por tipo en `references/rubrica.md`):

- **Código**: ejecuta los tests (escríbelos si no existen), lint, build, y ejecuta
  el programa de verdad con casos reales y casos límite del contrato.
- **Web/UI**: navega los flujos del contrato con Playwright (skill webapp-testing
  si está; si no, instala Playwright tú mismo y escribe el script; último recurso:
  peticiones HTTP + inspección del HTML, anotando en la evidencia qué quedó sin
  verificar visualmente).
- **Integraciones/APIs**: llamadas reales end-to-end. Si tocar producción cuesta
  dinero o es irreversible, usa sandbox/dry-run y anótalo en la evidencia (una
  línea factual); si el contrato no preveía sandbox, es una ambigüedad: consúltala
  a el usuario (en headless: lectura más estricta + nota en "Aclaraciones").
- **Documentos**: renderiza el formato final y revísalo renderizado, no en fuente.

Cada verificación se guarda en `evidencia\vuelta-N\` como salida cruda con su
cabecera de reproducción (comando exacto, directorio, fecha-hora, exit code — ver
`references/estado.md`); evidencia sin cabecera no existe para el jurado. La
evidencia de la vuelta N se genera ENTERA en la vuelta N: nada se copia de vueltas
anteriores; lo que no cambió se re-ejecuta igualmente.

Si algo falla, arréglalo y repite. **Puntuar un estado en rojo está prohibido.**
Pero la Fase 3 también puede atascarse: si llevas 3 intentos arregla-verifica
fallando en lo mismo, aplica el pivote material de la Fase 5 sin esperar al jurado,
guarda cada intento en `evidencia\vuelta-N\verificacion_intento_K.txt` (así el
contador sobrevive a compactaciones) y emite a el usuario una línea de latido:
`VERIFICACIÓN vuelta N: intento K fallido — <motivo>`.

Antes de pasar al jurado, congela un snapshot del entregable (commit + tag
`perfeccionista/snap-<YYYYMMDD-HHMM>` si hay git — sin número de vuelta en el
nombre, los jueces podrían verlo —; si no, copia en
`_perfeccionista\<slug>\snapshots\`, fuera de la evidencia): sin snapshot no hay
camino de vuelta si una mejora futura sale peor.

## Fase 4 — Jurado independiente

La nota la pone un panel de jueces que no han implementado nada. El protocolo
completo (prompts verbatim, ceguera, relanzamientos, agregación exacta) está en
`references/jurado.md` — léelo antes de cada pasada; no es opcional, es el fichero
que impide que el bucle se autoengañe.

Resumen (el detalle de jurado.md manda):

- Un juez por dimensión. Mecanismo, por capacidad real y en este orden: (1) la
  herramienta Workflow — esta skill te instruye explícitamente a usarla, lo que
  constituye el opt-in; (2) la herramienta de subagentes que exista en la sesión
  (Agent, Task o equivalente), varias llamadas en el mismo mensaje; (3) procesos
  nuevos con `claude -p "<prompt de juez>"` desde la terminal; (4) modo
  degradado-secuencial, solo si guardaste en evidencia el error literal de los
  mecanismos anteriores. **Una pasada con CUALQUIER juez degradado cuenta entera
  como degradada y nunca produce el 10.000 de cierre ni la confirmación**; si no
  hay forma de tener jueces reales, es un bloqueo de infraestructura: avisa a
  el usuario.
- Cada juez recibe contrato, su dimensión literal de la rúbrica, la raíz completa
  del entregable fijada en el contrato (la misma para todos, con rutas absolutas)
  y la copia neutra de la evidencia. No recibe historial, número de vuelta, ni
  presión por el resultado.
- Los prompts se construyen VERBATIM desde la plantilla de jurado.md y se guardan
  junto a cada respuesta cruda en `evidencia\vuelta-N\jueces\`. Sin esos ficheros,
  la pasada no vale.
- Nota final = agregación entera en milésimas (comando en jurado.md), truncada a 3
  decimales. Regístrala en `historial.md` con la tabla completa nota×peso y
  repórtala a el usuario con el signo real del delta:

```
VUELTA 4 — NOTA: 9.371 / 10.000 (Δ +0.482)
Peor dimensión: Robustez 8.200 — no valida entrada UTF-8 con BOM
Siguiente: arreglar BOM + reintentos en el webhook
```

## Fase 5 — Autoprompt y siguiente vuelta

Si la nota < 10.000:

1. Junta todas las listas de "PARA EL 10" de los jueces, más todo hallazgo FUERA
   DE DIMENSIÓN que reportaran (descartar uno en silencio invalida la vuelta).
2. Conviértelas en un prompt de mejora concreto y accionable — escríbelo en
   `siguiente_prompt.md`. Ese prompt es literalmente el encargo de la siguiente
   vuelta: redáctalo como se lo darías a otro agente que no ha visto nada.
3. Añade mejoras que tú veas más allá de lo que digan los jueces (simplificación,
   rendimiento, docs) — los jueces acotan el mínimo, no el máximo.
4. Vuelve a la Fase 2 con ese prompt.

**Anti-atasco.** Mira `historial.md` en cada vuelta:

- Si en 2 vueltas seguidas la nota sube ≤ 0.050 **o baja**, lo que haces no
  funciona: pivota de verdad — reescribe el componente desde cero, cambia de
  arquitectura o librería, ataca el problema por otro flanco. El pivote cambia el
  CÓMO, nunca el QUÉ: contrato, rúbrica y alcance son intocables; si crees que el
  problema es una suposición o decisión del contrato, eso es de el usuario — consúltale
  (en headless: lectura más exigente + nota en "Aclaraciones").
- Con nota ≥ 9.900 el umbral engaña (solo quedan centésimas): ahí el atasco se mide
  por ítems de "PARA EL 10" que se repiten dos vueltas sin resolverse, y el pivote
  es quirúrgico sobre esos ítems — nunca una reescritura total de algo casi
  perfecto.
- Cada pivote se registra en el historial (`PIVOTE: <dimensión> — <qué cambió>`) y
  resetea el contador; si tras un pivote vuelve el atasco, el siguiente ataca una
  dimensión o enfoque DISTINTO de los ya pivotados.
- Si la nota bajó, diagnostica comparando los descuentos de ambas pasadas: si es
  regresión real (no criterio distinto del juez), puedes revertir al snapshot de la
  mejor vuelta y reintentar la mejora de otro modo.

**Cuándo (y solo cuándo) interrumpir a el usuario:** un bloqueo que dependa de él —
credenciales, un pago, una decisión de negocio, un permiso de herramienta que
congela el bucle, o un criterio contradictorio de rúbrica/contrato. Preséntale la
nota actual, el historial y la pregunta exacta; nunca "¿sigo?" — eso ya lo contestó
al invocar la skill. Mientras esperas su respuesta, sigue mejorando las dimensiones
no bloqueadas y deja el bloqueo anotado al principio de `siguiente_prompt.md`. En
headless los bloqueos externos no paran el bucle: verifica contra sandbox/mock,
registra en "Suposiciones" el punto como `NO verificado en real — bloqueado por
<X>`, inclúyelo en la evidencia (los jueces descontarán lo que proceda) y ponlo en
cabeza del informe final.

## Cierre

Al obtener un 10.000 (de jurado no degradado ni mixto), actualiza la primera línea
del historial a `ESTADO: pendiente-confirmacion` y lanza la pasada de
confirmación: jurado completamente fresco con el esqueleto verbatim MÁS el "Anexo
de confirmación" de `references/jurado.md` (también verbatim) — re-ejecutar la
comprobación positiva de cada criterio, recalcular la aritmética y los
relanzamientos de la pasada del 10.000, y emitir `RUBRICA_BLANDA: sí/no` por
dimensión, con poder de invalidar el cierre. La confirmación re-ejecuta la
verificación de Fase 3 aunque no haya cambios y escribe TODO lo suyo (evidencia
nueva y jueces) en `evidencia\vuelta-N-confirmacion\` y en la copia neutra
`evidencia_actual\` — nunca en `evidencia\vuelta-N\` ni en el entregable.

- **Entre el 10.000 y su confirmación no se tocan ni el entregable ni
  `evidencia\vuelta-N\`** (la carpeta de la pasada que dio el 10.000): cualquier
  cambio ahí invalida el primer 10.000 y devuelve el bucle a la Fase 3. La
  confirmación escribe solo en su propia carpeta y en `evidencia_actual\`. Las
  "mejoras propias" de la Fase 5.3 solo aplican con nota < 10.000.
- **Si la confirmación da < 10.000, esa es la nota vigente:** se registra como
  pasada `confirmación` en el historial (mismo N, siguiente número de pasada, Δ
  contra la pasada anterior), sus "PARA EL 10" alimentan la Fase 5, el contador de
  dieces se reinicia y el bucle sigue (`ESTADO: en-curso`). Prohibido relanzar la
  confirmación sin cambios en el entregable — repetir jurado hasta que "salga" es
  jugar a la varianza, no confirmar.
- **Si algún juez dictamina `RUBRICA_BLANDA: sí`,** o un relanzamiento previo
  resulta injustificado, o la aritmética recalculada no cuadra: el 10.000 no
  computa; la confirmación invalidada se registra igualmente como fila (Tipo
  `confirmación`, motivo en Resumen); corrige lo que proceda (rúbrica endurecida
  con OK de el usuario — headless: endurécela y documenta en "Aclaraciones") y relanza
  pasada normal vía Fase 5 → Fase 2: vuelta nueva con N+1, la carpeta `vuelta-N`
  del 10.000 invalidado no se reescribe.
- **Si la propia confirmación sale degradada o mixta,** no computa por
  infraestructura, no por nota: no consume el intento, `ESTADO:` sigue
  `pendiente-confirmacion`, avisa a el usuario del bloqueo y repite la confirmación
  cuando haya jueces reales — sin exigir cambios en el entregable (eso no es jugar
  a la varianza).

Solo con dos 10.000 seguidos, cierra: ACTUALIZA la primera línea del historial a
`ESTADO: CERRADO <fecha> — 10.000 confirmado` (es la línea que lee la reanudación)
e informa a el usuario: nota confirmada, vueltas totales, tabla del historial, qué se
construyó, cómo se usa, dónde está la evidencia, y cualquier punto `NO verificado
en real` en cabeza. Deja `_perfeccionista\` intacto: es el registro de calidad del
encargo.

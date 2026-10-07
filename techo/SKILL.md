---
name: techo
description: >-
  Examina un proyecto (código, tienda, proceso, plan) y dictamina si está en un
  TECHO estructural (cada mejora es otro parche y la métrica no se mueve) o si
  el camino actual aún da de sí. Demuestra el techo con evidencia (fichero:línea,
  historial de parches, cifras medidas), intenta refutarlo con el mejor parche
  conservador, y solo si sobrevive propone caminos alternativos con coste
  honesto, prueba barata y convivencia con lo viejo. Si no hay techo lo dice y
  da las palancas que sí hacen crecer. Entrega un DICTAMEN detallado, no una
  lista de bugs. Úsala siempre que el usuario invoque /techo o pida
  "examina X y júzgalo", "busca otros caminos", "cómo sigo creciendo", "tiene
  techo", "cuello de botella", "llevo meses arreglando lo mismo", "¿sigo
  mejorando esto o cambio de enfoque?", "no solo fixear errores", "otra manera
  de hacerlo", "hasta dónde puede llegar", "dictamen", o cuando el
  mismo síntoma vuelve por tercera vez. NO es para cazar bugs (/code-review) ni
  para un bucle de calidad con nota (/perfeccionista)
---

# Techo — dictamen sobre dónde está el límite y cómo se rompe

Recibes un objeto a examinar: casi siempre un proyecto de código, a veces una
tienda, un proceso comercial, un plan. Tu trabajo NO es encontrar lo que está
roto. Es responder a una pregunta más cara: **¿este proyecto puede seguir
creciendo por el camino que lleva, o el camino en sí es el límite?** Y si el
camino es el límite, cuál es el otro camino, cuánto cuesta de verdad y cómo se
comprueba barato antes de apostar meses.

## Por qué existe (el caso de referencia, calibración)

El cerebro del chat de el proyecto de referencia (un SaaS con chat de IA) era un pipeline cerrado: clasificador de intención
→ el modelo extrae parámetros → SQL con filtros → si 0 resultados, relaja
filtros a ciegas → devuelve UN ganador con informe. Durante meses cada mejora
fue un parche DENTRO del pipeline (mapas estáticos, modos cosidos a mano,
listas de países, regex); cada uno arreglaba un síntoma y la calidad seguía
con techo. Una auditoría de 48 agentes encontró 37 bugs graves y ninguno era el
techo. El salto llegó al "abrir el modelo": dejar que el modelo decida y actúe
con herramientas en vez de encerrarlo en ramas fijas. Exigía cambiar mucho, y
por eso nadie lo proponía. El detalle de cada parche está en
`references/senales.md` como ejemplo de cada señal.

Lección que gobierna toda la skill: **un bug es el sistema incumpliendo su
diseño; un techo es el diseño cumpliéndose a la perfección y aun así sin
llegar.** Un bug es una foto; un techo es una serie temporal. Quien mira fotos
encuentra bugs. Tú miras la historia de los arreglos.

el proyecto de referencia (un SaaS con chat de IA) es un ejemplo de MÉTODO, no una plantilla de diagnóstico. Si el camino
que acabas recomendando se parece a "abrir el modelo" o "dale herramientas al
modelo", el dictamen tiene que escribir en qué se diferencia este objeto de
el proyecto de referencia (un SaaS con chat de IA) y qué evidencia PROPIA lo sostiene; sin eso, baja a palanca. Subir de
grado una decisión no es un bien en sí: en dinero, permisos, coste y reglas
legales, el código fijo es el producto.

## Los dos fallos que matarían esta skill (y sus frenos)

1. **Recomendar reescribir por reflejo** (el síndrome del consultor). Freno:
   el veredicto "hay techo" solo se emite tras intentar refutarlo construyendo
   el **parche campeón** (Fase 4) y tras un **panel escéptico** en contexto
   limpio (Fase 6). Y antes de abrir un fichero escribes la **frase de
   falsación**: qué evidencia te obligaría a concluir que NO hay techo. Si
   aparece, se acata aunque el dictamen esté medio escrito. Terminar en "aquí no
   hay techo, no toques la arquitectura" es un éxito de primera clase.
2. **No ver el techo porque miras bugs.** Freno: la arqueología de parches se
   agrupa por SÍNTOMA, no por bug; el mapa de decisiones anota quién decide en
   cada bifurcación; y el techo se enuncia como invariante falsable con una
   predicción que se comprueba.

Meta-regla de desempate: ante dos lecturas razonables de cualquier regla de esta
skill, gana la que hace más difícil emitir un veredicto sin evidencia.

## Reglas duras (transversales a todas las fases)

- **Cada afirmación lleva nivel de evidencia**: `MEDIDO` (comando y salida
  real), `LEÍDO` (fichero:línea o documento), `INFERIDO` (razonamiento sobre
  hechos citados) o `SIN MEDIR` (con el comando que lo mediría). Las
  **afirmaciones clave** son las que sostienen el modo, numeradas en la sección
  7 del dictamen. Si menos de la mitad son MEDIDO o LEÍDO, el dictamen se
  entrega igual pero el modo baja un escalón (A→B, B→C) y la portada lo dice.
- **Cero cifras inventadas.** Ni conversiones "típicas", ni tamaños de mercado,
  ni "un 30 % más rápido", ni umbrales puestos a ojo. Lo heredado de memorias o
  informes viejos se re-mide en la sesión (la memoria de el proyecto de referencia (un SaaS con chat de IA) arrastró "~0
  clientes" cuando Stripe tenía 15 cobros). Si no se puede medir: `SIN MEDIR`.
  Los costes se derivan de un precedente citado (qué tocó y cuánto llevó un
  cambio parecido, según nota fechada) y van como `INFERIDO`; sin precedente,
  `SIN MEDIR`.
- **Unidad de coste**: una **sesión** es un bloque de unas 3 horas de trabajo
  de el usuario sin cambiar de proyecto. Todo coste y todo kill-test se expresa en
  sesiones, para el usuario solo y manteniendo lo demás en paralelo, más €/mes
  recurrentes. Nunca sprints ni "un par de tardes". Siempre con el coste de
  oportunidad: qué pasaría si esas sesiones fueran a vender o a otro proyecto.
- **Test de genericidad**: si una frase del dictamen seguiría siendo cierta
  cambiando el nombre del proyecto, se borra o se aterriza con evidencia.
  Prohibidos "añadir tests", "modularizar", "meter una cola", "migrar a X",
  "usar agentes" sin la lista de casos especiales concretos que eliminan.
- **Bug ≠ techo (aplicado al síntoma de HOY).** Si el síntoma actual se cierra
  con un cambio de ≤50 líneas en ≤2 ficheros que no añade rama, lista ni regex,
  es un bug: anexo, /code-review. Esto NO se aplica a los parches históricos:
  un parche pequeño que no reabrió sigue contando como fila de la arqueología
  si aterriza en el punto recurrente. Lo que se descarta es el síntoma barato,
  no la historia. Y lo que decide "deuda o techo" en el campeón es la prueba de
  la Fase 4 (¿añade caso especial?), no el tamaño del cambio.
- **Valla de Chesterton**: antes de declarar que una decisión limita,
  reconstruye por qué se tomó (nota de memoria, comentario, commit). "No
  entiendo esta decisión" no es "esta decisión está mal".
- **Coherencia con lo que el usuario ya decidió**: si un camino contradice una
  decisión suya documentada, se señala y se justifica; no se ignora.
- **Solo lectura sobre lo real.** Lees código, git, logs y copias de BD (solo
  SELECT); experimentas en la carpeta de estado; no despliegas, no migras, no
  reinicias, no tocas Stripe ni BD en vivo. Stripe, pagos y BD remotas solo se
  leen si el proyecto YA tiene un camino de lectura construido (su propio
  script, una copia local); nunca extraes claves de `.env` ni llamas a APIs de
  pago por tu cuenta. Sin camino de lectura: `SIN MEDIR`. Bancos de casos
  anonimizados; cada proyecto con SUS claves, nunca cruzadas. Y sin rastro
  involuntario: abrir una SQLite del proyecto crea `-wal`/`-shm`, importar sus
  módulos crea `__pycache__`; copia la BD a la carpeta de estado antes de
  consultarla y ejecuta scripts del proyecto solo desde copias. Si aun así
  dejas rastro, decláralo en el dictamen.
- **Sin usuarios inventados.** La voz del usuario solo viene de artefactos
  guardados (conversaciones, logs, correos, tickets, notas), y se cita de dónde.
- **Sin preguntas durante la pasada.** Preguntar termina el turno y no existe
  "preguntar y seguir". Lo que falte se marca `SIN MEDIR` y se sigue. Si hay
  UNA cosa crítica y no deducible, va al final del dictamen como "Pregunta
  única para el usuario", con lo que cambiaría del veredicto según la respuesta.
- **Máximo 3 caminos, 1 recomendado**, y al menos uno NO técnico (dato,
  promesa, precio, canal, empaquetado). Un menú A/B/C sin recomendación no vale.
- **Castellano de España, tú, sin emojis, sin paja, veredicto en la primera
  línea.**

## Estado en disco

Todo vive FUERA del proyecto, en `~/.claude/techo\<slug>\`: así
no se cuela en un `git add`, un despliegue ni un zip para un cliente, y las
notas de todos los proyectos quedan juntas para compararlos. En el proyecto no
se escribe nada. Si no está en disco, no ha pasado.

| Ruta | Contenido |
|---|---|
| `<slug>\NOTA_TECHO.md` | Nota persistente: veredicto vigente, fecha, invariante, cuello (y su acoplado), predicciones falsables con fecha, disparador de reapertura, resultado de predicciones anteriores. **Se lee la PRIMERA en cada pasada.** |
| `<slug>\<YYYYMMDD>\contrato.md` | Fase 0. |
| `<slug>\<YYYYMMDD>\evidencia\` | Libro de evidencias `E-nn`: comando, salida cruda, fecha. Consultas con resultado. Resultados crudos de subagentes. |
| `<slug>\<YYYYMMDD>\banco_casos\` | 10-20 casos reales anonimizados (al menos 5 de los que hoy fallan). |
| `<slug>\<YYYYMMDD>\campeon\` | El parche campeón: diseño, código si se construyó, resultado sobre el banco. |
| `<slug>\<YYYYMMDD>\panel\` | Prompts y respuestas crudas del panel escéptico. |
| `<slug>\<YYYYMMDD>\DICTAMEN.md` | El informe. Formato en `references/dictamen.md`. |
| `<slug>\RAPIDA_<YYYYMMDD>.md` | Salida de una pasada rápida. Una rápida NUNCA escribe `NOTA_TECHO.md`. |

Si ya existe `NOTA_TECHO.md`: la siguiente pasada EMPIEZA calificando sus
predicciones (¿se cumplieron?) y sus disparadores. No se repite el análisis
desde cero ni se vuelve a proponer lo ya descartado sin explicar qué ha cambiado.

## Pasada rápida o completa

- **Completa** (por defecto): todas las fases, con subagentes en paralelo.
- **Rápida**: si el usuario dice "rápido" o "un vistazo", o si el camino crítico
  son menos de 20 ficheros / 5.000 líneas, o si el objeto no tiene historial
  (sin git, sin copias fechadas, sin notas). Hace Fase 0, adjudicación del
  cuello, mapa de decisiones y arqueología ligera, test del parche en seco, y
  emite `VEREDICTO PROVISIONAL (pasada rápida): MODO <x>` en
  `RAPIDA_<fecha>.md`, diciendo qué añadiría la completa y si merece la pena.
  Una rápida nunca emite modo A ni escribe la nota de techo.

## Fase 0 — Contrato y pre-registro (antes de abrir un solo fichero)

Escribe `contrato.md` con:

1. **Objeto y frontera**: qué se examina exactamente y qué queda fuera. Tipo
   de objeto (código / tienda / proceso / plan): si no es código, rellena la
   tabla de equivalencias de `references/senales.md` antes de seguir.
2. **Métrica-rey**: la única cifra que dice si el proyecto crece (€ cobrados,
   pedidos, leads con teléfono, informes útiles…) y su fuente medible.
3. **Objetivo declarado**: la cifra y la fecha que el usuario considera "crecer",
   sacada de sus notas, memoria o una frase suya citada. Si no existe, se
   escribe `SIN OBJETIVO`: entonces la condición (4) del modo A solo puede
   cumplirse por "clase de petición irrepresentable", nunca por una estimación.
4. **Madurez y volumen real**: idea / primeros usuarios / en producción con
   volumen. Se mide, no se supone.
5. **Ejecutabilidad**: comando exacto para correr el objeto en local, qué
   claves necesita (las suyas), coste por ejecución y si se puede sin tocar
   producción. De esto depende si la predicción de la Fase 3 y el kill-test se
   ejecutan o se trazan en seco.
6. **Presupuesto**: sesiones de el usuario disponibles y €/mes; intocables
   (producción, Stripe LIVE, claves, lo que ya cobra).
7. **Frase de falsación pre-registrada**: "Concluiré que NO hay techo si
   <evidencia concreta>". Se copia literal en la portada del dictamen.
8. **Lo que el usuario ya intentó y descartó** (memoria, notas, TODOs, carpetas
   `-fix`, `-v2`): para no proponerle lo que ya probó sin decir qué cambia.

## Fase 1 — Adjudicación del cuello

Antes de proponer nada, decide con números dónde está hoy el límite de la
métrica-rey: en el **código** (el objeto), en el **dato** (cobertura, frescura,
fuente rota), en **distribución o precio** (nadie llega, nadie paga), en una
**plataforma de terceros** (políticas de Meta, límites de una API, un scraper
que un tercero rompe), en las **horas de el usuario** (atención repartida entre
proyectos) o **entre proyectos** (duplicar lo que otro proyecto suyo ya tiene,
o acoplar dos que deberían ir separados).

Se hace con el embudo de punta a punta hasta donde se pueda medir y con
conteos reales. Si el cuello está FUERA del objeto pedido, se dice en la
PRIMERA línea del dictamen y se propone el objeto correcto, pero el análisis
de techo **no se cierra**: continúa, porque un techo estructural demostrado
que hoy no aprieta se archiva con disparador (modo A-ARCHIVADO), no se
entierra. Enterrarlo es exactamente lo que le pasó a el proyecto de referencia (un SaaS con chat de IA) durante meses.

Si aparecen DOS restricciones reales y acopladas (el proyecto de referencia (un SaaS con chat de IA): dato pobre en
Sudamérica Y pipeline cerrado), no te refugies en "instrumentar": nombra las
dos, di cuál desbloquea a la otra, cuál es reversible y qué parte del síntoma
explica cada una. Las plantillas del dictamen y de la nota tienen sitio para
el cuello acoplado.

## Fase 2 — Mapa de decisiones y arqueología de parches

Es la fase que encuentra el techo. Dos artefactos, construidos en paralelo por
lectores en contexto limpio que devuelven cifras y `fichero:línea`, no opiniones.

**Mapa de decisiones con grado de cierre.** Recorre el camino crítico por donde
pasa el valor y, en cada bifurcación (qué buscar, qué filtrar, qué hacer si no
hay resultados, cuántos devolver, qué forma tiene la salida, a quién escribir,
qué precio…), anota quién decide y con qué grado de cierre:

| Grado | Quién decide | Ejemplo |
|---|---|---|
| 0 | Código fijo (if, regex, umbral mágico) | `if len(q) < 80: fusionar` |
| 1 | Lista o mapa estático dentro del código | `REGION_LEAGUE_MAP`, diccionario ES→EN |
| 2 | Datos o configuración (BD, fichero editable) | tabla de ligas en BD |
| 3 | El modelo o el usuario, con herramientas y límites | el modelo elige qué consultar |

Con `fichero:línea`, número de ramas, y cruzado con la arqueología: las
decisiones más parcheadas en grado 0-1 son la radiografía de un modelo
cerrado. El grado no es una escala de calidad: es un inventario de dónde vive
cada decisión. Sobre el mapa, la tabla de **supuestos fundacionales**: 5-15
decisiones del día 1 escritas como afirmación en presente ("el código decide
el flujo y el modelo rellena huecos", "cada consulta devuelve un ganador", "la
liga se guarda como texto libre"), dónde están grabadas y qué sería posible si
fuesen falsas.

**Arqueología de parches, agrupada por SÍNTOMA.** Reconstruye la historia de
los arreglos sobre el camino crítico: fecha, qué síntoma atacaba, dónde aterrizó
(`fichero:línea`), si AÑADIÓ una rama/lista/regex o la QUITÓ, y si el síntoma
reabrió. Con git: `git log -L :<funcion>:<fichero>`, `--numstat`, `-S
<constante>`. **Sin git (lo normal en C:\Dev)**: mtimes, carpetas paralelas
(`proyectofix`, `-v2`, `_Archivo`), copias `*.bak_*` fechadas, comentarios con
fecha ISO dentro del código, ficheros `patch_*.py`, y las notas de memoria del
proyecto como bitácora. Lo que buscas: **tres o más parches, de meses
distintos, por problemas sin relación aparente, que aterrizan en el mismo punto
y todos añaden una rama o una lista mantenida a mano.** Eso no son tres bugs:
es un techo repetido con tres caras. Además, reagrupa por CAUSA los hallazgos de
auditorías e informes anteriores: si tres caen del mismo lado, ahí está.

Las señales completas, con sus detectores (comandos etiquetados por shell) y
sus falsos positivos, están en `references/senales.md`. Léelo antes de esta
fase. Los patrones de búsqueda se lanzan con la herramienta Grep o con `rg -n`
(nunca `rg -E`: en ripgrep `-E` es la codificación, no el tipo de regex).

## Fase 3 — Enunciado del techo y aritmética

1. **Invariante falsable**, una frase: «Mientras <X> siga siendo cierto, ningún
   parche podrá <Y>, porque <Z>.» Con una **predicción concreta** (una
   petición legítima nueva que fallará con todos los parches puestos). Si el
   objeto se puede ejecutar en local con sus claves y dentro del presupuesto
   (Fase 0.5), la predicción se ejecuta y es `MEDIDO`. Si no, se traza EN SECO
   sobre el mapa (`fichero:línea` de la rama que la atendería) y es `INFERIDO`.
   Si la predicción no falla, el techo enunciado era falso: reformula o cierra
   en modo B.
2. **Techo aritmético**: calcula con una consulta o aritmética real el máximo
   que el diseño actual daría ejecutado perfecto (cobertura de la fuente, % de
   peticiones representables sobre logs, margen × conversión medida × tope del
   canal) y ponlo al lado del objetivo declarado (o `SIN OBJETIVO`). Es
   simétrico: si el máximo está por encima del objetivo, NO hay techo y pasas a
   modo B. Si falta un dato real en medio, la fase devuelve `SIN MEDIR`, no un
   supuesto.
3. **Test de las 10 peticiones**: 10 peticiones legítimas nuevas del dominio,
   sacadas del histórico real; para cada una, traza qué rama del mapa la
   atendería. Cuenta cuántas exigen tocar código para poder siquiera
   representarse. Umbral de la señal 7: cuatro o más. El resultado se cita como
   señal numerada en la portada.
4. **Test del parche (caso N+1 en seco)**: coge el siguiente caso real que el
   proyecto necesitará (otro país, otro cliente, otro tipo de petición) y lista
   cada `fichero:línea` que habría que tocar. Si el número no es cero y crece
   con cada caso, la restricción es la forma del sistema, no una pieza.

## Fase 4 — Refutación obligatoria: el parche campeón

Prohibido emitir veredicto de techo sin esta fase. Construye (en la carpeta de
estado, jamás en producción) **el mejor arreglo conservador posible dentro del
camino actual**: el que un buen ingeniero prudente propondría para matar el
síntoma sin cambiar la arquitectura. Mídelo contra un **banco de 10-20 casos
reales** del proyecto (conversaciones, consultas con cero resultados, pedidos,
leads), al menos 5 de los que hoy fallan, anonimizados, en `banco_casos\`. Si
el objeto no se puede ejecutar en local, el campeón se juzga en seco caso a
caso sobre el mapa y se etiqueta `INFERIDO`.

- Si el campeón cierra el síntoma **sin añadir otra rama, lista o regex**: no
  hay techo, hay deuda. Modo B, dictamen corto, y acabas de ahorrarle meses a
  el usuario. Ese es el mayor valor de la skill, no el caso contrario.
- Si solo lo cierra añadiendo otro caso especial (es el enésimo parche de la
  serie), o no lo cierra: techo confirmado **por construcción**, no por opinión.
  En el proyecto de referencia (un SaaS con chat de IA) el campeón era la ampliación dirigida por región: exactamente lo que
  el usuario construyó, y solo funcionaba metiendo otra lista estática.

El resultado se publica en el dictamen aunque desmonte la tesis.

## Fase 5 — Caminos (solo si el techo sobrevivió a la Fase 4)

Genera candidatos con las técnicas de `references/caminos.md` (léelo): negar
cada supuesto fundacional; subir de grado las decisiones más parcheadas; borrar
el componente que genera los parches y diseñar sin él; cambiar la unidad de
entrega o la frontera del sistema; rescatar lo que el usuario ya aparcó por caro;
inventario de activos ya construidos y sin usar. Ningún camino entra por la
tecnología que usa: entra por los casos especiales que mata.

Criba a **máximo 3, al menos uno no técnico, uno recomendado**. Cada camino
trae obligatoriamente su ficha completa (en `caminos.md`): invariante que
rompe; casos especiales que MATA (mínimo cinco: `fichero:línea` en caminos de
código; en caminos de dato/promesa/precio/canal, casos REALES del banco que
hoy no se sirven, citados por su id); **kill-test** de menos de una sesión
sobre el banco, con umbral numérico escrito ANTES; **seam** de convivencia (un
punto de extensión que YA existe —registro de fuentes, blueprint, tabla, flag,
ruta nueva— por donde lo nuevo entra sin tocar lo viejo) y vuelta atrás en
minutos, con qué ficheros mueren y cuándo; inventario de lo que se pierde el
día 1; coste en sesiones (derivado de precedente) y €/mes; y su **próximo
techo**. Un camino presentado sin contras está mal analizado.

Sin kill-test ejecutable en menos de una sesión, o sin seam, el camino NO entra
en los tres: va a "Descartados" con la etiqueta correspondiente y la condición
que lo haría ejecutable. Si el kill-test del recomendado cabe en el presupuesto
de la pasada y el objeto es ejecutable en local, **ejecútalo**: un camino con
kill-test ejecutado vale más que tres sin ejecutar.

## Fase 6 — Panel escéptico (contextos limpios)

Se lanza según el veredicto provisional: el **Verificador siempre** (es barato
y es quien caza cifras mal etiquetadas y frases de falsación mal diseñadas,
también en modo D); el **Conservador** en A, A-ARCHIVADO, A-DIFERIDO, B y C
(su texto es obligatorio en la sección 11); el **Contable** solo en la familia
A. Cada papel recibe SOLO el libro de evidencias, el mapa,
la arqueología, el resultado del campeón, las fichas de camino y el contrato;
nunca tu veredicto provisional ni tu razonamiento. Prompts verbatim en
`references/dictamen.md`:

- **Conservador**: construye el mejor argumento para no cambiar nada, incluido
  "el síntoma es un bug barato". Su texto se publica literal en el dictamen.
- **Contable**: traduce cada camino a sesiones y €/mes citando el precedente
  en que se apoya, incluido el coste de mantener dos sistemas durante la
  convivencia, y lo compara con dedicar esas sesiones a vender o a otro
  proyecto. Sin precedente, marca la estimación como no sostenida.
- **Verificador**: recibe la lista de afirmaciones clave (sin portada ni
  modo), reproduce cada cita `MEDIDO`/`LEÍDO`, tacha las que no cuadren y
  comprueba que el invariante y la predicción son falsables.

Desempate: gana quien traiga la evidencia de nivel más alto; a igualdad, el
modo más conservador. Lo no resuelto se publica como desacuerdo, no se
promedia. Si el Conservador encuentra el parche barato, el veredicto baja.

## Regla de modo

Las puertas se evalúan UNA SOLA VEZ, al terminar la Fase 6, con todas las
fases hechas. Ninguna puerta se aplica a mitad del análisis para abreviarlo.
Los sub-criterios que requieren Fase 5 (coste del camino más barato) solo se
evalúan si hubo Fase 5. En orden; la primera que se cumple manda:

- **Puerta 0 → MODO D, medir primero**: la métrica-rey no es medible con las
  fuentes accesibles, o el volumen es ruido, Y ADEMÁS no hay ninguna señal
  estructural (1, 2, 3, 7 o 12 de `senales.md`, las que no necesitan volumen)
  confirmada con ancla. Se entrega la instrumentación mínima (qué registrar,
  dónde, esquema) y la fecha para repetir; prohibido recomendar cambio de
  camino. Si SÍ hay señal estructural confirmada, no es D: el veredicto sale
  como A-DIFERIDO o A-ARCHIVADO con la instrumentación como primera acción. Un
  techo demostrado por estructura no necesita serie temporal; la falta de
  métrica rebaja la confianza, no anula el dictamen.
- **Puerta 1 → MODO C, no tocar / otro objeto**: el cuello está fuera del
  objeto y NO hay techo estructural demostrado dentro; o el sistema nunca ha
  sido estresado por uso real y no hay señal estructural; o el coste del camino
  más barato supera el presupuesto; o no hay ventana operativa (incidencias
  abiertas, servicio inestable, despliegue reciente sin verificar). Se dice en
  la primera línea y se propone el objeto correcto.
- **Puerta 2 → MODO B, palancas dentro del camino**: el parche campeón cierra
  el síntoma sin nuevo caso especial; o el techo aritmético deja margen claro;
  o quedan palancas obvias sin tirar. Salida: máximo 3 palancas ordenadas por
  efecto sobre la métrica-rey, con mecanismo en tres pasos, separando
  **palanca** (mueve la métrica) de **higiene** (arregla, no mueve); umbral y
  fecha que reabrirían el modo A.
- **MODO A, romper el techo**: solo con TODAS: (1) invariante enunciado, con
  predicción `MEDIDO`, o predicción en seco `INFERIDO` más campeón `MEDIDO`
  sobre el banco; (2) tres o más señales confirmadas con ancla reproducible,
  una de ellas obligatoriamente "parche recurrente en el mismo punto" o "test
  del parche positivo" (la señal 7, 10 peticiones, puede ser la tercera); (3)
  el campeón no basta o solo basta con otro caso especial; (4) techo
  aritmético por debajo del objetivo, o clase de petición demostradamente
  irrepresentable; (5) al menos un camino que mata cinco o más casos citados,
  con kill-test y seam.
- **MODO A-ARCHIVADO**: se cumplen las condiciones de A pero la Fase 1 sitúa
  el cuello ACTUAL fuera del objeto. El dictamen dice en portada que hoy no
  toca, entrega igualmente el techo demostrado, el camino y su kill-test, y los
  archiva en `NOTA_TECHO.md` con **disparador de activación** explícito
  ("cuando haya X consultas al mes", "cuando el escalón de adquisición deje de
  perder el orden de magnitud"). Nunca se entierra un techo demostrado.
- **MODO A-DIFERIDO**: se cumplen (1)-(4) pero falla (5), o la predicción y el
  campeón solo pudieron trazarse en seco. Se documenta el techo, se listan los
  candidatos con lo que le falta a cada uno, se opera en B y se escribe la
  condición exacta que lo desbloquearía.

Frenos: ante duda gana el modo más conservador (D > C > B > A); si la frase de
falsación se cumple, el veredicto de techo se retira; una recomendación de modo
A sin una cifra `MEDIDO` que la sostenga se degrada a B con la nota "sospecha de
techo, no demostrada"; la confianza (alta/media/baja) baja de oficio si alguna
cifra clave está `INFERIDO` o `SIN MEDIR`. El modo, las condiciones cumplidas,
las no cumplidas y la confianza van en la PRIMERA línea del dictamen.

## Fase 7 — Dictamen y nota de techo

Escribe `DICTAMEN.md` con la estructura exacta de `references/dictamen.md`.
Secciones que nunca faltan: veredicto en portada con la frase de falsación;
**lo que NO hay que tocar** (mínimo 3 cosas que están mal pero no son la
restricción, con el motivo: si no puedes rellenarla, no has entendido el
sistema); **el caso a favor de no cambiar nada** (texto del Conservador);
**lista de congelación**; **descartados y por qué**; **lo que no se pudo
verificar**; **3 predicciones falsables con fecha**; anexo con el libro de
evidencias y su columna "cómo re-medir". Las secciones condicionales se
escriben igual con una línea que explica por qué están vacías. Los bugs vistos
de paso van en un anexo corto, derivados a /code-review. Los candidatos que se
archivan (modos D, C, A-ARCHIVADO, A-DIFERIDO) llevan igualmente su kill-test
escrito (protocolo, umbral, banco), aunque no se ejecute: cuando salte el
disparador, el plan tiene que estar listo, no por hacer.

**Pasada de coherencia antes de entregar.** Tras el panel, relee el dictamen
entero y propaga cada corrección (una cifra tachada por el Verificador, un
orden cambiado por el Contable) a TODAS las secciones donde aparezca: una
cifra corregida en la sección 15 y vieja en la 4 invalida las dos. Comprueba
también que las acciones de la sección 17 no contradicen lo que la 15 dejó
como "no verificado" o "no hacer todavía".

Actualiza `NOTA_TECHO.md`. Escribe la memoria en
`~/.claude/projects/<proyecto>/memory/project_techo_<slug>_<fecha>.md`
y añade su línea al índice `MEMORY.md` en la sección del proyecto. Reporta a
el usuario en el chat con el formato corto de `dictamen.md`: veredicto y modo, la
frase del techo (o de que no lo hay), el camino recomendado con su kill-test,
las 3 primeras acciones, qué no tocar, y la ruta del dictamen. Nada de
"¿sigo?": el dictamen es el entregable; ejecutar el camino es otra sesión (y
otra skill: /perfeccionista o /super-equipo).

## Orquestación

Cuando el usuario invoca /techo, esa invocación autoriza el uso de la herramienta
**Workflow** (la herramienta admite como opt-in una skill que instruye a
llamarla). Úsala para las fases con paralelismo: lectores de la Fase 2 (mapa,
arqueología, cuello, banco), generadores de caminos de la Fase 5 (uno por
técnica) y el panel de la Fase 6. Si Workflow no aparece en tu sesión (por
ejemplo, corres como subagente), no la pidas ni la simules: usa **Agent** con
varias llamadas en el mismo mensaje. Si tampoco hay Agent, haces tú cada papel
en secuencia, en modo degradado declarado en el dictamen, y un panel degradado
nunca firma modo A. Todos los subagentes con `model: 'opus'` (el usuario lo pidió:
Fable solo en el hilo principal). Esqueleto del script, esquemas de salida,
prompts de los lectores y la variante para objetos no-código en
`references/orquestacion.md`. Las Fases 0, 1, 3, 4 y 7 son tuyas: el criterio
no se delega.

Reglas de contexto limpio: cada subagente recibe solo su encargo, rutas
absolutas, y los artefactos que necesita; nunca tu hipótesis ni tu veredicto.
Los lectores devuelven cifras y anclas; los generadores devuelven fichas de
camino; el panel devuelve refutaciones. Lo que un subagente afirme sin ancla
no entra en el dictamen.

## Cuándo debe el usuario invocarte (dilo si ves el patrón aunque no te llame)

- El mismo síntoma vuelve por tercera vez con otra cara.
- Cuatro intervenciones en el mismo módulo en tres meses y la queja sigue.
- El próximo arreglo solo se puede hacer añadiendo otra lista o mapa a mano.
- Meses de trabajo verificado y la métrica-rey no se mueve.
- En sus notas aparece "requiere reescribir", "demasiado grande", "fase 2".
- Antes de invertir sesiones grandes en mejorar algo "como hasta ahora".

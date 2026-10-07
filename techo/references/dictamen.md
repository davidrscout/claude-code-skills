# Dictamen — estructura exacta, niveles de evidencia, nota de techo y prompts del panel

## Niveles de evidencia (obligatorios en cada afirmación relevante)

| Etiqueta | Significa | Forma |
|---|---|---|
| `MEDIDO` | Se ejecutó un comando o consulta en esta pasada | `[MEDIDO E-07]` → entrada del libro con comando, salida, fecha |
| `LEÍDO` | Está escrito en un fichero o documento | `[LEÍDO core/x.py:602]` o `[LEÍDO memoria project_chat_retrieval.md]` |
| `INFERIDO` | Razonamiento explícito sobre hechos citados | `[INFERIDO de E-03 y x.py:160]` |
| `SIN MEDIR` | No se pudo medir; se da el comando que lo mediría | `[SIN MEDIR: SELECT ... ]` |

Las **afirmaciones clave** son las que sostienen el modo, numeradas en la
sección 7. Si menos de la mitad son MEDIDO o LEÍDO, el dictamen se entrega
igual pero el modo baja un escalón (A→B, B→C) y la portada lo dice. Los datos
heredados de memorias o informes anteriores se re-miden; si no se puede, son
`SIN MEDIR`, no `LEÍDO`.

## Estructura de `DICTAMEN.md`

Secciones en este orden; ninguna se omite. Las marcadas "solo en modo X" se
escriben igual en los demás modos, con una línea que explica por qué están
vacías. En una pasada rápida el fichero es `RAPIDA_<fecha>.md`, la primera
línea es `VEREDICTO PROVISIONAL (pasada rápida): MODO <x>` y se omiten 8, 9,
11, 13 y 15 con esa explicación.

```
# DICTAMEN TECHO — <objeto> — <fecha>

**VEREDICTO: MODO <D | C | B | A | A-ARCHIVADO | A-DIFERIDO> — confianza <alta|media|baja>.**
<Una frase: el techo (o que no lo hay) y qué hacer.>
Condiciones de modo A cumplidas: <lista> · No cumplidas: <lista>.
Afirmaciones clave MEDIDO/LEÍDO: <n> de <m> (si < mitad: modo rebajado de <x> a <y>).
Frase de falsación pre-registrada: "<literal del contrato>" → <se cumplió / no se cumplió>.
Cuello actual (Fase 1): <código | dato | distribución/precio | plataforma | horas de el usuario | entre proyectos>, <dentro/fuera del objeto>
  [+ <capa 2> acoplada: cuál desbloquea a cuál, cuál es reversible, qué parte del síntoma explica cada una].
Objetivo declarado: <cifra y fecha, fuente | SIN OBJETIVO>.

## 1. Resumen ejecutivo (media página)
Qué frena al sistema, qué se propone, qué cuesta, cuándo se sabrá si funciona.
Las 3 primeras acciones, concretas.

## 2. Contrato de examen
Copiado de contrato.md: objeto, frontera, métrica-rey y fuente, madurez y
volumen [MEDIDO], presupuesto, intocables, lo que el usuario ya intentó.
Tipo de objeto y, si no es código, la tabla de equivalencias usada.

## 3. Adjudicación del cuello
Embudo hasta donde se pudo medir, con cifras etiquetadas. Dónde está el
límite de la métrica-rey y por qué. Si hay dos restricciones acopladas: las
dos, el orden de ataque, cuál desbloquea a la otra.

## 4. Mapa de decisiones y supuestos fundacionales
Tabla: decisión → quién decide (grado 0-3) → fichero:línea → nº de ramas →
parches que acumula. Tabla de supuestos: afirmación → dónde está grabada →
qué sería posible si fuese falsa.

## 5. Arqueología de parches (por síntoma)
Tabla: síntoma → parches (fecha, fichero:línea, añade/quita rama o lista) →
¿reabrió? → causa estructural compartida. Método usado (git / sin git).
Hallazgos de auditorías previas reagrupados por causa.

## 6. Señales de techo encontradas (y las buscadas que NO aparecieron)
Una entrada por señal de senales.md: evidencia con ancla, falso positivo
descartado y cómo. Las señales buscadas y ausentes también se listan: son la
prueba de que NO hay techo cuando el modo es B o C.

## 7. El techo enunciado
Invariante: «Mientras <X> siga siendo cierto, ningún parche podrá <Y>, porque <Z>.»
Predicción ejecutada: <qué se probó, resultado, E-nn>.
Techo aritmético: <cálculo, consulta, resultado> frente al objetivo <valor, fuente>.
Test de las 10 peticiones: <n>/10 exigen tocar código (lista).
Test del parche (caso N+1): <lista de fichero:línea que habría que tocar>.

## 8. Refutación: el parche campeón
Qué se diseñó, qué se construyó (ruta en campeon\), banco de casos usado
(ruta, tamaño, anonimizado), resultado medido, y el veredicto: cierra sin
caso especial nuevo / cierra solo con otro caso especial / no cierra.

## 9. Caminos (máximo 3, fichas completas de caminos.md) — solo en modo A/A-ARCHIVADO/A-DIFERIDO
Camino recomendado primero, con kill-test ejecutado si cupo. En A-DIFERIDO:
los candidatos generados y, por cada uno, exactamente qué le falta (kill-test,
seam o casos) y qué lo desbloquearía.

## 10. Palancas dentro del camino actual (máximo 3) — siempre
Palanca vs higiene. Umbral y fecha que reabrirían el modo A.

## 11. El caso a favor de no cambiar nada
Texto LITERAL del Conservador del panel. Debajo, qué parte del veredicto
cambió por su argumento y qué parte no, y por qué.

## 12. Lo que NO hay que tocar
Mínimo 3 cosas que están mal pero no son la restricción, cada una con el
motivo por el que arreglarlas ahora no movería la métrica.

## 13. Lista de congelación
Qué parches y mejoras se dejan de hacer para pagar el cambio (o, en modo B,
para concentrar las sesiones en las palancas).

## 14. Descartados y por qué
Una línea por camino o palanca que no sobrevivió: motivo (sin kill-test, sin
seam, mata < 5 casos, contradice decisión de el usuario, coste > presupuesto…).

## 15. Panel escéptico: desacuerdos y verificación
Contable: cifras. Verificador: citas tachadas y por qué. Desacuerdos no
resueltos, publicados como tales.

## 16. Lo que no se pudo verificar
Huecos de datos, accesos que faltaron, supuestos, y cómo debilitan el
veredicto. Nivel de confianza por hallazgo clave. Si hay UNA cosa crítica y
no deducible: "Pregunta única para el usuario", con lo que cambiaría del veredicto
según la respuesta.

## 17. Plan y contrato de seguimiento
Las dos primeras semanas en tareas concretas (empezando por el kill-test o
la primera palanca). Tres predicciones falsables con fecha y forma exacta de
comprobarlas. Disparadores de reapertura del dictamen.

## Anexo A. Bugs e higiene vistos de paso
Lista breve, derivada a /code-review. No cuentan como señal.

## Anexo B. Libro de evidencias y cómo re-medir
E-01 … E-nn: afirmación, nivel, comando o consulta, salida cruda (o ruta al
fichero en evidencia\), fecha-hora, y columna "cómo re-medir" (el mismo
comando, listo para pegar, con el valor de hoy al lado). Al final del anexo,
todos los comandos juntos en un solo bloque.
```

## `NOTA_TECHO.md` (persistente, se lee la primera en cada pasada)

```
# Nota de techo — <objeto>

ESTADO: <fecha> — MODO <x> — confianza <x>
Invariante vigente: «...»  (o: "sin techo demostrado")
Cuello actual: <capa> [+ <capa 2> acoplada: cuál desbloquea a cuál]
Objetivo declarado: <cifra y fecha, fuente | SIN OBJETIVO>
Camino recomendado: <nombre> — kill-test: <ejecutado: cifra | pendiente>
Disparador de activación / reapertura: <condición concreta y medible>
Predicciones (fecha límite → cómo comprobar → resultado):
  - <p1> → <cmd> → pendiente
  - <p2> → <cmd> → pendiente
  - <p3> → <cmd> → pendiente
Descartados (no volver a proponer sin decir qué cambió): <lista corta>
Pasadas anteriores: <fecha — modo — qué se cumplió de sus predicciones>
Dictamen: <ruta>
```

## Prompts del panel escéptico (verbatim; guarda prompt y respuesta en panel\)

Cada uno recibe SOLO: el libro de evidencias, el mapa de decisiones, la
arqueología, el resultado del parche campeón, las fichas de camino y el
contrato. No recibe el veredicto provisional ni el razonamiento del hilo
principal. Todos con `model: 'opus'`. Quién se lanza: el Verificador siempre
(incluido modo D); el Conservador en A, A-ARCHIVADO, A-DIFERIDO, B y C; el
Contable solo en la familia A.

### Conservador

```
Eres un ingeniero prudente con veinte años manteniendo sistemas que cobran
dinero. Te dan la evidencia recogida sobre <objeto> (rutas absolutas abajo). Tu
único encargo es construir el MEJOR argumento posible a favor de NO cambiar de
camino: que el síntoma es un bug barato, que el techo no está demostrado, que
el camino actual aún da de sí, que el coste de cambiar no compensa, o que lo
que limita está en otro sitio. Busca activamente el parche barato que el
análisis no vio. Usa solo la evidencia y lo que puedas comprobar tú mismo en
el proyecto (solo lectura). Cada afirmación con su ancla (fichero:línea,
comando, consulta). Responde en castellano de España, sin cortesías, con:
(1) tu argumento en menos de una página; (2) el parche barato si existe, con
fichero:línea y estimación honesta; (3) qué evidencia del análisis consideras
débil y por qué; (4) tu veredicto: "no hay techo" / "techo no demostrado" /
"techo plausible pero no toca ahora" / "techo demostrado, no encuentro el
parche barato". Si al final te convences de que sí hay techo, dilo: ganas
igual.
Rutas: <evidencia\, contrato.md, mapa, arqueología, campeon\, fichas>
```

### Contable

```
Eres el contable de un desarrollador que trabaja solo, mantiene varios
proyectos a la vez y tiene clientes de pago. Te dan las fichas de camino y la
evidencia sobre <objeto>. Tu encargo: traducir cada camino a su coste REAL
en sesiones de trabajo del desarrollador (solo, manteniendo lo demás) y en
€/mes recurrentes, incluido el coste de sostener DOS sistemas durante la
convivencia y a partir de qué duración esa carga hace inviable el camino.
Compara cada camino con dedicar esas mismas sesiones a vender o a otro
proyecto del desarrollador. Una sesión son unas 3 horas de trabajo suyo sin
cambiar de proyecto. Señala toda estimación optimista de las fichas y
corrígela CITANDO el precedente en el que te apoyas (un cambio parecido del
propio proyecto: qué tocó y cuánto llevó, según nota fechada o historial);
sin precedente, marca la estimación como "no sostenida" en vez de sustituirla
por otra cifra tuya. Nada de sprints ni story points. Responde en castellano
de España con una tabla camino → sesiones (rango, precedente) → €/mes (fuente)
→ coste de convivencia → coste de oportunidad → tu recomendación (merece la
pena / solo si <condición> / no).
Rutas: <fichas, contrato.md, evidencia\, arqueología (precedentes)>
```

### Verificador

```
Eres un verificador de citas. Te dan una lista de afirmaciones etiquetadas
MEDIDO, LEÍDO, INFERIDO o SIN MEDIR sobre <objeto>, con su libro de
evidencias. Tu encargo: reproducir CADA cita MEDIDO y LEÍDO (ejecuta el
comando o abre el fichero:línea, solo lectura) y decir si cuadra. Tacha las
que no cuadren, corrige las cifras que estén mal, y rebaja de nivel las que
estén etiquetadas por encima de lo que la evidencia sostiene. Comprueba además
que el invariante enunciado es falsable (existe un experimento concreto que lo
tumbaría) y si la predicción se ejecutó de verdad o se trazó en seco. Responde
en castellano de España con una tabla afirmación → nivel declarado → nivel
real → cuadra (sí/no) → corrección, y un resumen: cuántas cuadran, cuántas no,
y qué afirmaciones quedan en pie.
Rutas: <fichero con la lista de afirmaciones clave extraída del borrador, SIN
portada ni modo: una por línea con su etiqueta y su ancla>, <evidencia\>,
<proyecto>
```

## Reporte a el usuario en el chat (al cerrar)

Corto, sin repetir el dictamen:

```
DICTAMEN <objeto>: MODO <x> (confianza <x>)
Techo: «<invariante>» — o: sin techo demostrado; el cuello está en <capa>.
Campeón: <cierra / no cierra / cierra con otro caso especial>.
Camino recomendado: <nombre> — kill-test <ejecutado: cifra | pendiente, < 1 sesión>.
Primeras 3 acciones: 1) … 2) … 3) …
No tocar: <3 cosas>.
Dictamen completo: <ruta>. Nota de techo: <ruta>.
```

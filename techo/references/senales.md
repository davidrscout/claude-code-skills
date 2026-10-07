# Señales de techo — detectores, falsos positivos y equivalencias

Una señal solo cuenta si tiene ancla reproducible (`fichero:línea`, comando con
su salida, consulta con su resultado). Una sola señal nunca es techo. Para modo
A hacen falta tres confirmadas, y una de ellas tiene que ser la 1 o la 2.

Cómo lanzar los detectores: los patrones de búsqueda van con la herramienta
Grep o con `rg -n` por Bash. **Nunca `rg -E`**: en ripgrep `-E` es la
codificación (`--encoding`) y el comando falla con "unknown encoding", lo que
haría que el lector concluyera "no hay constantes" (falso negativo). Cada
bloque de comandos lleva su shell: `(Bash)` o `(PowerShell)`; pegado en el
otro, falla.

Las señales 1, 2, 3, 7 y 12 son **estructurales**: no necesitan volumen ni
serie temporal de la métrica, y por eso son las que evitan que un proyecto de
bajo volumen caiga en modo D cuando el techo está a la vista.

Índice: (1) parche recurrente · (2) test del parche · (3) conocimiento congelado
en constantes · (4) grado de cierre alto en lo más parcheado · (5) degradación a
ciegas · (6) hallazgos distintos, misma causa · (7) test de las 10 peticiones ·
(8) techo aritmético · (9) coste marginal creciente · (10) curva plana · (11)
ping-pong · (12) una sola forma de salida · Señales que NO son techo ·
Equivalencias para objetos que no son código.

---

## 1. Parche recurrente en el mismo punto por síntomas distintos

**Qué es.** Tres o más arreglos, en fechas distintas, por problemas sin
relación aparente, que aterrizan en la misma función o bloque y todos añaden
una rama, una lista o una regex. Es la señal reina: un techo repetido con
tres caras.

**Detectar (con git).** `(Bash)`
```
git log -L :<funcion>:<fichero> --date=short --format='%ad %s'
git log --since=6.months --numstat --date=short -- <ruta> | awk 'NF==3{f[$3]++} END{for(k in f) print f[k], k}' | sort -rn | head
git log -S '<nombre_de_constante>' --oneline
```
**Detectar (sin git, lo normal en C:\Dev).**
- Comentarios con fecha ISO dentro del fichero (estratos arqueológicos):
  `(Bash)` `rg -n '20[0-9]{2}-[0-9]{2}-[0-9]{2}' <fichero>`
- Copias `*.bak_*`, `*.bak_fix_*`, `*_PREVIO_*`, ficheros `patch_*.py`,
  `*_fix.py`, `repro_*.py`, carpetas paralelas (`proyectofix`, `-v2`, `_Archivo`).
  Comparar tamaños y `diff` entre versiones para datar cada parche.
- Notas de memoria del proyecto (`~/.claude/projects/*/memory/project_*.md`):
  cada nota fechada que dice "arreglado y desplegado" sobre el mismo módulo es
  una fila de la arqueología. Cada una da además un precedente de coste
  (qué tocó, cuánto llevó) para las fichas de camino.
- mtimes, para ver qué se toca siempre: `(PowerShell)`
  `Get-ChildItem -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 40 FullName,LastWriteTime,Length`

**Falso positivo.** Un monolito donde todo pasa por `app.py`: ahí el fichero se
toca siempre y no significa nada. Mide por función y por punto de decisión, no
por fichero. Y dos correcciones seguidas al estrenar una función son
aprendizaje normal, no techo.

## 2. Test del parche positivo (caso N+1 en seco)

**Qué es.** Para servir el próximo caso real (un país nuevo, un cliente nuevo,
una petición que hoy falla) hay que añadir otra rama, otro mapa o otra regex.

**Detectar.** Elige el caso N+1 del histórico real (no inventado). Recórrelo EN
SECO y lista cada `fichero:línea` que habría que tocar. Compara con lo que costó
el caso N y el N-1 si puedes datarlos. En el proyecto de referencia (un SaaS con chat de IA), una región nueva obligaba a
tocar `REGION_LEAGUE_MAP`, `PAIS_A_REGION`, `LEAGUE_LEVEL_KEYWORDS` y los
límites de valor de mercado: cuatro tablas para un caso.

**Falso positivo.** Casos que en realidad son problemas distintos disfrazados
del mismo nombre. Comprueba que son la misma familia antes de comparar costes.

## 3. Conocimiento del mundo congelado en constantes mantenidas a mano

**Qué es.** Listas o mapas dentro del código que describen una realidad que
cambia sola (ligas, países, categorías, traducciones, cobertura) y que el dato
ya tiene o podría tener.

**Detectar.** `(Bash)`
```
rg -n '^\s*[A-Z_]{4,}\s*=\s*[\{\[\(]' <nucleo>
rg -ni 'lista est[aá]tica|actualizar si|por ahora|de momento|temporal|provisional|hardcode' <nucleo>
```
Para cada constante: contar entradas y contrastarlas con el universo real
(`SELECT campo, COUNT(*) ... GROUP BY campo` en la BD, o el catálogo). Señal
fuerte si la constante cubre una fracción pequeña del universo o lleva meses
sin ampliarse mientras el universo creció.

**Falso positivo.** Catálogos legítimamente cerrados y estables: códigos ISO,
tipos de IVA, estados de un pedido, posiciones de fútbol, claves de i18n. Ahí lo
estático es la especificación.

## 4. Grado de cierre alto justo en las decisiones más parcheadas

**Qué es.** En el mapa de decisiones (SKILL.md, Fase 2), las bifurcaciones que
más parches acumulan están en grado 0 (código fijo) o 1 (lista estática), no en
grado 2 (dato) ni 3 (modelo/usuario con herramientas).

**Detectar.** Tabla decisión → grado → `fichero:línea` → nº de ramas, cruzada
con la arqueología de la señal 1. Además, predicados heurísticos que adivinan
la intención:
`(Bash)`
```
rg -n 'def _(is|wants|looks_like|seems|detect|should|has)_' <nucleo>
rg -n 're\.(search|match|compile)\(' <nucleo>
```
Mira si la heurística DECIDE la rama o solo la adorna. En el proyecto de referencia (un SaaS con chat de IA) había nueve
(`_looks_like_player_name`, `_is_shortlist_request`, `_wants_cheap`…).

**Falso positivo.** Dominios donde el determinismo es el producto: facturación,
impuestos, pagos, reglas legales, parsers de formatos estrictos (fechas ISO,
SKU). Ahí las ramas fijas son un activo. Y guardarraíles de seguridad o coste en
el borde (cortar entradas gigantes, filtrar spam): una regex ahí es correcta.

## 5. Degradación a ciegas

**Qué es.** Cuando no hay resultado, el sistema afloja condiciones sin saber
cuál sobraba, o devuelve lo más popular, en vez de poder decir "no lo sé" o
cambiar de estrategia. Es la huella del supuesto "siempre hay que devolver
algo".

**Detectar.** `(Bash)`
```
rg -n '\.pop\(|fallback|relax|relaj|ampliar|sin resultados|best.?effort|except:\s*pass|except Exception:\s*(pass|continue)' <nucleo>
```
Y leer la rama: ¿qué llega de verdad al usuario por ese camino? En el proyecto de referencia (un SaaS con chat de IA),
`relaxed.pop("filter_leagues_tm")` devolvía un central del Tottenham cuando se
pedía la B argentina.

**Falso positivo.** Degradación explícita, acotada y avisada al usuario ("no
tengo esa liga, te muestro las vecinas y te lo digo"), o fallback consciente
ante fallo de un servicio externo (caché si la API cae, reintento con backoff).

## 6. Hallazgos distintos que comparten una misma causa de diseño

**Qué es.** Bugs, TODOs y hallazgos de auditorías anteriores que, reagrupados
por CAUSA en vez de por síntoma, caen tres o más del mismo lado, señalable con
`fichero:línea`.

**Detectar.** Reúne informes previos, `BUGS_*.md`, `known issues`, backlogs de
las notas de memoria. Para cada uno pregunta: "¿qué decisión de diseño lo hace
posible?". Si la respuesta se repite, eso es el techo y no N bugs.

**Falso positivo.** Causa demasiado abstracta ("falta de tests", "código
antiguo") hasta que todo cabe en la misma caja. La causa tiene que ser una
decisión concreta con dirección.

## 7. Test de las 10 peticiones legítimas nuevas

**Qué es.** De 10 peticiones normales del dominio, sacadas del histórico real
(consultas, pedidos, leads, tickets), cuatro o más exigen tocar código para
poder siquiera representarse en el vocabulario del sistema.

**Detectar.** Inventaría el vocabulario (enums, claves del dict de parámetros,
campos del formulario, tipos aceptados). Para cada petición, traza a mano qué
rama del mapa la atendería. Cuenta.

**Falso positivo.** Producto deliberadamente estrecho por posicionamiento ("solo
hacemos X"). Si el vocabulario estrecho es la propuesta de valor y la retención
lo confirma, no es techo, es enfoque.

## 8. Techo aritmético alcanzado

**Qué es.** El máximo que el diseño actual puede dar ejecutado perfecto queda
por debajo del objetivo declarado.

**Detectar.** Cálculo con datos reales: cobertura de la fuente (`SELECT liga,
COUNT(*) FROM jugadores GROUP BY liga`), fracción de peticiones representables
sobre logs, o aritmética de negocio (margen por pedido × conversión MEDIDA ×
tope real del canal). Los supuestos van escritos al lado. Es simétrica: si el
máximo supera el objetivo con margen, NO hay techo.

**Falso positivo.** Un supuesto inventado en medio (una conversión "típica", un
CTR "de mercado"), o confundir el límite de la fuente actual con un límite
absoluto cuando la fuente se puede ampliar con configuración. Si falta un dato
real, la señal devuelve `SIN MEDIR`, no una cifra.

## 9. Coste marginal creciente del caso N

**Qué es.** Los tres últimos cambios de la misma familia tocan más sitios y
rinden menos que los tres anteriores.

**Detectar.** Tabla de los últimos 10 cambios comparables: ficheros, líneas,
sesiones invertidas, efecto medido. Con git, `git show --stat <sha>`. Sin git,
tamaños de versiones sucesivas y diffs entre copias. Excluye refactors,
renombrados masivos y features nuevas legítimas.

**Falso positivo.** Un pico puntual por algo transversal de verdad (i18n,
autenticación). Hace falta tendencia, no un punto.

## 10. Curva plana con ventana y denominador suficientes

**Qué es.** Tres o más rondas verificadas en producción y la métrica-rey dentro
del ruido.

**Detectar.** Serie de la métrica (BD, Stripe, pedidos, leads) superpuesta a
las fechas de despliegue. ANTES comprueba que el volumen da señal: con 10 usos
al mes no hay curva, hay ruido.

**Falso positivo.** Métrica que no depende del sistema examinado (trabajas el
producto y miras ventas cuando nadie entra): la línea plana acusa a la
distribución, no a la arquitectura. Ventana demasiado corta, estacionalidad,
gasto en ads. Si no hay ventana suficiente, la señal no cuenta.

## 11. Ping-pong: el arreglo de un síntoma creó el siguiente

**Qué es.** Correcciones de un parche anterior sobre el mismo punto en menos de
un mes; reglas que compiten entre sí.

**Detectar.** Commits o notas con "corrección post-", "ajuste del mapa
anterior", comentarios que documentan una marcha atrás ("'Premier League
Closing Round' era Malta → ELIMINADA por sobre-captura").

**Falso positivo.** Una regresión puntual por falta de tests. Solo cuenta si el
conflicto es entre dos reglas de negocio que se contradicen y el patrón se
repite.

## 12. Una sola forma de salida a la que se dobla todo

**Qué es.** El camino crítico solo sabe entregar una forma (un ganador con
informe, un producto, un lead) y los casos nuevos entran como "modo especial"
cosido a mano.

**Detectar.** Inventaría las formas de entrega (funciones de salida,
plantillas) y contrástalas con peticiones reales guardadas. Mira cómo llegó el
último modo: si entró como rama y no como caso del contrato, el techo es la
premisa. En el proyecto de referencia (un SaaS con chat de IA), "las 5 mejores opciones" tuvo que coserse como modo aparte.

**Falso positivo.** Herramienta deliberadamente opinada que hace UNA cosa muy
bien y dice que no al resto, con retención que lo confirma.

---

## Señales que NO son techo (y adónde van)

- **Fealdad de código**: ramas por cada 100 líneas, longitud de la función más
  larga, tamaño del fichero, crecimiento del monolito. Miden incomodidad, no
  límite. Un módulo de 2.700 líneas puede tener margen de sobra y uno limpio de
  200 puede tener un techo brutal. Se anotan como coste, no como señal.
- **Escalado por copia** (seis scrapers con el mismo hash md5): deuda de código
  de manual, se arregla parametrizando en un día y no cambia el máximo
  alcanzable. Vale solo como indicador de coste marginal (señal 9).
- **Un bug**: cambio de ≤50 líneas en ≤2 ficheros que cierra el síntoma y no
  reabre en 3 meses. Anexo, /code-review.
- **Código muerto**: se borra, no señala nada.
- **Capacidad construida y sin uso**: es una pista sobre dónde está el cuello
  y un activo para un camino, no un camino por sí misma.

---

## Equivalencias para objetos que no son código

Las señales son las mismas; cambia dónde se miran. Antes de examinar un objeto
no-código, rellena esta tabla para él en `contrato.md`.

| Concepto | Código | Tienda (Shopify/Meta) | Proceso comercial / captación | Plan o documento |
|---|---|---|---|---|
| Camino crítico | petición → respuesta → cobro | visita → producto → carrito → pago → repetición | fuente de leads → contacto → reunión → contrato | objetivo → hipótesis → acciones → medida |
| "Parche" | rama, lista, regex añadida | otro tema, otro creativo, otra oferta, otro descuento, otra app instalada | otro guion, otra plantilla de mensaje, otra lista de exclusiones, otro canal probado y abandonado | otra sección, otra excepción, otra fase 2 |
| Arqueología | git, .bak, notas | historial de temas y versiones, campañas pausadas, creativos, cambios de precio, apps instaladas/desinstaladas, notas de memoria | plantillas fechadas, CRM, hojas de leads, listas de "cadenas excluidas", notas | versiones del documento, fechas, tachados |
| Lista estática | `MAPA = {...}` | colección manual fija en el theme (`bt_handles`), reglas de descuento a mano, lista de países de envío | lista curada de marcas a excluir, mapa de sectores, guion por tipo de negocio | tabla de supuestos sin fecha |
| Grado de cierre | quién decide en el if | ¿la portada la decide una lista fija, una colección automática o el dato de ventas? | ¿quién decide a quién escribir: una lista, una heurística de "web mala", el dato de respuesta? | ¿quién decide qué se hace: el plan o la señal? |
| Degradación a ciegas | `relaxed.pop` | el pick automático que elige "ice silk underwear" para unos leggings y se publica igual | se contacta a todo lo que pasa el filtro aunque el filtro falle | seguir el plan cuando la hipótesis ya falló |
| Métrica-rey | cobros, informes útiles | pedidos, margen neto tras ads | contratos firmados, leads con teléfono que contestan | el resultado que el plan prometía |
| Techo aritmético | cobertura de la BD | margen × conversión medida × tope del canal; límite de la audiencia; políticas de la plataforma | leads/día que la fuente puede dar × tasa de respuesta medida × capacidad de reuniones de el usuario | recursos × tiempo frente al objetivo |
| Techo de plataforma | API de un tercero | políticas de Meta Ads, límites de la API de Shopify, comisiones | Google Maps que bloquea, WhatsApp que limita, BORME sin teléfonos | dependencia de una decisión ajena |
| Banco de casos | consultas, logs | pedidos reales, sesiones, carritos abandonados, comentarios | leads reales con su resultado, conversaciones | decisiones pasadas y su resultado |
| Kill-test | replay en sombra | un test de una semana con presupuesto acotado, o una página nueva contra la vieja | 20 contactos por el camino nuevo frente a 20 por el viejo, mismo periodo | una decisión pequeña que confirme o tumbe la hipótesis |

Dos añadidos que en objetos no-código pesan más que en código:

- **Techo de plataforma**: el límite lo pone alguien de fuera y no se puede
  elevar. Dos salidas y solo dos: cambiar de plataforma o cambiar la promesa.
  Se declara con esas palabras.
- **Techo en el usuario**: la restricción es su atención repartida entre proyectos.
  Es un diagnóstico legítimo y a veces la recomendación honesta es congelar o
  cerrar el objeto examinado en favor de otro proyecto suyo con techo más alto.
  Se dice en portada, con la comparación.

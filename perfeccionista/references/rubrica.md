# Construcción de la rúbrica congelada

La rúbrica es el contrato de calidad: se escribe DESPUÉS del contrato y ANTES de
implementar, pasa una auditoría independiente (Fase 1 de SKILL.md) y no se toca
durante el bucle. Su función es que el 10.000 signifique algo concreto y
verificable, no "me parece que está bien".

## Reglas generales

- 6–8 dimensiones. Menos de 6 deja huecos; más de 8 diluye los pesos y encarece el
  jurado sin ganar señal.
- Pesos enteros que suman exactamente 100. Reparte según lo que importe en ESTE
  encargo (el contrato manda): en un bot de pagos, Seguridad pesa más que UX; en una
  landing, al revés.
- Cada dimensión define **qué es un 10 en términos que un juez pueda verificar con
  evidencia**. Prohibido lo difuso ("código limpio", "buena experiencia"): escribe
  qué miraría el juez y qué tendría que encontrar.
- Anota también 2–3 ejemplos de descuento típico por dimensión ("−1.000 si un caso
  límite del contrato no tiene test"), para calibrar a los jueces.
- Toda dimensión de la plantilla que elimines lleva su justificación escrita en la
  propia `rubrica.md` — el auditor independiente y la pasada de confirmación la
  revisarán.
- La definición de 10 sale de dos fuentes: lo que el usuario dijo que es un 10 para él
  (Fase 0) y el estándar profesional del tipo de entregable. Si el usuario pidió menos
  que el estándar profesional, el estándar gana — el contrato define el alcance,
  no la vara de calidad.

## Plantillas por tipo de entregable

Parte de la plantilla; si quitas o fusionas dimensiones, justifícalo por escrito y
reparte los pesos manteniendo 6–8 dimensiones y suma 100.

### Código / script / integración

| Dimensión | Peso orientativo | Un 10 significa |
|---|---|---|
| Funcionalidad vs contrato | 25 | Cada punto del contrato demostrado funcionando con evidencia ejecutada. |
| Corrección y tests | 20 | Suite de tests que pasa entera, cubre el camino feliz Y cada caso límite listado en el contrato; tests significativos, no de relleno. |
| Robustez | 15 | Entradas malformadas, errores de red/IO, condiciones de carrera aplicables: manejados y con test. Falla con mensaje útil, nunca en silencio. |
| Seguridad | 15 | Sin secretos hardcodeados, entradas saneadas, sin inyección (SQL/shell/plantillas), permisos mínimos, dependencias sin CVEs conocidas. |
| Calidad de código | 10 | Sigue las convenciones del proyecto, sin duplicación, nombres claros, sin código muerto, complejidad justificada. |
| Rendimiento | 5 | Sin cuellos evidentes (N+1, bucles O(n²) sobre datos grandes, sync donde debía ser async); medido si el contrato fija cifras. |
| Entrega y docs | 10 | Se puede instalar/ejecutar siguiendo solo el README u órdenes documentadas; configuración explicada; ejemplo de uso real. |

### Web / UI

| Dimensión | Peso orientativo | Un 10 significa |
|---|---|---|
| Flujos del contrato | 25 | Cada flujo navegado en real con Playwright, con captura; sin callejones sin salida. |
| Visual y marca | 20 | Consistente con la marca/diseño acordado; sin elementos rotos, solapes ni placeholder text. |
| Responsive | 15 | Verificada en móvil (390px), tablet y escritorio con capturas; nada roto ni cortado. |
| Robustez del front | 10 | Consola sin errores; estados vacíos/carga/error diseñados; formularios validan y comunican. |
| Accesibilidad | 10 | Contraste AA, alt en imágenes, navegable por teclado, labels en formularios. |
| SEO/metadatos | 10 | Title/description/og:image correctos por página; sin enlaces rotos (verificado). |
| Rendimiento | 10 | Imágenes optimizadas, sin assets gigantes; carga razonable medida. |

### Bot / automatización / servicio

Tabla completa (variante de "Código": Operabilidad absorbe Rendimiento, y Robustez
amplía con el ciclo de vida de errores; suma 100):

| Dimensión | Peso orientativo | Un 10 significa |
|---|---|---|
| Funcionalidad vs contrato | 25 | Cada punto del contrato demostrado funcionando con evidencia ejecutada. |
| Corrección y tests | 20 | Suite completa que pasa; cubre camino feliz y casos límite del contrato. |
| Robustez y ciclo de errores | 15 | Entradas malformadas manejadas; qué pasa si la API externa cae, si llega un mensaje inesperado, si se reinicia a mitad — probado, no supuesto. |
| Seguridad | 15 | Sin secretos hardcodeados, entradas saneadas, sin inyección, permisos mínimos. |
| Operabilidad | 15 | Autoarranque/reinicio configurado y probado (matar el proceso y verlo volver); logs útiles; sin cuellos de rendimiento evidentes; alertas si el contrato las pide. |
| Calidad de código | 5 | Convenciones del proyecto, sin duplicación ni código muerto. |
| Entrega y docs | 5 | Instalable/ejecutable siguiendo solo lo documentado; configuración explicada. |

### Documento / informe / diseño

| Dimensión | Peso orientativo | Un 10 significa |
|---|---|---|
| Contenido vs contrato | 25 | Cubre todo lo pedido, sin relleno. |
| Veracidad y fuentes | 10 | Cada afirmación factual contrastada con su fuente; nada inventado. |
| Estructura y claridad | 20 | Se entiende a la primera; orden lógico. |
| Formato final | 20 | Revisado RENDERIZADO (el PDF/DOCX/HTML final, no la fuente); sin desbordes, viudas, imágenes rotas. |
| Corrección lingüística | 15 | Sin faltas; registro e idioma acordados (castellano de España salvo contrato en contra). |
| Presentación | 10 | Tipografía/colores/portada al nivel acordado. |

## Auditoría de la rúbrica (Fase 1) — plantilla del auditor

Quien escribe la rúbrica es quien será puntuado con ella; por eso, antes de
congelarla, la audita un agente independiente usando la misma cadena de mecanismos
del jurado (`references/jurado.md`, Composición; en modo degradado, audita
releyendo contrato y plantilla desde disco y anótalo en `rubrica.md`). Su prompt es
esta plantilla **VERBATIM** (solo corchetes editables), y el prompt exacto y la
respuesta cruda se guardan como `auditoria-rubrica-prompt.md` y `-respuesta.md`
junto al contrato: **sin esos dos ficheros, la rúbrica NO está congelada** y el
bucle no puede avanzar. Si la auditoría tiene que correr en modo degradado, el
error literal de los mecanismos 1-3 se guarda junto al contrato como
`auditoria-rubrica-error-mecanismos.txt` (en Fase 1 aún no existe carpeta de
evidencia). Si el veredicto es "no-apta", aplica las objeciones y
reaudita. La pasada de confirmación verificará que estos ficheros existen y que el
prompt coincide con esta plantilla.

```
Eres un auditor externo de rúbricas de calidad, escéptico. No has participado en
este encargo y no le debes nada a quien redactó la rúbrica.

CONTRATO: [contenido de contrato.md]
RÚBRICA PROPUESTA: [contenido de rubrica.md]
PLANTILLA DE REFERENCIA: [plantilla del tipo de entregable, literal de references/rubrica.md]

Dictamina:
1. ¿Cada dimensión de la plantilla eliminada o fusionada tiene justificación
   escrita que se sostiene?
2. ¿Los pesos reflejan los riesgos reales del contrato (lo que más daño haría si
   fallara pesa más)?
3. ¿Cada definición de 10 está al nivel del estándar profesional o por encima, y
   es verificable con evidencia?
4. ¿Hay alguna dimensión redactada para ser alcanzable de serie (un 10 "gratis")?

Devuelve exactamente:
- VEREDICTO: apta | no-apta
- OBJECIONES: lista concreta y accionable (vacía solo si apta)
```

## Guía de verificación por tipo (Fase 3)

Qué significa "probar todo" antes de cada pasada de jurado. Toda salida se guarda
en `evidencia\vuelta-N\` con su cabecera de reproducción (comando exacto,
directorio, fecha-hora, exit code — formato en `references/estado.md`): evidencia
sin cabecera no existe para el jurado.

- **Código**: la suite del proyecto completa (no solo los tests nuevos), lint del
  proyecto, build si lo hay, y una ejecución real del programa con los casos del
  contrato. En Windows recuerda: PowerShell 5.1 (sin `&&`), rutas con `\`, cuidado
  con BOM/UTF-16 al escribir ficheros que leerá otra herramienta.
- **Web**: servidor levantado de verdad + navegación real de cada flujo. Orden de
  preferencia: skill webapp-testing → Playwright instalado por ti
  (`pip install playwright` + `python -m playwright install chromium` + script
  propio de navegación y captura) → último recurso, `Invoke-WebRequest`/`curl`
  para códigos de estado + inspección del HTML servido, dejando en
  `evidencia\vuelta-N\limitaciones.txt` qué NO pudiste comprobar visualmente (los
  jueces descontarán en consecuencia; eso es preferible a no verificar o a
  bloquearte). Consola y peticiones de red sin errores; capturas guardadas.
- **Integraciones**: llamada real por cada endpoint/flujo del contrato. Si tocar
  producción cuesta dinero o es irreversible, sandbox/dry-run con una línea factual
  de anotación en la evidencia — el juez decidirá si basta para un 10 según el
  contrato.
- **Bots/servicios**: arranca el servicio, mándale entradas reales, mátalo y
  comprueba que revive si el contrato exige autoarranque.
- **Documentos**: genera el formato final y LÉELO renderizado página a página.

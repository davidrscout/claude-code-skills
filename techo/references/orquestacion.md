# Orquestación — cómo se reparte una pasada completa entre subagentes

Regla: el criterio no se delega. Las Fases 0 (contrato), 1 (adjudicación), 3
(enunciado), 4 (parche campeón: diseño y juicio) y 7 (dictamen) las haces tú.
Se delega lo que se beneficia de contexto limpio y paralelismo: lectura y
medición (Fase 2), generación de candidatos (Fase 5) y el panel (Fase 6).

Todos los `agent()` llevan `model: 'opus'` (Fable solo en el hilo principal).
Los subagentes reciben rutas ABSOLUTAS, solo lectura, y NUNCA tu hipótesis.
Coste de referencia de una pasada completa: 4 lectores + 4 generadores + 2-3
panelistas = 10-11 subagentes. No lo infles: más agentes no es más rigor.

## Escalera de mecanismos

1. **Workflow**: la invocación de /techo por el usuario autoriza su uso. Esqueleto
   abajo. Si la herramienta no aparece en la sesión, no la pidas ni la simules.
2. **Agent**: varias llamadas en el mismo mensaje → paralelas. Mismos prompts.
3. **Solo (degradado)**: haces tú cada papel en secuencia con contexto
   contaminado. Se declara en el dictamen y un panel degradado nunca firma modo A.

## Anclas válidas por tipo de objeto

- Código: `fichero:línea`, comando con salida, consulta con resultado.
- Tienda: URL con fecha de consulta, id de producto/colección/campaña, versión
  fechada del theme, fila de un export (pedidos, sesiones) con su id.
- Proceso comercial: fila de CRM u hoja de leads con su id, plantilla fechada,
  conversación guardada citada por fecha.
- Plan o documento: versión fechada y sección.

## Esqueleto de Workflow (pasada completa, objeto de código)

Adáptalo: menos lectores si el objeto es pequeño. `RAIZ`, `ESTADO` (carpeta
`~/.claude/techo\<slug>\<fecha>\`) y `CONTRATO` (texto de
contrato.md) se pasan por `args`. Los patrones de búsqueda van con `rg -n`
(nunca `rg -E`, que en ripgrep es la codificación) o con la herramienta Grep.

```javascript
export const meta = {
  name: 'techo-pasada-completa',
  description: 'Lectores en paralelo → (tú: enunciado + campeón) → generadores de caminos → panel escéptico',
  phases: [
    { title: 'Lectura', detail: 'mapa de decisiones, arqueología, cuello, banco de casos' },
    { title: 'Caminos', detail: 'un generador por técnica' },
    { title: 'Panel', detail: 'conservador, verificador y (en modo A) contable' },
  ],
}

const { RAIZ, ESTADO, CONTRATO, FASE } = args   // FASE: 'lectura' | 'caminos' | 'panel'
const OPUS = { model: 'opus' }
const BASE = `Proyecto: ${RAIZ}. Carpeta de estado: ${ESTADO}. Solo lectura sobre el proyecto (consultas SELECT, nada de escribir fuera de ${ESTADO}). Ignora ficheros de credenciales (.env, secrets): no los leas ni los cites. Castellano de España. Devuelve SOLO el objeto pedido; cada afirmación con ancla: fichero:línea, o comando con su salida, o consulta con su resultado. Sin ancla no vale. No opines: mide y cita. Para buscar patrones usa la herramienta Grep o "rg -n" (nunca "rg -E").\n\nCONTRATO DEL EXAMEN:\n${CONTRATO}\n\n`

const ANCLA = { type: 'object', properties: { nivel: { type: 'string', enum: ['MEDIDO','LEIDO','INFERIDO','SIN_MEDIR'] }, ref: { type: 'string' }, salida: { type: 'string' } }, required: ['nivel','ref'] }

const LECTORES = [
  { key: 'mapa', prompt: 'Construye el MAPA DE DECISIONES del camino crítico por donde pasa el valor. En cada bifurcación (qué buscar, qué filtrar, qué hacer si no hay resultados, cuántos devolver, forma de la salida, a quién escribir, precio...) anota quién decide y el grado de cierre: 0 código fijo (if/regex/umbral), 1 lista o mapa estático en el código, 2 datos o configuración, 3 modelo o usuario con herramientas. Con fichero:línea y nº de ramas. Añade la tabla de supuestos fundacionales (5-15 decisiones del día 1 escritas como afirmación en presente, dónde están grabadas, qué sería posible si fuesen falsas). Inventaría también constantes con conocimiento del mundo (patrón: líneas que empiezan por un nombre en MAYÚSCULAS de 4+ letras seguido de = y { [ o ( ) con nº de entradas y su universo real, y heurísticas que deciden ramas (funciones def _is_/_wants_/_looks_like_/_seems_/_detect_/_should_/_has_ y regex sobre texto libre del usuario).',
    schema: { type: 'object', properties: {
      decisiones: { type: 'array', items: { type: 'object', properties: { decision: { type: 'string' }, grado: { type: 'integer' }, decisor: { type: 'string' }, ancla: { type: 'string' }, ramas: { type: 'integer' } }, required: ['decision','grado','decisor','ancla'] } },
      supuestos: { type: 'array', items: { type: 'object', properties: { afirmacion: { type: 'string' }, ancla: { type: 'string' }, si_fuese_falso: { type: 'string' } }, required: ['afirmacion','ancla','si_fuese_falso'] } },
      constantes_del_mundo: { type: 'array', items: { type: 'object', properties: { nombre: { type: 'string' }, ancla: { type: 'string' }, entradas: { type: 'integer' }, universo_real: { type: 'string' } }, required: ['nombre','ancla','entradas'] } },
      heuristicas: { type: 'array', items: { type: 'object', properties: { nombre: { type: 'string' }, ancla: { type: 'string' }, decide_rama: { type: 'boolean' } }, required: ['nombre','ancla','decide_rama'] } },
      formas_de_salida: { type: 'array', items: { type: 'string' } },
    }, required: ['decisiones','supuestos','constantes_del_mundo','heuristicas','formas_de_salida'] } },
  { key: 'arqueologia', prompt: 'Reconstruye la ARQUEOLOGÍA DE PARCHES sobre el camino crítico, agrupada por SÍNTOMA (no por bug). Con git si existe (git log -L, --numstat, -S); si no, con mtimes, carpetas paralelas (-fix, -v2, _Archivo), copias *.bak_* fechadas, comentarios con fecha ISO dentro del código (patrón 20[0-9]{2}-[0-9]{2}-[0-9]{2}), ficheros patch_*/repro_*, y las notas de memoria del proyecto en ~/.claude/projects/*/memory\\ como bitácora. Por cada parche: fecha, síntoma, dónde aterrizó (fichero:línea), si AÑADIÓ o QUITÓ una rama/lista/regex, si el síntoma reabrió, y cuánto tocó (ficheros/líneas) como precedente de coste. Señala explícitamente los puntos donde aterrizan 3+ parches de fechas y síntomas distintos. Añade ping-pongs (un parche corrigiendo a otro en < 30 días) y el coste del caso N+1 comparado con N y N-1 si se puede datar. Lista lo que el dueño ya intentó y descartó ("requiere reescribir", "fase 2", "algún día") y sus decisiones documentadas (vetos, direcciones).',
    schema: { type: 'object', properties: {
      metodo: { type: 'string' },
      parches: { type: 'array', items: { type: 'object', properties: { fecha: { type: 'string' }, sintoma: { type: 'string' }, ancla: { type: 'string' }, anade_o_quita: { type: 'string' }, reabrio: { type: 'string' }, coste_precedente: { type: 'string' }, fuente: { type: 'string' } }, required: ['fecha','sintoma','ancla','anade_o_quita','fuente'] } },
      puntos_recurrentes: { type: 'array', items: { type: 'object', properties: { ancla: { type: 'string' }, parches: { type: 'array', items: { type: 'string' } }, sintomas_distintos: { type: 'integer' } }, required: ['ancla','parches','sintomas_distintos'] } },
      ping_pongs: { type: 'array', items: { type: 'string' } },
      coste_caso_n: { type: 'string' },
      descartado_por_el_dueno: { type: 'array', items: { type: 'object', properties: { idea: { type: 'string' }, fuente: { type: 'string' }, motivo: { type: 'string' } }, required: ['idea','fuente'] } },
      decisiones_del_dueno: { type: 'array', items: { type: 'object', properties: { decision: { type: 'string' }, fuente: { type: 'string' } }, required: ['decision','fuente'] } },
    }, required: ['metodo','parches','puntos_recurrentes','ping_pongs','descartado_por_el_dueno','decisiones_del_dueno'] } },
  { key: 'cuello', prompt: 'Mide el EMBUDO y el volumen real para adjudicar el cuello, SOLO con caminos de lectura ya construidos en el proyecto (copias locales de BD con SELECT, ficheros de estado, logs, informes, scripts de lectura propios del proyecto). NO extraigas claves ni llames a APIs de pago. Cada cifra con su comando o consulta y su salida. Cubre: cuántos usos/consultas/pedidos/leads reales y en qué ventana; frescura y cobertura de la fuente de datos; límites de plataforma de terceros que aparezcan en código o notas (rate limits, políticas, APIs rotas); capacidad ya construida y sin uso; el objetivo declarado del dueño si aparece en notas o memoria (cifra y fecha, con fuente). Marca SIN_MEDIR lo que no puedas con el comando que lo mediría. No interpretes: cifras.',
    schema: { type: 'object', properties: {
      embudo: { type: 'array', items: { type: 'object', properties: { escalon: { type: 'string' }, valor: { type: 'string' }, ancla: ANCLA }, required: ['escalon','valor','ancla'] } },
      volumen_real: { type: 'string' },
      objetivo_declarado: { type: 'string' },
      dato: { type: 'array', items: { type: 'object', properties: { fuente: { type: 'string' }, frescura: { type: 'string' }, cobertura: { type: 'string' }, ancla: ANCLA }, required: ['fuente','ancla'] } },
      limites_de_plataforma: { type: 'array', items: { type: 'object', properties: { limite: { type: 'string' }, ancla: { type: 'string' } }, required: ['limite','ancla'] } },
      capacidad_sin_uso: { type: 'array', items: { type: 'object', properties: { que: { type: 'string' }, ancla: { type: 'string' }, uso_medido: { type: 'string' } }, required: ['que','ancla'] } },
      sin_medir: { type: 'array', items: { type: 'string' } },
    }, required: ['embudo','volumen_real','objetivo_declarado','dato','limites_de_plataforma','capacidad_sin_uso','sin_medir'] } },
  { key: 'banco', prompt: `Construye el BANCO DE CASOS REALES: 10-20 casos sacados del propio proyecto (consultas guardadas, peticiones con cero resultados, pedidos, leads, tickets, notas), con al menos 5 de los que hoy fallan. ANONIMÍZALOS (sustituye nombres, teléfonos, correos, ids de cliente por marcadores) y escríbelos en ${ESTADO}\\banco_casos\\banco.jsonl, un JSON por línea con: id, origen (fichero/tabla/nota), peticion, resultado_actual, esperado_si_se_sabe, falla_hoy (true/false). Devuelve el recuento y de dónde salieron. Si no hay artefactos reales suficientes, devuelve los que haya y di cuántos faltan: NUNCA inventes casos.`,
    schema: { type: 'object', properties: { ruta: { type: 'string' }, total: { type: 'integer' }, fallan_hoy: { type: 'integer' }, origenes: { type: 'array', items: { type: 'string' } }, faltan: { type: 'string' }, anonimizado: { type: 'boolean' } }, required: ['ruta','total','fallan_hoy','origenes','anonimizado'] } },
]

if (FASE === 'lectura') {
  phase('Lectura')
  const lect = await parallel(LECTORES.map(l => () => agent(BASE + l.prompt, { ...OPUS, label: `lee:${l.key}`, phase: 'Lectura', schema: l.schema })))
  const out = {}; LECTORES.forEach((l, i) => { out[l.key] = lect[i] })
  log(`lectura: ${Object.values(out).filter(Boolean).length}/${LECTORES.length} lectores`)
  return out
}

if (FASE === 'caminos') {
  // args.SUPUESTOS, args.MAPA_RESUMEN, args.ARQUEO_RESUMEN, args.INVARIANTE, args.CAMPEON_RESULTADO, args.BANCO, args.DESCARTADOS, args.DECISIONES_DUENO (hechos y rutas, no tu veredicto)
  const TECNICAS = [
    ['negar', 'NEGAR EL SUPUESTO: coge cada supuesto fundacional, niégalo, y diseña el sistema MÍNIMO que funcionaría con la negación (quién decide, qué herramientas, qué límites, qué código deja de hacer falta). Si el resultado se parece a "dale herramientas al modelo", di en qué se diferencia este objeto de un chat con pipeline cerrado y qué evidencia propia lo sostiene.'],
    ['borrar', 'BORRAR EN VEZ DE AÑADIR: elige el componente que genera más parches y diseña el sistema sin él. Además, dibuja el flujo del dato capa por capa y marca dónde se destruye información irrecuperable; propón eliminar las capas que solo traducen o clasifican.'],
    ['insumo', 'BAJAR EL TECHO AL INSUMO (camino NO técnico obligatorio): comprueba con conteos reales si con el dato disponible el mejor algoritmo posible tampoco llegaría; si es así, el camino es de datos, alcance, promesa, precio o canal. Sus "casos que mata" son casos REALES del banco que hoy no se sirven, citados por id, no fichero:línea.'],
    ['rescate', 'RESCATAR LO ARCHIVADO E INVENTARIAR ACTIVOS: reevalúa con coste derivado de precedentes las ideas que el dueño aparcó (lista dada) y los activos ya construidos sin uso; busca el cambio de diseño que mataría cinco pendientes de golpe. Si propones algo parecido a un intento anterior, di qué es distinto ahora.'],
  ]
  // "subir de grado" y "cambiar unidad/frontera" las aplicas tú como checklist sobre el mapa; no hacen falta agentes.
  const FICHA = { type: 'object', properties: { caminos: { type: 'array', items: { type: 'object', properties: {
    nombre: { type: 'string' }, tesis: { type: 'string' }, invariante_que_rompe: { type: 'string' },
    casos_que_mata: { type: 'array', items: { type: 'object', properties: { ancla: { type: 'string' }, que: { type: 'string' }, por_que_deja_de_hacer_falta: { type: 'string' } }, required: ['ancla','que','por_que_deja_de_hacer_falta'] } },
    techo_nuevo: { type: 'string' }, proximo_techo: { type: 'string' }, perdidas_dia_1: { type: 'array', items: { type: 'string' } },
    kill_test: { type: 'object', properties: { protocolo: { type: 'string' }, umbral_de_fallo: { type: 'string' }, duracion_sesiones: { type: 'string' } }, required: ['protocolo','umbral_de_fallo','duracion_sesiones'] },
    seam: { type: 'string' }, convivencia_y_vuelta_atras: { type: 'string' }, que_muere_y_cuando: { type: 'string' },
    coste_sesiones: { type: 'string' }, coste_precedente: { type: 'string' }, coste_eur_mes: { type: 'string' }, coste_dos_sistemas: { type: 'string' },
    dependencias_externas: { type: 'array', items: { type: 'string' } }, contradice_decision_del_dueno: { type: 'string' },
    que_lo_mataria: { type: 'string' }, es_tecnico: { type: 'boolean' },
  }, required: ['nombre','tesis','invariante_que_rompe','casos_que_mata','techo_nuevo','proximo_techo','perdidas_dia_1','kill_test','seam','convivencia_y_vuelta_atras','coste_sesiones','coste_precedente','que_lo_mataria','es_tecnico'] } } }, required: ['caminos'] }
  phase('Caminos')
  const gens = await parallel(TECNICAS.map(([k, t]) => () => agent(
    `${BASE}Genera 1-3 CAMINOS ALTERNATIVOS con UNA técnica: ${t}\n\nPROHIBIDO proponer "reescribir todo" o justificar un camino por su tecnología: entra por los casos especiales concretos que mata (mínimo 5, con ancla) y por su kill-test de menos de una sesión (3 h de trabajo del dueño) con umbral escrito antes. Cada camino con su próximo techo, lo que se pierde el día 1, y el coste en sesiones DERIVADO de un precedente citado (sin precedente: SIN MEDIR). Contexto (hechos, no veredicto):\nSUPUESTOS: ${args.SUPUESTOS}\nMAPA: ${args.MAPA_RESUMEN}\nARQUEOLOGÍA: ${args.ARQUEO_RESUMEN}\nINVARIANTE ENUNCIADO: ${args.INVARIANTE}\nRESULTADO DEL PARCHE CAMPEÓN: ${args.CAMPEON_RESULTADO}\nBANCO DE CASOS: ${args.BANCO}\nDESCARTADO POR EL DUEÑO: ${args.DESCARTADOS}\nDECISIONES DOCUMENTADAS DEL DUEÑO: ${args.DECISIONES_DUENO}`,
    { ...OPUS, label: `camino:${k}`, phase: 'Caminos', schema: FICHA })))
  const caminos = gens.filter(Boolean).flatMap(g => g.caminos)
  log(`caminos: ${caminos.length} candidatos de ${gens.filter(Boolean).length}/${TECNICAS.length} técnicas`)
  return { caminos }
}

if (FASE === 'panel') {
  // args.PROMPT_VERIFICADOR siempre; args.PROMPT_CONSERVADOR (null en modo D); args.PROMPT_CONTABLE (null si el modo provisional no es de la familia A)
  phase('Panel')
  const tareas = [() => agent(args.PROMPT_VERIFICADOR, { ...OPUS, label: 'panel:verificador', phase: 'Panel' })]
  if (args.PROMPT_CONSERVADOR) tareas.push(() => agent(args.PROMPT_CONSERVADOR, { ...OPUS, label: 'panel:conservador', phase: 'Panel' }))
  if (args.PROMPT_CONTABLE) tareas.push(() => agent(args.PROMPT_CONTABLE, { ...OPUS, label: 'panel:contable', phase: 'Panel' }))
  const [verificador, conservador, contable] = await parallel(tareas)
  return { verificador, conservador: conservador || null, contable: contable || null }
}
```

Se lanza tres veces (una por `FASE`), porque entre lectura y caminos van tus
Fases 3 y 4 (enunciado, aritmética, campeón), y entre caminos y panel va tu
criba. Guarda cada resultado crudo en `ESTADO\evidencia\workflow_<fase>.json`
y las respuestas del panel en `ESTADO\panel\`. El Verificador se lanza
siempre; el Conservador salvo en D; el Contable solo en la familia A.

## Variante para objetos que no son código

Mismos cuatro lectores, con el encargo traducido con la tabla de
`senales.md` (sección "Equivalencias"). Prompts de sustitución:

- **mapa**: "Construye el mapa de decisiones del camino crítico <visita →
  producto → carrito → pago | fuente de leads → contacto → reunión → contrato>:
  en cada punto, quién decide (una lista fija, una colección o regla automática,
  una heurística, el dato de ventas/respuesta, el dueño a mano) con su ancla
  (URL con fecha, id de colección/campaña/plantilla, fila de export con id).
  Supuestos fundacionales del negocio escritos como afirmación."
- **arqueología**: "Reconstruye la historia de intervenciones: versiones y
  temas, campañas creadas y pausadas con fechas, cambios de precio y oferta,
  plantillas y guiones fechados, apps instaladas y quitadas, y las notas de
  memoria del proyecto. Agrupa por síntoma (qué se intentaba arreglar) y marca
  los puntos donde aterrizan 3+ intentos distintos."
- **cuello**: igual, con embudo de negocio (sesiones → carrito → pedido;
  leads → contestan → reunión → contrato) desde exports y ficheros del proyecto.
- **banco**: pedidos, sesiones, carritos abandonados, leads con su resultado,
  conversaciones; anonimizados.

Las técnicas de caminos son las mismas; el camino "no técnico" suele ser aquí
el principal y sus casos que mata son filas del banco.

## Pasada rápida con Agent (sin Workflow)

Tres llamadas `Agent` en el mismo mensaje, `model: "opus"`: `mapa`,
`arqueologia`, `cuello` con los mismos prompts. Tú haces el test del parche en
seco y emites `VEREDICTO PROVISIONAL (pasada rápida)`. Sin panel, sin campeón:
nunca modo A y nunca `NOTA_TECHO.md`.

## Si un subagente cae por el filtro de seguridad

Reformula una vez con tono neutro (sin listas de palabras tipo
contraseña/clave/token; el proyecto puede tener ficheros de credenciales:
indícale que los ignore). Nunca insistas igual dos veces.

# Caminos — cómo se genera el otro camino, cómo se juzga y cómo se migra

Solo se entra aquí si el techo sobrevivió al parche campeón (Fase 4). Un camino
no es una idea: es una ficha completa con su kill-test. Sin ficha, no existe.

## Técnicas generativas

Cada técnica produce candidatos crudos, sin filtrar por coste todavía. La criba
viene después. Ninguna técnica puede proponer "reescribir todo". En la pasada
completa, cuatro van a subagentes en contexto limpio (1 negar, 3 borrar, 5
insumo, 6+7 rescate y activos); las demás (2 subir de grado, 4 unidad y
frontera, 8 pendientes) las aplicas tú como checklist sobre el mapa que ya
tienes: no necesitan un agente.

**Seam**: un punto de extensión que YA existe en el sistema (registro de
fuentes, blueprint, tabla, flag, ruta nueva) por donde lo nuevo entra sin
tocar lo viejo. Un camino sin seam no tiene plan de convivencia.

1. **Negar el supuesto.** Coge cada supuesto fundacional de la Fase 2, escrito
   como afirmación en presente, y niégalo. Diseña el sistema MÍNIMO que
   funcionaría con la negación: quién decide ahora, qué herramientas necesita,
   qué límites duros lleva, qué código deja de hacer falta. el proyecto de referencia (un SaaS con chat de IA): "el código
   decide el flujo y el modelo rellena huecos" → negado → "el modelo decide y
   actúa con herramientas; el código pone límites".
2. **Subir de grado las decisiones más parcheadas.** Con el mapa de decisiones,
   proponer subir UN escalón (0→1→2→3) cada punto de decisión que acumula
   parches, y contar cuánto código muere. No todo debe subir: se justifica punto
   por punto, y también se baja de grado lo que el modelo hace mal (dinero,
   permisos, límites de coste).
3. **Borrar en vez de añadir.** Elige el componente que genera la mayor parte
   de los parches y pregunta qué necesitaría el sistema si ese componente no
   existiera. No se pide una alternativa mejor: se pide diseñar sin él. Si el
   resultado es más simple y cubre más casos, ese componente era el techo.
   Variante: dibuja el flujo del dato capa por capa y marca dónde se destruye
   información irrecuperable (un clasificador de intención que colapsa la
   petición en 5 clases; una traducción que pierde el matiz). Las capas que
   solo traducen o clasifican para que la siguiente entienda son candidatas a
   desaparecer.
4. **Cambiar la unidad de entrega o la frontera.** Qué entrega hoy (una
   respuesta, un informe, un producto, un lead) y tres unidades alternativas
   (un conjunto navegable, un flujo continuo, una suscripción a avisos, un
   espacio que el usuario explora). Y la frontera: meter dentro algo externo
   (los datos del cliente, un canal) o sacar fuera algo interno que cuesta más
   de lo que aporta (un scraper frágil, una traducción propia).
5. **Bajar el techo al insumo.** Si con el dato disponible el mejor algoritmo
   posible tampoco daría la respuesta, el camino no es de software: es de
   datos, de alcance o de promesa. Se comprueba con conteos reales. Este es el
   camino "no técnico" que la criba exige.
6. **Rescatar lo archivado por el usuario.** Rastrea memoria, informes viejos,
   TODOs y comentarios buscando "requiere reescribir", "demasiado grande",
   "fase 2", "algún día", "pendiente trocear", y reevalúa esas ideas con coste
   medido. El camino bueno suele estar ya escrito y aparcado precisamente
   porque era caro (la integración documentada estaba documentado desde junio con prototipo).
   Si se propone algo parecido a un intento anterior, hay que decir qué es
   distinto ahora.
7. **Inventario de activos infrautilizados.** Tablas, endpoints, modelos,
   datos históricos, integraciones ya construidos, cruzados con su uso real.
   El camino más barato casi siempre recombina activos existentes. Cada activo
   se puntúa por si sirve al cliente objetivo, no por existir.
8. **Arqueología invertida de pendientes.** Reúne todos los "known issues" y
   backlogs y busca el cambio de diseño que mataría CINCO de golpe. Un cambio
   que cierra un pendiente es un parche; uno que cierra media lista es un
   camino.

Técnicas que NO se usan como generadores con voto propio (producen narrativa
plausible sin evidencia y alimentan el sesgo a reescribir): "la hoja en blanco"
(cómo lo haría hoy un competidor desde cero), "en qué negocio estás realmente",
entrevistas imaginarias, "los usuarios quieren". Como mucho sirven para
sugerir candidatos que luego tienen que pasar la ficha completa.

## Ficha obligatoria de camino

```
## Camino <n>: <nombre en 5 palabras>
Tesis (una frase): ...
Invariante que rompe: <cuál de los supuestos de la Fase 2 deja de ser cierto>
Casos especiales que MATA (mínimo 5, o es un parche disfrazado):
  - <ancla> <qué> — por qué deja de hacer falta
  - ...
  Ancla admitida: fichero:línea (constante, función, rama) en caminos de
  código; en caminos de dato / promesa / precio / canal, cada caso es una
  petición, pedido o lead REAL del banco que hoy no se sirve, citado por su id
  en banco_casos\banco.jsonl. Un camino no técnico se juzga por casos del
  banco, no por anclas de código.
Techo nuevo: qué permite que hoy es imposible, calculado con el MISMO método
  que el techo viejo (misma consulta, mismo denominador). Efecto esperado sobre
  la métrica-rey y por qué mecanismo concreto.
Próximo techo: contra qué chocará este camino cuando funcione, y cuándo.
Lo que se pierde el día 1: capacidades que hoy salen gratis y el camino nuevo
  no cubre (coste acotado por petición, latencia previsible, reproducibilidad,
  casos límite ya resueltos, control determinista). Cómo se acota cada una.
Kill-test (< 1 sesión = unas 3 h de el usuario): el experimento que puede MATARLO,
  no confirmarlo.
  Banco: <ruta a banco_casos\, 10-20 casos reales anonimizados>
  Protocolo: replay en sombra del camino nuevo contra el viejo sobre el banco
  Umbral de fallo escrito ANTES: "si <métrica> < <valor>, el camino muere"
  Resultado: <ejecutado: cifra | trazado en seco (INFERIDO): por qué | no ejecutado: por qué>
Seam de convivencia: el punto de extensión que YA existe por donde entra lo
  nuevo (registro de fuentes, blueprint, tabla, flag, ruta nueva). Cómo conviven
  viejo y nuevo (flag por usuario, porcentaje de tráfico, ruta paralela).
  Métrica de paridad para avanzar de fase. Punto de no retorno. Vuelta atrás
  en minutos. Qué ficheros mueren y en qué fase.
Coste: rango de sesiones de el usuario (solo, manteniendo lo demás) DERIVADO de un
  precedente citado ("el parche X tocó N ficheros y llevó M sesiones según
  <nota fechada>"), etiquetado INFERIDO; sin precedente, SIN MEDIR y se dice
  qué lo mediría. Desglosado por fase, con la primera fase que aporta valor
  por sí sola. €/mes recurrentes solo con página de precios o factura citada;
  si no, SIN MEDIR. Coste de mantener DOS sistemas durante la convivencia, y
  a partir de qué duración esa carga hace inviable el camino aunque sea
  correcto.
Coste de oportunidad: qué pasaría si esas sesiones fueran a vender o a otro
  proyecto de el usuario.
Dependencias fuera de control: datos que no tienes, proveedores, permisos,
  aprobaciones de plataforma, clientes que aún no existen.
Coherencia con decisiones documentadas de el usuario: <ninguna contradicción | contradice X, y por qué se propone igual>
Qué lo mataría: la condición falsable que, si se cumple, lo descarta.
Confianza: alta/media/baja, con motivo.
```

## Criba

1. Un camino sin kill-test ejecutable en menos de una sesión NO entra en los
   tres: va a "Descartados" con la etiqueta "sin kill-test". Es fe, no camino.
2. Un camino sin seam de convivencia (no puede correr en paralelo con lo que
   hoy cobra y revertirse en minutos) NO entra en los tres: va a "Descartados
   — no ejecutable ahora" con la condición que lo haría ejecutable.
3. Descarta todo camino que no mate al menos cinco casos citados: anclas de
   código para caminos de código, ids del banco para caminos no técnicos.
4. Descarta todo camino que se justifique por su tecnología (agentes, IA,
   microservicios, otro lenguaje) y no por los parches que mata.
5. De los que quedan, máximo tres, al menos uno no técnico. Ordena por: casos
   que mata × techo nuevo ÷ coste, y tiempo hasta la primera señal real (días
   hasta saber si va bien, no días hasta "terminado").
6. Uno recomendado. Si el kill-test del recomendado cabe en la pasada, se
   ejecuta y su cifra va en el dictamen.

## Plan de convivencia (strangler) para el recomendado

Nunca big bang: un dev solo con clientes de pago no lo aguanta, y un plan sin
fecha de muerte del código viejo deja dos sistemas que mantener, que es peor
que el techo original.

```
Fase 1 (valor propio, < N sesiones): entra lo nuevo por el seam <X> para el
  <segmento acotado: un tipo de petición, un nicho, un % de tráfico>.
  Métrica de paridad: <la misma que el kill-test, sobre tráfico real>.
  Vuelta atrás: <flag/ruta>, minutos.
Fase 2: amplía a <segmento>. Muere: <ficheros/constantes>. Punto de no retorno: <cuál>.
Fase 3: lo viejo se apaga. Muere: <resto>. Se archiva: <copia>.
Lista de congelación durante la migración: <parches y mejoras del camino viejo
  que NO se hacen, para pagar el cambio con las horas que hoy se van al parcheo>.
Criterio de abandono escrito: <qué resultado concreto en Fase 1 obliga a parar y volver>.
```

## Palancas (modo B)

Cuando no hay techo, el dictamen entrega máximo tres palancas ordenadas por
efecto sobre la métrica-rey. Cada una: mecanismo en tres pasos, evidencia del
proyecto que la sostiene, efecto esperado con su nivel de evidencia, y
etiqueta **palanca** (mueve la métrica) o **higiene** (arregla, no mueve). La
higiene va aparte y corta. Y siempre: el umbral y la fecha que reabrirían el
modo A ("si tras estas tres palancas el síntoma <X> reaparece, hay techo").

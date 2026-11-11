CÓMO DELEGAR CON EL CENTRO IA (instrucciones que este MCP da al agente que lo usa; edítalas a tu gusto)

PAPELES
- Tú (el agente de esta sesión) = el orquestador: decides, troceas, repartes, integras, revisas y hablas con el usuario.
- Trabajadores = tus propios subagentes (Agent en Claude Code, subagent en OpenCode) Y las demás IAs que este MCP lanza por su CLI o su API (otras cuentas de Claude Code, Codex, Kimi, OpenCode, Experiential Labs).
- Advisor = el agente `estratega` con el modelo que mejor razona: para las decisiones que cambian el resultado. No se le pasan resúmenes: lee él la conversación volcada (conversacion.py), el código y los datos. auto:pensar sirve para pensar sin leer ficheros.

CRITERIO: CALIDAD, NO SOLO AHORRO
- Delega en otra IA cuando sea MEJOR en ese tipo de tarea, para tener una segunda mirada distinta o para paralelizar mucho volumen.
- Las cadenas auto:<tipo> van ordenadas por calidad esperada y se reordenan solas con las notas que pongas (ia_valorar). Si una IA no rinde en algo, baja; si otra sorprende, sube.
- Las cadenas de serie son un punto de partida genérico. Para medir de verdad qué IA va mejor en tu equipo, usa calibrar.py (ver README).

CÓMO DELEGAR
1. ias_estado: cupos, saldo de API, modelos gratis ahora y el ranking de cada auto:<tipo>.
2. ia_delegar con motor «auto:<tipo>». Si un motor falla (sin cupo, límite, error, timeout, respuesta vacía) pasa solo al siguiente; si fallan todos, te lo devuelve y lo haces tú.
3. Motor concreto: pasa también «tipo» para que cuente en el aprendizaje; respaldo:["motor|modelo", ...] para tus propios respaldos.
4. Subtareas independientes → en paralelo (esperar=false + ia_resultado).
5. Prompt autocontenido: objetivo, rutas absolutas, criterio de éxito medible y qué devolver. Las otras IAs no ven esta conversación.
6. Revisa lo entregado y llama SIEMPRE a ia_valorar (id del trabajo, nota 1-5, comentario corto). Así aprende el reparto.

¿LO HAGO YO O DELEGO?
- Tú: lo pequeño, lo que depende del contexto de esta conversación, las decisiones, integrar y revisar, y lo que sea más rápido hacer que explicar.
- Tus subagentes: trabajo que necesita las herramientas o los MCP de esta sesión, o leer y buscar mucho en el disco.
- Otras IAs: cuando son mejores en ese tipo, para una segunda opinión independiente o para paralelizar volumen.
- Tiempo de arranque orientativo: API (exp:*) 2-5 s; CLIs agénticas 5-20 s.

REGLAS
- Una cuenta con «solo_para» en config.json solo se usa para eso.
- Los modelos de pago por API solo para lo que lo merezca y mientras haya saldo; las cadenas los quitan solas por debajo de 0,05 $.
- Verifica tú (tests, ficheros, salida real) antes de dar algo por hecho. En piezas delicadas (dinero, datos, seguridad, borrados, publicar hacia fuera) la única revisión extra es la del estratega.
- Si otra IA ya trabaja en una carpeta, no le metas trabajo encima ahí.
- Al terminar, dile al usuario qué motor hizo cada parte, cuánto tardó, qué nota le pusiste y si costó algo.

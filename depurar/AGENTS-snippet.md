## Depuración y calidad de código

- No cambies código para arreglar un fallo hasta poder escribir la causa con evidencia: `fichero:línea — qué pasa — valor observado vs esperado`.
- Reproduce primero el fallo con un comando (test, script mínimo u orden exacta) y ejecútalo tú; no pidas al usuario que te pegue errores que puedes ver ejecutando.
- El error se ve donde explota, pero suele nacer antes: rastrea el valor malo hacia atrás (¿quién lo creó?, ¿quién lo pasó?) y arregla en el origen.
- Hipótesis → comprobación barata (print/log/assert en las fronteras, marcado `DEBUG-TMP`) → dato real. Sin dato, no hay causa.
- Arreglo mínimo. Prohibido: try/except que se traga el error, defaults que lo esconden, `if` especial para el caso que falla, `type: ignore`/`any`, desactivar tests.
- Tras cada edición: lint + tipos sobre los ficheros tocados. Antes de decir "hecho": ejecuta la reproducción, lint, tipos y tests, y quita los `DEBUG-TMP`.
- 3 intentos fallidos con la misma idea → para, relee el error completo y amplía el rastreo. "Antes iba" → `git diff` contra la última versión buena o `git bisect run`.
- No inventes APIs: comprueba nombres y firmas en el código instalado antes de usarlas.
- Informe final: Síntoma / Causa (fichero:línea + evidencia) / Arreglo / Verificación (comandos y resultado) / Pendiente.

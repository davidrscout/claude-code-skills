---
name: depurar
description: Método para arreglar errores encontrando la CAUSA con evidencia, no el síntoma, y para no meter fallos tontos al escribir código. Úsala SIEMPRE que haya un bug, error, excepción, traceback, crash, test que falla, salida incorrecta, regresión ("antes iba"), "no funciona", "da error", o cuando vayas a dar por terminado código que has escrito o cambiado. Use for any bug, error, exception, stack trace, failing test, wrong output, crash or regression, and before declaring code done.
---

# Depurar

**Regla de oro: no cambies código hasta poder escribir la causa con evidencia (fichero:línea + valor real observado).**

Tú ejecutas el bucle completo (reproducir → leer → investigar → arreglar → verificar). No le pidas al usuario que ejecute cosas y te pegue el error si puedes ejecutarlas tú.

Responde en el idioma del usuario.

---

## 0. Herramientas del proyecto (una vez por proyecto)

Mira qué usa el proyecto (`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `Makefile`, CI) y usa ESO. No instales herramientas nuevas sin preguntar.

| Lenguaje | Lint | Tipos / compilación | Tests |
|---|---|---|---|
| Python | `ruff check` | `pyright` o `mypy` (si no hay: `python -m py_compile f.py`) | `pytest -x -q` |
| JS / TS | `eslint` | `tsc --noEmit` (JS sin TS: `node --check f.js`) | `vitest run` / `jest` / `npm test` |
| Go | `go vet ./...` | `go build ./...` | `go test ./...` |
| Rust | `cargo clippy` | `cargo check` | `cargo test` |
| Shell | `shellcheck` | `bash -n f.sh` | — |

Apunta los comandos que funcionan; los vas a repetir mucho.

---

## Cuando hay un fallo: 8 pasos, en orden

### 1. Reproducir
- Consigue UN comando que muestre el fallo: el test que falla, un script mínimo, o la orden exacta del usuario.
- Ejecútalo y guarda la salida COMPLETA.
- Si no se reproduce: no adivines un arreglo. Busca qué es distinto (datos de entrada, entorno, variables, versión, orden de ejecución) y consigue reproducirlo o reúne logs.

### 2. Leer el error entero
- El traceback se lee de abajo arriba: abajo está DÓNDE PETÓ, no dónde nació el problema.
- Anota: tipo de error, mensaje literal, y el primer marco que es código del proyecto (no de librerías).
- Abre ese fichero y lee la función entera, no solo la línea.
- Si hay varios errores, el primero suele causar los demás. Empieza por el primero.

### 3. Rastrear hacia atrás hasta el origen
El fallo casi nunca está donde explota. Para el valor malo pregúntate: **¿quién lo creó y quién me lo pasó?** Sigue la cadena llamante → llamado con búsqueda (`grep -rn`) hasta el punto donde el valor deja de ser correcto.

En cada frontera comprueba lo típico:
- `None` / `undefined` / vacío / lista sin elementos
- tipo distinto (str vs int, bytes vs str, dict vs objeto, promesa sin `await`)
- índices y rangos (off-by-one), claves que no existen
- unidades, zonas horarias, codificación, separadores de ruta
- estado viejo: caché, variable global, fichero de una ejecución anterior
- configuración / variables de entorno / versión de librería distinta a la que crees
- la firma real de la API (mírala en el código instalado o con `help()`; no la supongas)

### 4. Hipótesis y comprobación barata
- Escribe 1–3 hipótesis ordenadas por probabilidad.
- Para cada una, una comprobación BARATA que la confirme o la descarte: un `print`/log, un `assert`, una línea en el REPL, un test pequeño.
- Pon la instrumentación temporal en las FRONTERAS (lo que entra y sale de cada función implicada), no solo donde peta. Márcala con `DEBUG-TMP` para quitarla luego.
- Ejecuta y mira los valores reales. Una hipótesis sin dato que la apoye no cuenta.

### 5. Causa demostrada
Escríbela en una línea antes de tocar nada:

> **Causa:** `ruta/fichero.py:123` — qué pasa — evidencia: valor observado `X` cuando se esperaba `Y`.

Si no puedes rellenar la evidencia, vuelve al paso 4.

### 6. Arreglo mínimo, en el origen
- Arregla donde NACE el problema (paso 3), no donde explota.
- Cambio mínimo. Nada de reescribir el módulo ni refactorizar de paso.
- Busca el mismo patrón en el resto del código (`grep`) y arregla los hermanos.
- Prohibido como "arreglo": `try/except` que se traga el error, valores por defecto que lo esconden, `if` especial para la entrada que falla, `# type: ignore` / `any` / `@ts-ignore`, desactivar o borrar el test.

### 7. Verificar
- Vuelve a ejecutar el comando del paso 1: ahora tiene que pasar.
- Pasa lint + tipos + tests del proyecto (paso 0).
- Quita toda la instrumentación `DEBUG-TMP` (búscala con grep).
- Si hay suite de tests, añade un test que reproduzca este fallo para que no vuelva.

### 8. Informar
```
Síntoma:      qué fallaba (error literal)
Causa:        fichero:línea — por qué — evidencia
Arreglo:      qué cambié y dónde
Verificación: comandos ejecutados y su resultado
Pendiente:    riesgos o cosas que no pude comprobar (o "nada")
```

---

## Límites del bucle
- Si llevas **3 intentos** fallidos con la misma idea, PARA: vuelve al paso 2, relee todo y amplía el rastreo. Seguir probando variantes de lo mismo no funciona.
- Tras **~5 iteraciones** sin causa demostrada, informa al usuario con lo que sabes (qué descartaste y con qué evidencia) y qué necesitas.
- **"Antes funcionaba"**: compara con la última versión buena (`git log`, `git diff <commit_bueno>`). Si no es obvio: `git bisect start; git bisect bad; git bisect good <commit>; git bisect run <comando_del_paso_1>`.

---

## Al escribir o cambiar código (prevención)
Así se evitan los fallos tontos antes de que existan:
1. **Pasos pequeños.** Cambia poco, ejecuta, sigue.
2. **Lint + tipos tras CADA edición** sobre los ficheros tocados. Arregla lo que salga antes de seguir.
3. **No inventes APIs.** Si dudas de un nombre, firma o parámetro, compruébalo en el código instalado o en la ayuda antes de usarlo.
4. **Valida en las fronteras** (entrada del usuario, respuestas de APIs, ficheros, variables de entorno) y falla con un mensaje claro que diga qué valor llegó.
5. **Ejecútalo de verdad** antes de decir que funciona. "Debería funcionar" no es verificar.
6. Si hay git, **commit cuando algo funciona**: es tu punto de vuelta.

## Antipatrones (no hacer nunca)
- Cambiar código "a ver si" sin hipótesis.
- Arreglar varias cosas a la vez (no sabrás cuál funcionó).
- Silenciar errores o warnings para que "pase".
- Dar algo por arreglado sin ejecutarlo.
- Pedir al usuario que haga de mensajero de errores que puedes ver tú.
- Reescribir desde cero algo que tiene un bug localizado.

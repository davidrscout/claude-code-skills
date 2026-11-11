"""Centro IA: núcleo del MCP (mcp_ias.py). EXPERIMENTAL: ver README.md.

Motores (id → qué lanza):
  claude:<cuenta>      Claude Code en esa cuenta (config.json)        agéntico
  codex                Codex CLI (cuenta de ChatGPT)                  agéntico
  kimi                 Kimi Code CLI                                  agéntico
  opencode:<prov/mod>  OpenCode con ese modelo                        agéntico
  exp:<modelo>         Experiential Labs por API (solo texto)         rápido

Todo lo que se ejecuta deja eventos en datos/trabajos/<id>.jsonl y una línea en
datos/historial.jsonl. Ningún token sale de este proceso.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / 'datos'
TRABAJOS = DATOS / 'trabajos'
ACTIVOS = DATOS / 'activos'
PROMPTS = DATOS / 'prompts'
HISTORIAL = DATOS / 'historial.jsonl'
ALERTAS = DATOS / 'alertas.jsonl'
GRATIS = DATOS / 'gratis.json'
CACHE_USO = DATOS / 'cache_uso.json'
for _d in (DATOS, TRABAJOS, ACTIVOS, PROMPTS):
    _d.mkdir(parents=True, exist_ok=True)

HOME = Path.home()
CUENTAS_JSON = HOME / '.claude-cuentas' / 'cuentas.json'
EXP_BASE = 'https://api.experientiallabs.ai/v1'
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0

CONFIG_DEFECTO = {
    # Cuentas de Claude Code. Sin esta clave se usa ~/.claude-cuentas/cuentas.json si existe
    # (formato de claude-multicuenta) y, si no, una sola cuenta «principal» en ~/.claude.
    'cuentas_claude': [],
    # Cadenas auto:<tipo> propias: {"tipo": ["motor|modelo", ...]}. Sustituyen a las de serie.
    'cadenas': {},
    # Tipos de tarea extra o descripciones propias: {"tipo": "descripción"}.
    'tipos': {},
    'claude_modelos': ['claude-opus-5-5', 'claude-sonnet-5-5', 'claude-haiku-5-5'],
    'codex_modelos': [],
    'exp_vigilar': [],
    'sondeo_horas': 3,
    'renovar_tokens_auto': True,
    'timeout_agentico_min': 30,
    'timeout_exp_min': 5,
    # Comando opcional para avisos (cambios en los modelos gratis): se le añaden título y mensaje.
    'aviso_comando': [],
    'trabajo_dir': str(HOME / 'centro-ia-trabajo'),
}


def config() -> dict:
    c = dict(CONFIG_DEFECTO)
    f = RAIZ / 'config.json'
    if f.exists():
        try:
            c.update(json.loads(f.read_text(encoding='utf-8')))
        except Exception:
            pass
    return c


def ahora() -> float:
    return time.time()


def iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts or time.time()).isoformat(timespec='seconds')


def leer_json(p: Path, defecto=None):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return defecto


_lock_ficheros = threading.Lock()


def escribir_json(p: Path, datos) -> None:
    tmp = p.with_suffix(p.suffix + '.tmp')
    with _lock_ficheros:
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(tmp, p)


def anexar(p: Path, registro: dict) -> None:
    with _lock_ficheros:
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')


def variable_usuario(nombre: str) -> str:
    v = os.environ.get(nombre, '')
    if v:
        return v
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            return str(winreg.QueryValueEx(k, nombre)[0])
    except Exception:
        return ''


def http_json(url: str, cabeceras: dict, cuerpo: dict | None = None, timeout: int = 30):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    h = {'User-Agent': 'centro-ia/1.0', **cabeceras}
    if datos is not None:
        h['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=datos, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def matar_arbol(pid: int) -> None:
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True,
                           creationflags=CREATE_NO_WINDOW, timeout=20)
        else:
            import signal
            os.kill(pid, signal.SIGTERM)
    except Exception:
        pass


def avisar(titulo: str, mensaje: str) -> None:
    cmd = config().get('aviso_comando') or []
    if not cmd:
        return
    try:
        subprocess.Popen([*cmd, titulo, mensaje], creationflags=CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ───────────────────────── cuentas de Claude ─────────────────────────

def cuentas_claude() -> list[dict]:
    """Cuentas de Claude Code: las de config.json; si no hay, las de ~/.claude-cuentas/cuentas.json;
    si tampoco, una sola cuenta «principal» con la configuración normal (~/.claude)."""
    c = config()
    out = []
    lista = c.get('cuentas_claude') or []
    if lista:
        for x in lista:
            d = os.path.expanduser(x.get('dir') or '~/.claude')
            normal = os.path.normcase(os.path.abspath(d)) == os.path.normcase(str(HOME / '.claude'))
            out.append({'id': x['id'], 'nombre': x['id'], 'alias': x.get('alias') or [],
                        'etiqueta': x.get('etiqueta', ''), 'dir': d, 'normal': normal,
                        'solo_para': x.get('solo_para', '')})
        return out
    d = leer_json(CUENTAS_JSON, {}) or {}
    for x in d.get('cuentas', []):
        carp = x.get('carpeta', x['nombre'])
        directorio = HOME / '.claude' if carp == '' else HOME / '.claude-cuentas' / carp
        alias = x.get('alias') or []
        out.append({'id': alias[0] if alias else x['nombre'], 'nombre': x['nombre'], 'alias': alias,
                    'etiqueta': x.get('etiqueta', ''), 'dir': str(directorio), 'normal': carp == '',
                    'solo_para': x.get('solo_para', '')})
    if not out:
        out.append({'id': 'principal', 'nombre': 'principal', 'alias': [], 'etiqueta': 'Claude Code',
                    'dir': str(HOME / '.claude'), 'normal': True, 'solo_para': ''})
    return out


def cuenta_claude(ident: str) -> dict | None:
    for c in cuentas_claude():
        if ident in (c['id'], c['nombre'], *c['alias']):
            return c
    return None


def entorno_claude(cuenta: dict) -> dict:
    env = dict(os.environ)
    env.pop('CLAUDE_CONFIG_DIR', None)
    env.pop('CLAUDECODE', None)
    env.pop('CLAUDE_CODE_ENTRYPOINT', None)
    if not cuenta['normal']:
        env['CLAUDE_CONFIG_DIR'] = cuenta['dir']
    return env


_ultimo_renovar: dict[str, float] = {}


def renovar_token(motor: str, forzar: bool = False) -> str:
    """Los tokens OAuth caducan cada ~8 h y los renueva el propio CLI al usarse.
    Lanzamos una llamada mínima (Haiku / modelo rápido) en segundo plano para que lo haga."""
    if not forzar and ahora() - _ultimo_renovar.get(motor, 0) < 1200:
        return 'esperando (renovación reciente)'
    _ultimo_renovar[motor] = ahora()

    def correr():
        try:
            if motor.startswith('claude:'):
                cu = cuenta_claude(motor.split(':', 1)[1])
                if not cu:
                    return
                subprocess.run([shutil.which('claude') or 'claude', '-p', 'Responde solo: ok', '--model', 'claude-haiku-5-5'],
                               env=entorno_claude(cu), capture_output=True, timeout=180, stdin=subprocess.DEVNULL,
                               cwd=tempfile.gettempdir(), creationflags=CREATE_NO_WINDOW)
            elif motor == 'kimi':
                subprocess.run([shutil.which('kimi') or 'kimi', '-p', 'Responde solo: ok', '-m', 'kimi-code/kimi-for-coding-highspeed'],
                               capture_output=True, timeout=180, stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir(),
                               creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass
        borrar_cache_uso()

    threading.Thread(target=correr, daemon=True).start()
    return 'renovando'


# ───────────────────────── uso / cupos ─────────────────────────

def _limite(nombre, porcentaje, reinicio, extra=None):
    d = {'nombre': nombre, 'pct': None if porcentaje is None else round(float(porcentaje), 1), 'reinicio': reinicio}
    if extra:
        d.update(extra)
    return d


def uso_claude(cu: dict) -> dict:
    r = {'motor': f"claude:{cu['id']}", 'tipo': 'claude', 'cuenta': cu['id'], 'etiqueta': cu['etiqueta'],
         'solo_para': cu['solo_para'], 'limites': []}
    cred = leer_json(Path(cu['dir']) / '.credentials.json', {}) or {}
    o = cred.get('claudeAiOauth') or {}
    r['plan'] = f"{o.get('subscriptionType', '?')} · {o.get('rateLimitTier', '').replace('default_', '')}"
    if not o.get('accessToken'):
        r['estado'] = 'sin sesión'
        return r
    if o.get('expiresAt', 0) / 1000 < ahora() + 60:
        r['estado'] = 'token caducado'
        if config().get('renovar_tokens_auto'):
            r['renovacion'] = renovar_token(r['motor'])
        return r
    try:
        u = http_json('https://api.anthropic.com/api/oauth/usage',
                      {'Authorization': 'Bearer ' + o['accessToken'], 'anthropic-beta': 'oauth-2025-04-20'})
    except urllib.error.HTTPError as e:
        r['estado'] = f'error {e.code}'
        return r
    except Exception as e:
        r['estado'] = f'error: {e}'
        return r
    nombres = {'five_hour': 'Sesión 5 h', 'seven_day': 'Semanal', 'seven_day_opus': 'Semanal Opus',
               'seven_day_sonnet': 'Semanal Sonnet'}
    for k, n in nombres.items():
        v = u.get(k)
        if v and v.get('utilization') is not None:
            r['limites'].append(_limite(n, v['utilization'], v.get('resets_at')))
    ex = u.get('extra_usage') or {}
    r['extra'] = 'activado' if ex.get('is_enabled') else 'desactivado'
    r['estado'] = 'ok'
    return r


def uso_codex() -> dict:
    r = {'motor': 'codex', 'tipo': 'codex', 'etiqueta': 'ChatGPT · Codex CLI', 'limites': []}
    ficheros = sorted(glob.glob(str(HOME / '.codex' / 'sessions' / '*' / '*' / '*' / 'rollout-*.jsonl')),
                      key=os.path.getmtime, reverse=True)[:8]
    for f in ficheros:
        try:
            with open(f, 'rb') as fh:
                fh.seek(0, 2)
                tam = fh.tell()
                fh.seek(max(0, tam - 400_000))
                texto = fh.read().decode('utf-8', 'replace')
        except Exception:
            continue
        lineas = [l for l in texto.splitlines() if '"rate_limits"' in l]
        if not lineas:
            continue
        try:
            ev = json.loads(lineas[-1])
        except Exception:
            m = re.search(r'"rate_limits":(\{.*?"plan_type":"[^"]*"[^}]*\})', lineas[-1])
            if not m:
                continue
            ev = {'payload': {'rate_limits': json.loads(m.group(1))}}
        rl = _buscar_clave(ev, 'rate_limits') or {}
        r['plan'] = rl.get('plan_type') or '?'
        for clave, nombre in (('primary', 'Principal'), ('secondary', 'Secundario')):
            v = rl.get(clave)
            if v:
                minutos = v.get('window_minutes') or 0
                ventana = f'{minutos // 1440} días' if minutos >= 1440 else f'{minutos // 60} h'
                reinicio = v.get('resets_at')
                r['limites'].append(_limite(f'{nombre} ({ventana})', v.get('used_percent'),
                                            iso(reinicio) if isinstance(reinicio, (int, float)) else reinicio))
        cr = rl.get('credits') or {}
        if cr.get('has_credits'):
            r['creditos'] = cr.get('balance')
        r['dato_de'] = iso(os.path.getmtime(f))
        r['estado'] = 'ok'
        return r
    r['estado'] = 'sin datos (aún no se ha usado Codex)'
    return r


def _buscar_clave(obj, clave):
    if isinstance(obj, dict):
        if clave in obj:
            return obj[clave]
        for v in obj.values():
            x = _buscar_clave(v, clave)
            if x is not None:
                return x
    elif isinstance(obj, list):
        for v in obj:
            x = _buscar_clave(v, clave)
            if x is not None:
                return x
    return None


def codex_modelos() -> list[str]:
    """Modelos que ofrece la cuenta de ChatGPT conectada a Codex (cambia si se hace codex login con otra cuenta)."""
    d = leer_json(HOME / '.codex' / 'models_cache.json')
    ms = d.get('models') if isinstance(d, dict) else d
    return [m.get('slug') for m in (ms or []) if isinstance(m, dict) and m.get('visibility') == 'list' and m.get('slug')]


def uso_kimi() -> dict:
    r = {'motor': 'kimi', 'tipo': 'kimi', 'etiqueta': 'Kimi Code', 'limites': []}
    creds = glob.glob(str(HOME / '.kimi-code' / 'credentials' / '*.json'))
    if not creds:
        r['estado'] = 'sin sesión'
        return r
    d = leer_json(Path(creds[0]), {}) or {}
    exp = d.get('expires_at', 0)
    exp = exp / 1000 if exp > 1e11 else exp
    if exp < ahora() + 60:
        # el token de Kimi dura 15 min: no se renueva solo (gastaría cupo); se usa la última lectura buena
        r['estado'] = 'token caducado'
        return r
    try:
        u = http_json('https://api.kimi.ai/coding/v1/usages',
                      {'Authorization': 'Bearer ' + d['access_token'], 'User-Agent': 'KimiCLI/2.4.1'})
    except Exception as e:
        r['estado'] = f'error: {e}'
        return r
    us = u.get('usages') or {}
    for k, n in (('limit_5h', 'Sesión 5 h'), ('limit_month_total', 'Mes (total)'), ('limit_month_code', 'Mes (código)')):
        v = us.get(k)
        if v:
            r['limites'].append(_limite(n, (v.get('used_ratio') or 0) * 100, v.get('reset_time')))
    tc = leer_toml_simple(HOME / '.kimi-code' / 'config.toml')
    r['plan'] = 'suscripción · ' + (tc.get('default_model', '').split('/')[-1] or '?')
    r['estado'] = 'ok'
    return r


def leer_toml_simple(p: Path) -> dict:
    out = {'modelos': []}
    try:
        for linea in p.read_text(encoding='utf-8').splitlines():
            m = re.match(r'^default_model\s*=\s*"([^"]+)"', linea)
            if m:
                out['default_model'] = m.group(1)
            m = re.match(r'^\[models\."([^"]+)"\]', linea)
            if m:
                out['modelos'].append(m.group(1))
    except Exception:
        pass
    return out


def uso_apis() -> list[dict]:
    """Saldo y gasto de las APIs de pago (Experiential y fal.ai). Caché de 5 min."""
    f = DATOS / 'cache_apis.json'
    c = leer_json(f)
    if c and ahora() - c.get('ts', 0) < 300:
        return c['apis']
    out = []
    k = variable_usuario('EXPLABS_API_KEY')
    if k:
        r = {'id': 'experiential', 'nombre': 'Experiential Labs', 'estado': 'ok'}
        h = {'Authorization': 'Bearer ' + k}
        try:
            cr = http_json('https://api.experientiallabs.ai/api/v1/credits', h)['data']
            r['cargado'] = round(cr.get('total_credits') or 0, 2)
            r['gastado'] = round(cr.get('total_usage') or 0, 4)
            r['saldo'] = round(r['cargado'] - r['gastado'], 4)
        except Exception as e:
            r['estado'] = f'error: {e}'
        try:
            kd = http_json('https://api.experientiallabs.ai/api/v1/key', h)['data']
            r['clave'] = {'nombre': kd.get('label'), 'hoy': kd.get('usage_daily'), 'semana': kd.get('usage_weekly'),
                          'mes': kd.get('usage_monthly'), 'limite': kd.get('limit')}
        except Exception:
            pass
        try:
            act = http_json('https://api.experientiallabs.ai/api/v1/activity', h)['data']
            hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            por = {}
            for a in act:
                if a.get('date') != hoy:
                    continue
                d = por.setdefault(a['model'], {'modelo': a['model'], 'peticiones': 0, 'coste': 0.0})
                d['peticiones'] += a.get('requests') or 0
                d['coste'] += a.get('usage') or 0
            r['hoy_modelos'] = sorted(por.values(), key=lambda x: (-x['coste'], -x['peticiones']))[:8]
        except Exception:
            pass
        # /credits no descuenta las reservas: si hace poco una llamada de pago dio insufficient_credits, está bloqueado
        for h in historial(800):
            if ahora() - h.get('inicio', 0) > 12 * 3600:
                break
            if 'insufficient_credits' in (h.get('error') or ''):
                r['bloqueado'] = True
                m = re.search(r'after reservations:\s*(-?[\d.]+)', h['error'])
                r['tras_reservas'] = float(m.group(1)) if m else None
                break
        out.append(r)
    kf = variable_usuario('FAL_KEY')
    if kf:
        r = {'id': 'fal', 'nombre': 'fal.ai', 'estado': 'ok'}
        try:
            req = urllib.request.Request('https://rest.alpha.fal.ai/billing/user_balance',
                                         headers={'Authorization': 'Key ' + kf, 'User-Agent': 'centro-ia/1.0'})
            with urllib.request.urlopen(req, timeout=20) as x:
                r['saldo'] = round(float(x.read().decode().strip()), 4)
        except Exception as e:
            r['estado'] = f'error: {e}'
        out.append(r)
    escribir_json(f, {'ts': ahora(), 'apis': out})
    return out


def borrar_cache_uso() -> None:
    try:
        CACHE_USO.unlink()
    except Exception:
        pass


def uso_todo(forzar: bool = False) -> dict:
    cache = leer_json(CACHE_USO)
    if cache and not forzar and ahora() - cache.get('ts', 0) < 90:
        return cache
    resultados = []
    hilos = []

    def con(fn, *a):
        try:
            resultados.append(fn(*a))
        except Exception as e:
            resultados.append({'motor': getattr(fn, '__name__', '?'), 'estado': f'error: {e}', 'limites': []})

    for cu in cuentas_claude():
        hilos.append(threading.Thread(target=con, args=(uso_claude, cu)))
    hilos.append(threading.Thread(target=con, args=(uso_codex,)))
    hilos.append(threading.Thread(target=con, args=(uso_kimi,)))
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(40)
    orden = [f"claude:{c['id']}" for c in cuentas_claude()] + ['codex', 'kimi']
    resultados.sort(key=lambda x: orden.index(x['motor']) if x.get('motor') in orden else 99)
    # si una cuenta no se puede leer ahora, se enseña su última lectura buena con la hora
    f_ult = DATOS / 'ultimo_uso.json'
    ult = leer_json(f_ult, {}) or {}
    for r in resultados:
        m = r.get('motor')
        if r.get('estado') == 'ok' and r.get('limites'):
            ult[m] = {'ts': ahora(), 'limites': r['limites'], 'plan': r.get('plan')}
        elif m in ult and not r.get('limites'):
            r['limites'] = ult[m]['limites']
            r['plan'] = r.get('plan') or ult[m].get('plan')
            r['dato_de'] = iso(ult[m]['ts'])
    escribir_json(f_ult, ult)
    datos = {'ts': ahora(), 'cuentas': resultados}
    escribir_json(CACHE_USO, datos)
    return datos


# ───────────────────────── modelos gratis (sondeo) ─────────────────────────

_lock_sondeo = threading.Lock()
SONDEO_ESTADO = {'activo': False, 'que': '', 'progreso': ''}


def exp_modelos(forzar: bool = False) -> list[dict]:
    f = DATOS / 'exp_modelos.json'
    d = leer_json(f)
    if d and not forzar and ahora() - d.get('ts', 0) < 6 * 3600:
        return d['modelos']
    k = variable_usuario('EXPLABS_API_KEY')
    if not k:
        return (d or {}).get('modelos', [])
    try:
        ms = http_json(EXP_BASE + '/models', {'Authorization': 'Bearer ' + k})['data']
    except Exception:
        return (d or {}).get('modelos', [])
    out = []
    for m in ms:
        p = m.get('pricing') or {}
        nano = 1e9

        def precio(clave):
            v = p.get(clave)
            return None if v is None else round(v / nano, 4)
        out.append({'id': m['id'], 'contexto': m.get('context_window_tokens'),
                    'salida_max': m.get('maximum_output_tokens'),
                    'entrada_usd_m': precio('input_nano_usd_per_million_tokens'),
                    'salida_usd_m': precio('output_nano_usd_per_million_tokens'),
                    'herramientas': m.get('supports_tools'), 'imagenes': m.get('supports_image_generation'),
                    'chat': m.get('supports_completions') is not False and not m.get('supports_embeddings')})
    escribir_json(f, {'ts': ahora(), 'modelos': out})
    return out


def sondear_exp(modelo: str, clave: str) -> dict:
    t = ahora()
    try:
        r = http_json(EXP_BASE + '/chat/completions', {'Authorization': 'Bearer ' + clave},
                      {'model': modelo, 'messages': [{'role': 'user', 'content': 'Responde solo: ok'}], 'max_tokens': 16},
                      timeout=90)
        coste = (r.get('usage') or {}).get('cost')
        if coste is None:
            return {'estado': 'desconocido', 'coste': None, 'seg': round(ahora() - t, 1)}
        return {'estado': 'gratis' if coste == 0 else 'pago', 'coste': coste, 'seg': round(ahora() - t, 1)}
    except urllib.error.HTTPError as e:
        cuerpo = e.read()[:300].decode('utf-8', 'replace')
        sin_saldo = e.code == 402 or re.search(r'insufficient|balance|credit|saldo', cuerpo, re.I)
        return {'estado': 'sin saldo' if sin_saldo else 'error', 'error': f'{e.code} {cuerpo}'[:200],
                'seg': round(ahora() - t, 1)}
    except Exception as e:
        return {'estado': 'error', 'error': str(e)[:200], 'seg': round(ahora() - t, 1)}


def opencode_modelos(forzar: bool = False) -> list[str]:
    f = DATOS / 'opencode_modelos.json'
    d = leer_json(f)
    if d and not forzar and ahora() - d.get('ts', 0) < 12 * 3600:
        return d['modelos']
    try:
        p = subprocess.run([shutil.which('opencode') or 'opencode', 'models'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=90, stdin=subprocess.DEVNULL,
                           creationflags=CREATE_NO_WINDOW)
        ms = [l.strip() for l in p.stdout.splitlines() if '/' in l and ' ' not in l.strip()]
    except Exception:
        ms = (d or {}).get('modelos', [])
    if ms:
        escribir_json(f, {'ts': ahora(), 'modelos': ms})
    return ms


def opencode_gratis_lista() -> list[str]:
    return [m for m in opencode_modelos() if m.startswith('opencode/') and (m.endswith('-free') or m == 'opencode/big-pickle')]


def sondear_opencode(modelo: str) -> dict:
    t = ahora()
    res = {'estado': 'error', 'seg': 0}
    with tempfile.TemporaryDirectory() as d:
        cmd = [shutil.which('opencode') or 'opencode', 'run', '--print-logs', '--log-level', 'warn',
               '--format', 'json', '--title', 'sondeo', '-m', modelo, 'Responde solo: ok']
        p = subprocess.Popen(cmd, cwd=d, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             creationflags=CREATE_NO_WINDOW)
        hecho = threading.Event()

        def leer_err():
            for linea in iter(p.stderr.readline, b''):
                s = linea.decode('utf-8', 'replace')
                if 'stream error' in s or 'level=ERROR' in s:
                    m = re.search(r'error\.error="([^"]+)"', s)
                    msg = m.group(1) if m else s.strip()[-200:]
                    res.update(estado='agotado' if 'limit' in msg.lower() else 'error', error=msg[:200])
                    hecho.set()
                    return

        def leer_out():
            for linea in iter(p.stdout.readline, b''):
                try:
                    ev = json.loads(linea)
                except Exception:
                    continue
                if ev.get('type') == 'text':
                    res.update(estado='gratis')
                if ev.get('type') == 'step_finish':
                    res['coste'] = (ev.get('part') or {}).get('cost')
                    hecho.set()
                    return
                if ev.get('type') == 'error':
                    res.update(estado='error', error=json.dumps(ev.get('error'))[:200])
                    hecho.set()
                    return
            hecho.set()

        threading.Thread(target=leer_err, daemon=True).start()
        threading.Thread(target=leer_out, daemon=True).start()
        if not hecho.wait(75):
            res.update(estado='error', error='sin respuesta en 75 s')
        if p.poll() is None:
            matar_arbol(p.pid)
    res['seg'] = round(ahora() - t, 1)
    return res


def sondear(que: str = 'todo', completo: bool = False) -> dict:
    """Comprueba qué modelos son gratis AHORA. que: exp | opencode | todo."""
    if not _lock_sondeo.acquire(blocking=False):
        return {'ok': False, 'motivo': 'ya hay un sondeo en marcha'}
    try:
        SONDEO_ESTADO.update(activo=True, que=que)
        g = leer_json(GRATIS, {}) or {}
        antes = {**{f'exp:{k}': v.get('estado') for k, v in (g.get('exp') or {}).items()},
                 **{f'opencode:{k}': v.get('estado') for k, v in (g.get('opencode') or {}).items()}}
        if que in ('exp', 'todo'):
            clave = variable_usuario('EXPLABS_API_KEY')
            if clave:
                ms = exp_modelos(forzar=completo)
                if completo:
                    lista = [m['id'] for m in ms if m.get('chat')]
                else:
                    ids = {m['id'] for m in ms}
                    lista = [m for m in config()['exp_vigilar'] if m in ids or not ids]
                exp = dict(g.get('exp') or {})
                hechos = [0]

                def uno(mid):
                    r = sondear_exp(mid, clave)
                    r['ts'] = ahora()
                    exp[mid] = r
                    hechos[0] += 1
                    SONDEO_ESTADO['progreso'] = f'Experiential {hechos[0]}/{len(lista)}'
                # 6 en paralelo
                for i in range(0, len(lista), 6):
                    hs = [threading.Thread(target=uno, args=(m,)) for m in lista[i:i + 6]]
                    [h.start() for h in hs]
                    [h.join(120) for h in hs]
                g['exp'] = exp
                g['exp_ts'] = ahora()
                sincronizar_opencode_exp([m for m, v in exp.items() if v.get('estado') == 'gratis'])
        if que in ('opencode', 'todo'):
            oc = dict(g.get('opencode') or {})
            lista = opencode_gratis_lista()
            for i, m in enumerate(lista):
                SONDEO_ESTADO['progreso'] = f'OpenCode {i + 1}/{len(lista)}'
                r = sondear_opencode(m)
                r['ts'] = ahora()
                oc[m] = r
            g['opencode'] = oc
            g['opencode_ts'] = ahora()
        escribir_json(GRATIS, g)
        # cambios gratis ↔ pago → alerta
        despues = {**{f'exp:{k}': v.get('estado') for k, v in (g.get('exp') or {}).items()},
                   **{f'opencode:{k}': v.get('estado') for k, v in (g.get('opencode') or {}).items()}}
        cambios = []
        for k, v in despues.items():
            a = antes.get(k)
            if a and a != v and 'gratis' in (a, v):
                cambios.append(f'{k}: {a} → {v}')
        if cambios:
            for c in cambios:
                anexar(ALERTAS, {'ts': ahora(), 'texto': c})
            avisar('Centro IA: cambian los gratis', '; '.join(cambios)[:400])
        return {'ok': True, 'cambios': cambios}
    finally:
        SONDEO_ESTADO.update(activo=False, progreso='')
        _lock_sondeo.release()


def sincronizar_opencode_exp(gratis: list[str]) -> None:
    """Mete en la config de OpenCode los modelos de Experiential que estén gratis, para usarlos en modo agente."""
    f = HOME / '.config' / 'opencode' / 'opencode.json'
    if not f.exists() or not gratis:
        return
    try:
        d = json.loads(f.read_text(encoding='utf-8'))
    except Exception:
        return
    prov = (d.get('provider') or {}).get('experiential')
    if not prov:
        return
    modelos = prov.setdefault('models', {})
    info = {m['id']: m for m in exp_modelos()}
    nuevos = [g for g in gratis if g not in modelos]
    if not nuevos:
        return
    copia = HOME / '.config' / 'opencode' / 'backups' / f'opencode.json.centro-ia_{datetime.now():%Y%m%d_%H%M%S}'
    copia.parent.mkdir(exist_ok=True)
    shutil.copy2(f, copia)
    for g in nuevos:
        i = info.get(g, {})
        modelos[g] = {'name': f'{g} (gratis)', 'limit': {'context': i.get('contexto') or 200000,
                                                        'output': i.get('salida_max') or 32000}}
    f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    opencode_modelos(forzar=True)


def gratis_ahora() -> dict:
    g = leer_json(GRATIS, {}) or {}
    return {
        'exp': sorted([k for k, v in (g.get('exp') or {}).items() if v.get('estado') == 'gratis']),
        'opencode': sorted([k for k, v in (g.get('opencode') or {}).items() if v.get('estado') == 'gratis']),
        'detalle': g,
        'sondeo': dict(SONDEO_ESTADO),
    }


# ───────────────────────── catálogo de motores ─────────────────────────

def motores() -> list[dict]:
    c = config()
    out = []
    for cu in cuentas_claude():
        out.append({'id': f"claude:{cu['id']}", 'grupo': 'Claude', 'nombre': f"Claude · {cu['id']}",
                    'detalle': cu['etiqueta'], 'modelos': c['claude_modelos'], 'agentico': True,
                    'solo_para': cu['solo_para']})
    out.append({'id': 'codex', 'grupo': 'ChatGPT', 'nombre': 'Codex (ChatGPT)', 'detalle': 'Codex CLI, agéntico',
                'modelos': codex_modelos() or c['codex_modelos'], 'agentico': True})
    tk = leer_toml_simple(HOME / '.kimi-code' / 'config.toml')
    out.append({'id': 'kimi', 'grupo': 'Kimi', 'nombre': 'Kimi Code', 'detalle': 'Kimi Code CLI, agéntico',
                'modelos': tk.get('modelos', []), 'modelo_defecto': tk.get('default_model'), 'agentico': True})
    g = gratis_ahora()
    for m in opencode_gratis_lista():
        out.append({'id': f'opencode:{m}', 'grupo': 'OpenCode gratis', 'nombre': m.split('/', 1)[1],
                    'detalle': 'OpenCode, agéntico', 'agentico': True,
                    'estado': ((g['detalle'].get('opencode') or {}).get(m) or {}).get('estado', 'sin sondear')})
    for m in g['exp']:
        out.append({'id': f'opencode:experiential/{m}', 'grupo': 'OpenCode + Experiential gratis',
                    'nombre': m, 'detalle': 'OpenCode con modelo gratis de Experiential, agéntico', 'agentico': True,
                    'estado': 'gratis'})
    for m in exp_modelos():
        if not m.get('chat'):
            continue
        est = ((g['detalle'].get('exp') or {}).get(m['id']) or {}).get('estado', '')
        out.append({'id': f"exp:{m['id']}", 'grupo': 'Experiential (API, solo texto)', 'nombre': m['id'],
                    'detalle': f"{m.get('entrada_usd_m')}/{m.get('salida_usd_m')} $/M", 'agentico': False,
                    'estado': est or 'sin sondear'})
    return out


# ───────────────────────── trabajos ─────────────────────────

_procesos: dict[str, subprocess.Popen] = {}


class Trabajo:
    def __init__(self, motor: str, prompt: str, modelo: str = '', cwd: str = '', origen: str = 'web',
                 padre: str = '', extra_args: list[str] | None = None, sistema: str = '', timeout_min: float | None = None,
                 tipo: str = ''):
        self.id = datetime.now().strftime('%m%d-%H%M%S-') + uuid.uuid4().hex[:4]
        self.motor = motor
        self.prompt = prompt
        self.modelo = modelo or ''
        self.modelo_pedido = modelo or ''
        self.tipo = tipo
        self.cwd = cwd or ''
        self.origen = origen
        self.padre = padre
        self.extra = extra_args or []
        self.sistema = sistema
        self.inicio = ahora()
        self.texto: list[str] = []
        self.coste = None
        self.tokens = {}
        self.estado = 'en curso'
        self.error = ''
        self.fichero = TRABAJOS / f'{self.id}.jsonl'
        self.hecho = threading.Event()
        agentico = not motor.startswith('exp:')
        c = config()
        self.timeout = 60 * (timeout_min or (c['timeout_agentico_min'] if agentico else c['timeout_exp_min']))

    # eventos
    def ev(self, tipo: str, **kw):
        anexar(self.fichero, {'t': round(ahora() - self.inicio, 2), 'tipo': tipo, **kw})

    def meta(self) -> dict:
        return {'id': self.id, 'motor': self.motor, 'modelo': self.modelo, 'origen': self.origen,
                'padre': self.padre, 'cwd': self.cwd, 'prompt': self.prompt[:600], 'inicio': self.inicio,
                'tarea_tipo': self.tipo, 'modelo_pedido': self.modelo_pedido}

    def lanzar(self) -> 'Trabajo':
        escribir_json(ACTIVOS / f'{self.id}.json', {**self.meta(), 'pid': os.getpid()})
        self.ev('inicio', **self.meta())
        threading.Thread(target=self._correr, daemon=True).start()
        return self

    def _correr(self):
        try:
            if self.motor.startswith('exp:'):
                self._exp()
            else:
                self._cli()
        except Exception as e:
            self.estado, self.error = 'error', str(e)
        finally:
            self._cerrar()

    def _cerrar(self):
        seg = round(ahora() - self.inicio, 1)
        respuesta = ''.join(self.texto).strip()
        if self.estado == 'en curso':
            self.estado = 'ok' if respuesta else 'error'
            if not respuesta and not self.error:
                self.error = 'sin respuesta'
        self.ev('fin', estado=self.estado, error=self.error, segundos=seg, coste=self.coste, tokens=self.tokens,
                respuesta=respuesta)
        anexar(HISTORIAL, {**self.meta(), 'fin': ahora(), 'segundos': seg, 'estado': self.estado, 'error': self.error[:500],
                           'coste': self.coste, 'tokens': self.tokens, 'respuesta': respuesta[:3000]})
        try:
            (ACTIVOS / f'{self.id}.json').unlink()
        except Exception:
            pass
        _procesos.pop(self.id, None)
        self.hecho.set()

    def resultado(self) -> dict:
        return {'id': self.id, 'motor': self.motor, 'modelo': self.modelo, 'estado': self.estado, 'error': self.error,
                'segundos': round(ahora() - self.inicio, 1), 'coste': self.coste, 'tokens': self.tokens,
                'respuesta': ''.join(self.texto).strip()}

    # ── Experiential por API (streaming) ──
    def _exp(self):
        modelo = self.motor.split(':', 1)[1]
        clave = variable_usuario('EXPLABS_API_KEY')
        msgs = []
        if self.sistema:
            msgs.append({'role': 'system', 'content': self.sistema})
        msgs.append({'role': 'user', 'content': self.prompt})
        cuerpo = json.dumps({'model': modelo, 'messages': msgs, 'stream': True,
                             'stream_options': {'include_usage': True}}).encode()
        req = urllib.request.Request(EXP_BASE + '/chat/completions', data=cuerpo, headers={
            'Authorization': 'Bearer ' + clave, 'Content-Type': 'application/json', 'User-Agent': 'centro-ia/1.0'})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                for linea in r:
                    s = linea.decode('utf-8', 'replace').strip()
                    if not s.startswith('data:'):
                        continue
                    s = s[5:].strip()
                    if s == '[DONE]':
                        break
                    try:
                        ch = json.loads(s)
                    except Exception:
                        continue
                    for c in ch.get('choices') or []:
                        t = (c.get('delta') or {}).get('content')
                        if t:
                            self.texto.append(t)
                            self.ev('texto', texto=t)
                    if ch.get('usage'):
                        u = ch['usage']
                        self.coste = u.get('cost')
                        self.tokens = {'entrada': u.get('prompt_tokens'), 'salida': u.get('completion_tokens')}
        except urllib.error.HTTPError as e:
            self.estado, self.error = 'error', f"{e.code} {e.read()[:300].decode('utf-8', 'replace')}"
            self.ev('error', texto=self.error)

    # ── CLIs agénticos ──
    def _prompt_cli(self) -> str:
        p = self.prompt
        if self.sistema:
            p = self.sistema + '\n\n' + p
        if len(p) > 12000:
            f = PROMPTS / f'{self.id}.md'
            f.write_text(p, encoding='utf-8')
            return f'Lee el fichero {f} y haz exactamente lo que pide (es el encargo completo).'
        return p

    def _cli(self):
        cwd = os.path.expanduser(self.cwd or config()['trabajo_dir'])
        Path(cwd).mkdir(parents=True, exist_ok=True)
        self.cwd = cwd
        env = dict(os.environ)
        env['CENTRO_IA_PADRE'] = self.id
        env['CENTRO_IA_PROFUNDIDAD'] = str(int(os.environ.get('CENTRO_IA_PROFUNDIDAD', '0')) + 1)
        # OpenCode (Bun) trabaja en $PWD, no en el cwd real: si se hereda el del padre, escribe en otra carpeta
        env['PWD'] = str(Path(cwd).resolve())
        stdin_texto = None
        m = self.motor
        if m.startswith('claude:'):
            cu = cuenta_claude(m.split(':', 1)[1])
            if not cu:
                raise RuntimeError(f'no existe la cuenta {m}')
            env.update({k: v for k, v in entorno_claude(cu).items() if k == 'CLAUDE_CONFIG_DIR'})
            if cu['normal']:
                env.pop('CLAUDE_CONFIG_DIR', None)
            for k in ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT'):
                env.pop(k, None)
            cmd = [shutil.which('claude') or 'claude', '-p', '--output-format', 'stream-json', '--verbose',
                   '--dangerously-skip-permissions']
            if self.modelo:
                cmd += ['--model', self.modelo]
            if self.sistema:
                cmd += ['--append-system-prompt', self.sistema]
            cmd += self.extra
            stdin_texto = self.prompt
            parser = self._linea_claude
        elif m == 'codex':
            cmd = [shutil.which('codex') or 'codex', 'exec', '--json', '--skip-git-repo-check',
                   '--dangerously-bypass-approvals-and-sandbox', '-C', cwd]
            if self.modelo:
                cmd += ['-m', self.modelo]
            cmd += self.extra + ['-']
            stdin_texto = (self.sistema + '\n\n' + self.prompt) if self.sistema else self.prompt
            parser = self._linea_codex
        elif m == 'kimi':
            # en modo -p Kimi ya actúa sin pedir permiso (y no admite --auto)
            cmd = [shutil.which('kimi') or 'kimi', '-p', self._prompt_cli(), '--output-format', 'stream-json']
            if self.modelo:
                cmd += ['-m', self.modelo]
            cmd += self.extra
            parser = self._linea_kimi
        elif m.startswith('opencode:'):
            modelo = m.split(':', 1)[1]
            self.modelo = self.modelo or modelo
            cmd = [shutil.which('opencode') or 'opencode', 'run', '--print-logs', '--log-level', 'warn',
                   '--format', 'json', '--title', 'centro-ia ' + self.id, '--auto', '-m', modelo]
            cmd += self.extra + [self._prompt_cli()]
            parser = self._linea_opencode
        else:
            raise RuntimeError(f'motor desconocido: {m}')

        self.ev('info', texto=f'Lanzando {m} en {cwd}')
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin_texto is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
        _procesos[self.id] = p
        escribir_json(ACTIVOS / f'{self.id}.json', {**self.meta(), 'pid': os.getpid(), 'pid_hijo': p.pid})
        if stdin_texto is not None:
            try:
                p.stdin.write(stdin_texto.encode('utf-8'))
                p.stdin.close()
            except Exception:
                pass
        fin_temprano = threading.Event()
        errores: list[str] = []

        def leer_err():
            for linea in iter(p.stderr.readline, b''):
                s = linea.decode('utf-8', 'replace').rstrip()
                if not s:
                    continue
                errores.append(s)
                del errores[:-40]
                if m.startswith('opencode:') and ('stream error' in s or 'level=ERROR' in s):
                    mm = re.search(r'error\.error="([^"]+)"', s)
                    self.error = mm.group(1) if mm else s[-300:]
                    self.estado = 'error'
                    self.ev('error', texto=self.error)
                    fin_temprano.set()
                    return

        def leer_out():
            for linea in iter(p.stdout.readline, b''):
                s = linea.decode('utf-8', 'replace').strip()
                if not s:
                    continue
                try:
                    ev = json.loads(s)
                except Exception:
                    self.texto.append(s + '\n')
                    self.ev('texto', texto=s + '\n')
                    continue
                try:
                    if parser(ev):
                        fin_temprano.set()
                except Exception as e:
                    self.ev('info', texto=f'(evento no interpretado: {e})')
            fin_temprano.set()

        he = threading.Thread(target=leer_err, daemon=True)
        ho = threading.Thread(target=leer_out, daemon=True)
        he.start()
        ho.start()
        if not fin_temprano.wait(self.timeout):
            self.estado, self.error = 'timeout', f'superó {self.timeout // 60} min'
        # da 5 s para salir solo; si no, se corta (OpenCode se queda colgado tras un error)
        try:
            p.wait(5 if self.estado != 'en curso' or m.startswith('opencode:') else 30)
        except subprocess.TimeoutExpired:
            matar_arbol(p.pid)
        ho.join(3)
        if p.returncode not in (0, None) and self.estado == 'en curso' and not self.texto:
            self.estado = 'error'
            self.error = self.error or ('\n'.join(errores[-8:]) or f'código {p.returncode}')
        if self.estado == 'cancelado':
            self.error = 'cancelado'

    # parsers: devuelven True si el motor ha terminado
    def _linea_claude(self, ev) -> bool:
        t = ev.get('type')
        if t == 'assistant':
            for c in (ev.get('message') or {}).get('content') or []:
                if c.get('type') == 'text' and c.get('text'):
                    self.texto.append(c['text'] + '\n')
                    self.ev('texto', texto=c['text'] + '\n')
                elif c.get('type') == 'tool_use':
                    self.ev('herramienta', nombre=c.get('name'), entrada=_resumen(c.get('input')))
        elif t == 'user':
            for c in (ev.get('message') or {}).get('content') or []:
                if isinstance(c, dict) and c.get('type') == 'tool_result':
                    cont = c.get('content')
                    if isinstance(cont, list):
                        cont = ' '.join(x.get('text', '') for x in cont if isinstance(x, dict))
                    self.ev('resultado', texto=str(cont)[:600], error=bool(c.get('is_error')))
        elif t == 'system' and ev.get('subtype') == 'init':
            self.ev('info', texto=f"Modelo {ev.get('model')} · {len(ev.get('tools') or [])} herramientas")
            self.modelo = self.modelo or ev.get('model', '')
        elif t == 'result':
            self.coste = ev.get('total_cost_usd')
            u = ev.get('usage') or {}
            self.tokens = {'entrada': u.get('input_tokens'), 'salida': u.get('output_tokens'),
                           'cache': u.get('cache_read_input_tokens')}
            if ev.get('is_error'):
                self.estado = 'error'
                self.error = str(ev.get('result') or ev.get('subtype'))[:500]
            elif ev.get('result'):
                # el texto final es el que vale como respuesta
                self.texto = [ev['result']]
            return True
        return False

    def _linea_codex(self, ev) -> bool:
        t = ev.get('type')
        it = ev.get('item') or {}
        if t == 'item.completed':
            if it.get('type') == 'agent_message':
                self.texto.append(it.get('text', '') + '\n')
                self.ev('texto', texto=it.get('text', '') + '\n')
            elif it.get('type') in ('command_execution', 'file_change', 'mcp_tool_call', 'web_search'):
                self.ev('herramienta', nombre=it['type'], entrada=_resumen(it.get('command') or it.get('changes') or it))
        elif t == 'turn.completed':
            u = ev.get('usage') or {}
            self.tokens = {'entrada': u.get('input_tokens'), 'salida': u.get('output_tokens'),
                           'cache': u.get('cached_input_tokens')}
            return True
        elif t in ('turn.failed', 'error'):
            self.estado = 'error'
            self.error = json.dumps(ev.get('error') or ev.get('message') or ev, ensure_ascii=False)[:500]
            self.ev('error', texto=self.error)
            return True
        return False

    def _linea_kimi(self, ev) -> bool:
        rol = ev.get('role')
        if rol == 'assistant':
            cont = ev.get('content')
            if isinstance(cont, list):
                cont = ''.join(x.get('text', '') for x in cont if isinstance(x, dict) and x.get('type') == 'text')
            if cont:
                self.texto.append(str(cont) + '\n')
                self.ev('texto', texto=str(cont) + '\n')
            for tc in ev.get('tool_calls') or []:
                fn = tc.get('function') or {}
                self.ev('herramienta', nombre=fn.get('name'), entrada=_resumen(fn.get('arguments')))
        elif rol == 'tool':
            self.ev('resultado', texto=str(ev.get('content'))[:600])
        elif ev.get('type') == 'error' or rol == 'error':
            self.estado = 'error'
            self.error = json.dumps(ev, ensure_ascii=False)[:500]
            self.ev('error', texto=self.error)
        return False

    def _linea_opencode(self, ev) -> bool:
        t = ev.get('type')
        part = ev.get('part') or {}
        if t == 'text' and part.get('text'):
            self.texto.append(part['text'] + '\n')
            self.ev('texto', texto=part['text'] + '\n')
        elif t in ('tool_use', 'tool'):
            st = part.get('state') or {}
            self.ev('herramienta', nombre=part.get('tool'), entrada=_resumen(st.get('input')))
        elif t == 'step_finish':
            tk = part.get('tokens') or {}
            self.coste = (self.coste or 0) + (part.get('cost') or 0)
            self.tokens = {'entrada': tk.get('input'), 'salida': tk.get('output'), 'cache': (tk.get('cache') or {}).get('read')}
        elif t == 'error':
            self.estado = 'error'
            self.error = json.dumps(ev.get('error'), ensure_ascii=False)[:500]
            self.ev('error', texto=self.error)
            return True
        return False


def _resumen(x, n: int = 300) -> str:
    if x is None:
        return ''
    if isinstance(x, str):
        s = x
    else:
        try:
            s = json.dumps(x, ensure_ascii=False)
        except Exception:
            s = str(x)
    return s if len(s) <= n else s[:n] + '…'


_trabajos_vivos: dict[str, Trabajo] = {}


def lanzar(motor: str, prompt: str, **kw) -> Trabajo:
    t = Trabajo(motor, prompt, **kw)
    _trabajos_vivos[t.id] = t
    return t.lanzar()


def cancelar(ident: str) -> bool:
    t = _trabajos_vivos.get(ident)
    if t and ident in _procesos:
        t.estado = 'cancelado'
        matar_arbol(_procesos[ident].pid)
        return True
    a = leer_json(ACTIVOS / f'{ident}.json')
    if a and a.get('pid_hijo'):
        matar_arbol(a['pid_hijo'])
        return True
    return False


def activos() -> list[dict]:
    out = []
    for f in ACTIVOS.glob('*.json'):
        a = leer_json(f)
        if not a:
            continue
        # limpia los que se quedaron huérfanos (proceso dueño muerto)
        if not _pid_vivo(a.get('pid', 0)):
            try:
                f.unlink()
            except Exception:
                pass
            continue
        out.append(a)
    return sorted(out, key=lambda x: x.get('inicio', 0), reverse=True)


def _pid_vivo(pid: int) -> bool:
    if not pid:
        return False
    if pid == os.getpid():
        return True
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    try:
        r = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], capture_output=True, text=True,
                           creationflags=CREATE_NO_WINDOW, timeout=10)
        return str(pid) in r.stdout
    except Exception:
        return True


def historial(n: int = 200) -> list[dict]:
    if not HISTORIAL.exists():
        return []
    with open(HISTORIAL, encoding='utf-8') as f:
        lineas = f.readlines()[-n:]
    out = []
    for l in reversed(lineas):
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def resumen_gasto() -> dict:
    """Suma por motor de lo registrado por el Centro (coste real en Experiential/OpenCode;
    en Claude es el equivalente API que informa el CLI, no se cobra con suscripción)."""
    tot: dict[str, dict] = {}
    for h in historial(5000):
        k = h['motor'].split(':')[0]
        d = tot.setdefault(k, {'llamadas': 0, 'coste': 0.0, 'segundos': 0.0, 'errores': 0})
        d['llamadas'] += 1
        d['coste'] += h.get('coste') or 0
        d['segundos'] += h.get('segundos') or 0
        d['errores'] += 1 if h.get('estado') != 'ok' else 0
    for d in tot.values():
        d['coste'] = round(d['coste'], 4)
        d['segundos'] = round(d['segundos'])
    return tot


def leer_eventos(ident: str, desde: int = 0) -> tuple[list[dict], int]:
    f = TRABAJOS / f'{ident}.jsonl'
    if not f.exists():
        return [], desde
    with open(f, 'rb') as fh:
        fh.seek(desde)
        datos = fh.read()
    # solo líneas completas
    corte = datos.rfind(b'\n') + 1
    out = []
    for l in datos[:corte].splitlines():
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out, desde + corte


# ───────────────────────── cadenas con respaldo (motor «auto:<tipo>») ─────────────────────────

TIPOS_BASE = {
    'texto': 'texto corto sin herramientas: resumir, clasificar, traducir, extraer JSON, redactar',
    'sencillo': 'código sencillo, tests, scripts, arreglos pequeños con ficheros',
    'front': 'frontend / UI y tareas algo complejas de poco volumen',
    'codigo': 'programar algo mediano-grande con ficheros y tests',
    'investigacion': 'investigar, buscar en internet y sintetizar (RAG)',
    'lote': 'tareas mecánicas en lote: renombrar, scripts, migraciones',
    'largo': 'contexto enorme (>200k) o refactor grande',
    'revision': 'segunda opinión / verificación independiente',
    'pensar': 'estrategia o razonamiento difícil (el modelo que mejor razona)',
}
TIPOS = {**TIPOS_BASE, **(config().get('tipos') or {})}

# Punto de partida de serie, pensado para alguien con UNA cuenta de Claude Code, Codex y OpenCode
# con modelos gratis. Orden = calidad esperada. Las notas reales (ia_valorar) lo reordenan con el uso,
# y config.json («cadenas») lo sustituye entero por tipo.
# '@ocgratis' = el mejor modelo gratis de OpenCode sondeado en ese momento;
# '@expgratis' = lo mismo en Experiential Labs (solo si hay EXPLABS_API_KEY).
H, S, O = 'claude-haiku-5-5', 'claude-sonnet-5-5', 'claude-opus-5-5'
SEMILLAS_BASE = {
    'texto': [('claude:principal', H), ('opencode:@ocgratis', ''), ('exp:@expgratis', '')],
    'sencillo': [('claude:principal', S), ('opencode:@ocgratis', ''), ('codex', '')],
    'front': [('claude:principal', S), ('codex', ''), ('claude:principal', O)],
    'codigo': [('claude:principal', S), ('codex', ''), ('claude:principal', O), ('kimi', '')],
    'investigacion': [('claude:principal', S), ('kimi', ''), ('codex', '')],
    'lote': [('opencode:@ocgratis', ''), ('claude:principal', H), ('codex', '')],
    'largo': [('kimi', ''), ('claude:principal', S), ('codex', '')],
    'revision': [('codex', ''), ('kimi', ''), ('claude:principal', S)],
    'pensar': [('claude:principal', O), ('codex', '')],
}


def _semillas() -> dict:
    s = dict(SEMILLAS_BASE)
    for tipo, lista in (config().get('cadenas') or {}).items():
        s[tipo] = [tuple((x.split('|', 1) + [''])[:2]) for x in lista]
    return s


SEMILLAS = _semillas()
VALORACIONES = DATOS / 'valoraciones.jsonl'


def valorar(ident: str, nota: float, comentario: str = '', tipo: str = '') -> dict:
    """Nota 1-5 de un trabajo delegado (la pone el orquestador al revisar)."""
    h = next((x for x in historial(3000) if x['id'] == ident), None)
    if not h:
        raise RuntimeError(f'No encuentro el trabajo {ident}')
    reg = {'ts': ahora(), 'id': ident, 'motor': h['motor'], 'modelo': h.get('modelo', ''),
           'tipo': tipo or h.get('tarea_tipo', ''), 'nota': max(1.0, min(5.0, float(nota))), 'comentario': comentario[:400],
           'segundos': h.get('segundos')}
    anexar(VALORACIONES, reg)
    return reg


def _clave(motor: str, modelo: str) -> str:
    return motor + (f'|{modelo}' if modelo else '')


def estadisticas() -> dict:
    """Por tipo y motor: trabajos, % éxito, nota media, segundos medianos."""
    est: dict = {}
    for h in historial(5000):
        t = h.get('tarea_tipo')
        if not t:
            continue
        d = est.setdefault(t, {}).setdefault(_clave(h['motor'], h.get('modelo_pedido', '')),
                                              {'n': 0, 'ok': 0, 'seg': [], 'notas': []})
        d['n'] += 1
        d['ok'] += 1 if h.get('estado') == 'ok' else 0
        if h.get('segundos') is not None:
            d['seg'].append(h['segundos'])
    if VALORACIONES.exists():
        for l in VALORACIONES.read_text(encoding='utf-8').splitlines():
            try:
                v = json.loads(l)
            except Exception:
                continue
            if not v.get('tipo'):
                continue
            d = est.setdefault(v['tipo'], {}).setdefault(_clave(v['motor'], v.get('modelo', '') if v['motor'].startswith('claude:') else ''),
                                                          {'n': 0, 'ok': 0, 'seg': [], 'notas': []})
            d['notas'].append(v['nota'])
    for t in est.values():
        for d in t.values():
            s = sorted(d['seg'])
            d['seg_mediana'] = s[len(s) // 2] if s else None
            d['nota_media'] = round(sum(d['notas']) / len(d['notas']), 2) if d['notas'] else None
            d['exito'] = round(d['ok'] / d['n'] * 100) if d['n'] else None
            del d['seg']
    return est


def _uso_por_motor() -> dict:
    try:
        return {c['motor']: c for c in uso_todo()['cuentas']}
    except Exception:
        return {}


def _saturada(c: dict | None) -> bool:
    """True si la cuenta está casi sin cupo (no merece la pena mandarle trabajo)."""
    if not c:
        return False
    for l in c.get('limites') or []:
        p = l.get('pct') or 0
        n = l.get('nombre', '')
        if ('5 h' in n and p >= 90) or (p >= 97):
            return True
    return False


def cadena(tipo: str, explicar: bool = False):
    """Motores (motor, modelo) para un tipo de tarea, ordenados por CALIDAD esperada:
    semillas + notas reales + % de éxito. Quita lo no disponible (gratis caídos, sin saldo, cuentas sin cupo)."""
    g = gratis_ahora()
    exp_g = g['exp']
    oc_g = g['opencode']
    _exp_api = next((a for a in uso_apis() if a['id'] == 'experiential'), {})
    saldo_exp = None if _exp_api.get('bloqueado') else _exp_api.get('saldo')
    uso = _uso_por_motor()
    est = estadisticas().get(tipo, {})
    cand, vistos = [], set()
    # orden inicial MEDIDO (calibración) si existe; lo no calibrado va detrás como respaldo
    medido = (leer_json(DATOS / 'orden_inicial.json', {}) or {}).get(tipo) or []
    base = [(m, mod, nota) for m, mod, nota in medido]
    suelo = min([n for _, _, n in base], default=5.4) - 0.5
    for i, (m, mod) in enumerate(SEMILLAS.get(tipo, [])):
        mm = m.split(':', 1)[1] if m.startswith('exp-pago:') else m
        if not any(x[0] == mm and x[1] == mod for x in base):
            base.append((m, mod, (suelo - 0.1 * i) if medido else (5 - 0.4 * i)))
    for i, (m, mod, semilla) in enumerate(base):
        if m.startswith('exp:') and m[4:] not in exp_g and any(x[0] == m for x in medido):
            # modelo de pago medido: solo con saldo
            if saldo_exp is None or saldo_exp < 0.05:
                continue
            m = 'exp-pago:' + m
        pago = m.startswith('exp-pago:')
        if pago:
            m = m.split(':', 1)[1]
            if saldo_exp is None or saldo_exp < 0.05:
                continue
        if '@expgratis' in m:
            libres = [x for x in exp_g if f'exp:{x}' not in vistos]
            if not libres:
                continue
            m = m.replace('@expgratis', libres[0])
        if '@ocgratis' in m:
            if not oc_g:
                continue
            m = m.replace('@ocgratis', oc_g[0])
        if not pago:
            if m.startswith('exp:') and m[4:] not in exp_g:
                continue
            if m.startswith('opencode:experiential/') and m.split('/', 1)[1] not in exp_g:
                continue
            if m.startswith('opencode:opencode/') and m.split(':', 1)[1] not in oc_g:
                continue
        if _saturada(uso.get(m)):
            continue
        k = _clave(m, mod)
        if k in vistos:
            continue
        vistos.add(k)
        d = est.get(k) or {}
        notas = d.get('notas') or []
        punt = (semilla * 2 + sum(notas)) / (2 + len(notas))
        if (d.get('n') or 0) >= 3 and (d.get('exito') or 100) < 60:
            punt -= 1.5
        cand.append((punt, m, mod, d))
    cand.sort(key=lambda x: -x[0])
    if explicar:
        return [(m, mod, round(p, 2), d) for p, m, mod, d in cand]
    return [(m, mod) for p, m, mod, d in cand]


class Cadena:
    """Prueba los motores en orden; si uno falla (sin cupo, error, timeout, vacío) pasa al siguiente.
    Si fallan todos, lo dice claramente para que lo haga el orquestador."""

    def __init__(self, motores: list[tuple[str, str]], prompt: str, cwd: str = '', origen: str = 'mcp',
                 padre: str = '', timeout_min: float | None = None, etiqueta: str = '', tipo: str = ''):
        self.id = 'c-' + datetime.now().strftime('%m%d-%H%M%S-') + uuid.uuid4().hex[:4]
        self.motores = motores
        self.prompt, self.cwd, self.origen, self.padre, self.timeout_min = prompt, cwd, origen, padre, timeout_min
        self.etiqueta = etiqueta
        self.tipo = tipo
        self.motor = etiqueta or 'cadena'
        self.intentos: list[dict] = []
        self.final: dict | None = None
        self.actual: Trabajo | None = None
        self.hecho = threading.Event()
        self.inicio = ahora()
        self.cancelada = False

    def lanzar(self) -> 'Cadena':
        threading.Thread(target=self._correr, daemon=True).start()
        return self

    def _correr(self):
        try:
            for motor, modelo in self.motores:
                if self.cancelada:
                    break
                t = Trabajo(motor, self.prompt, modelo=modelo, cwd=self.cwd, origen=self.origen, padre=self.padre,
                            timeout_min=self.timeout_min, tipo=self.tipo)
                _trabajos_vivos[t.id] = t
                self.actual = t
                t.lanzar()
                t.hecho.wait()
                r = t.resultado()
                self.intentos.append({'motor': motor, 'modelo': modelo, 'estado': r['estado'],
                                      'segundos': r['segundos'], 'error': r['error'][:200]})
                if r['estado'] == 'ok' and r['respuesta']:
                    self.final = r
                    return
                if r['estado'] == 'cancelado':
                    return
        finally:
            self.hecho.set()

    def resultado(self) -> dict:
        seg = round(ahora() - self.inicio, 1)
        if self.final:
            r = dict(self.final)
        else:
            r = {'motor': self.etiqueta or 'cadena', 'modelo': '', 'estado': 'error' if self.hecho.is_set() else 'en curso',
                 'coste': None, 'tokens': {}, 'respuesta': '',
                 'error': ('TODOS LOS MOTORES DE LA CADENA FALLARON: hazlo tú (orquestador) o elige otro motor.'
                           if self.hecho.is_set() else '')}
        r['segundos'] = seg
        r['cadena'] = self.id
        r.setdefault('id', self.id)
        r['intentos'] = self.intentos
        return r


def politica() -> str:
    f = RAIZ / 'politica.md'
    return f.read_text(encoding='utf-8') if f.exists() else ''


def estado_texto() -> str:
    """Resumen compacto para el orquestador (MCP)."""
    u = uso_todo()
    g = gratis_ahora()
    l = ['USO DE LAS CUENTAS:']
    for c in u['cuentas']:
        lim = ', '.join(f"{x['nombre']} {x['pct']}%" for x in c.get('limites', []) if x.get('pct') is not None)
        extra = f" [SOLO PARA: {c['solo_para']}]" if c.get('solo_para') else ''
        l.append(f"- {c['motor']}{extra}: {c.get('estado')} · {c.get('plan', '')} · {lim}")
    for a in uso_apis():
        if a.get('saldo') is not None:
            l.append(f"- API {a['nombre']}: saldo {a['saldo']} $" + (f" (cargado {a['cargado']} $)" if a.get('cargado') else ''))
    l.append('GRATIS AHORA (sondeado):')
    l.append('- Experiential (exp:<modelo>, solo texto): ' + (', '.join(g['exp']) or 'ninguno'))
    l.append('- OpenCode (opencode:<modelo>, agéntico): ' + (', '.join(g['opencode']) or 'ninguno (cupo gratis agotado)'))
    if g['exp']:
        l.append('- Agéntico con los gratis de Experiential: ' + ', '.join(f'opencode:experiential/{m}' for m in g['exp']))
    ts = g['detalle'].get('exp_ts')
    if ts:
        l.append(f'(último sondeo de Experiential: hace {int((ahora() - ts) / 60)} min)')
    l.append('CADENAS AUTOMÁTICAS AHORA (motor «auto:<tipo>», salta al siguiente si uno falla o está sin cupo):')
    for tipo, desc in TIPOS.items():
        ch = cadena(tipo, explicar=True)
        l.append(f"- auto:{tipo} ({desc}): " + (' → '.join(
            m + (f'[{mod}]' if mod else '') + f' ({p}' + (f", nota {d['nota_media']}" if d.get('nota_media') else '')
            + (f", {d['exito']}% ok en {d['n']}" if d.get('n') else '') + ')' for m, mod, p, d in ch) or 'ninguno disponible: hazlo tú'))
    act = activos()
    if act:
        l.append(f'TRABAJOS EN CURSO: {len(act)} → ' + ', '.join(f"{a['id']} ({a['motor']})" for a in act[:8]))
    return '\n'.join(l)

"""Tareas de calibración con corrector objetivo. Edita CANDIDATOS con los motores que tengas."""
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

H, S, O = 'claude-haiku-5-5', 'claude-sonnet-5-5', 'claude-opus-5-5'
SOLO = '\n\nHazlo tú directamente: NO delegues en otras IAs ni lances subagentes.'

CANDIDATOS = {
    'texto': [('exp:deepseek-v4.1-flash-1017', ''), ('exp:gpt-6-luna', ''), ('exp:gpt-6-sol', ''), ('claude:principal', H)],
    'sencillo': [('opencode:experiential/deepseek-v4.1-flash-1017', ''), ('codex', ''), ('claude:principal', H), ('claude:principal', S)],
    'codigo': [('claude:principal', O), ('claude:principal', S), ('codex', ''), ('opencode:experiential/deepseek-v4.1-flash-1017', '')],
    'investigacion': [('kimi', ''), ('claude:principal', S), ('claude:principal', H), ('codex', '')],
    'front': [('exp:gpt-6-sol', ''), ('codex', ''), ('claude:principal', S), ('claude:principal', O)],
}


def primer_json(texto: str):
    texto = re.sub(r'```(?:json)?', '', texto or '')
    for ini, fin in (('[', ']'), ('{', '}')):
        i = texto.find(ini)
        j = texto.rfind(fin)
        if i != -1 and j > i:
            try:
                return json.loads(texto[i:j + 1])
            except Exception:
                continue
    return None


def norm(x) -> str:
    return re.sub(r'[\s.,€]', '', str(x).lower().strip()).replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')


def pytest_ratio(d: Path, fichero_test: str, codigo_test: str):
    f = d / fichero_test
    f.write_text(codigo_test, encoding='utf-8')
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', str(f)], cwd=d,
                       capture_output=True, text=True, timeout=120)
    sal = r.stdout + r.stderr
    p = int(m.group(1)) if (m := re.search(r'(\d+) passed', sal)) else 0
    fa = int(m.group(1)) if (m := re.search(r'(\d+) failed', sal)) else 0
    er = int(m.group(1)) if (m := re.search(r'(\d+) error', sal)) else 0
    tot = p + fa + er
    if tot == 0:
        return 0.0, 'no se pudieron ejecutar los tests: ' + sal.strip().splitlines()[-1][:80] if sal.strip() else 'sin salida'
    return p / tot, f'{p}/{tot} tests'


# ─────────────── TEXTO ───────────────
EXTR_TEXTOS = [
    'Ayer, 14 de octubre de 2026, Lucía Fernández pagó 1.250,50 € en nuestra tienda de Valencia.',
    'Factura emitida en Bilbao a nombre de Marcos Ruiz el 2 de noviembre de 2026 por un total de 89 euros.',
    'El cliente Andrés Gil (Sevilla) abonó trescientos euros justos el 30/09/2026.',
    'Pago recibido: 4.000 € — Teresa Molina — sucursal de Zaragoza — fecha 1 de enero de 2026.',
    'Nos escribe desde Málaga Pablo Ortega: el 15-07-2026 transfirió 19,99 €.',
]
EXTR_ESPERADO = [
    {'nombre': 'Lucía Fernández', 'ciudad': 'Valencia', 'importe_eur': 1250.5, 'fecha': '2026-10-14'},
    {'nombre': 'Marcos Ruiz', 'ciudad': 'Bilbao', 'importe_eur': 89, 'fecha': '2026-11-02'},
    {'nombre': 'Andrés Gil', 'ciudad': 'Sevilla', 'importe_eur': 300, 'fecha': '2026-09-30'},
    {'nombre': 'Teresa Molina', 'ciudad': 'Zaragoza', 'importe_eur': 4000, 'fecha': '2026-01-01'},
    {'nombre': 'Pablo Ortega', 'ciudad': 'Málaga', 'importe_eur': 19.99, 'fecha': '2026-07-15'},
]


def comp_extraccion(d, resp):
    j = primer_json(resp)
    if not isinstance(j, list):
        return 0.0, 'no devolvió una lista JSON'
    bien = tot = 0
    for i, esp in enumerate(EXTR_ESPERADO):
        got = j[i] if i < len(j) and isinstance(j[i], dict) else {}
        for k, v in esp.items():
            tot += 1
            g = got.get(k)
            if k == 'importe_eur':
                try:
                    bien += abs(float(str(g).replace(',', '.')) - v) < 0.01
                except Exception:
                    pass
            else:
                bien += norm(g) == norm(v)
    return bien / tot, f'{bien}/{tot} campos'


CLAS_MENSAJES = [
    ('Me habéis cobrado dos veces el pedido y necesito que me devolváis el dinero ya, es urgente.', 'factura', 'alta'),
    ('¿Cuándo llega mi paquete? El seguimiento no se mueve desde el lunes.', 'envio', 'baja'),
    ('Quiero devolver las zapatillas, me quedan pequeñas.', 'devolucion', 'baja'),
    ('La app se cierra sola al abrir el carrito, no puedo comprar nada y tengo que hacerlo hoy.', 'tecnico', 'alta'),
    ('¿Tenéis tienda física en Madrid?', 'otro', 'baja'),
    ('Necesito la factura con mi NIF para presentarla a Hacienda.', 'factura', 'baja'),
    ('El repartidor dejó el paquete roto en la puerta, y dentro había cristal: ¡casi se corta mi hijo!', 'envio', 'alta'),
    ('No me deja iniciar sesión, dice contraseña incorrecta aunque la he cambiado.', 'tecnico', 'baja'),
]


def comp_clasif(d, resp):
    j = primer_json(resp)
    if not isinstance(j, list):
        return 0.0, 'no devolvió una lista JSON'
    bien = 0
    for i, (_, cat, urg) in enumerate(CLAS_MENSAJES):
        g = j[i] if i < len(j) and isinstance(j[i], dict) else {}
        bien += norm(g.get('categoria')) == cat
        bien += norm(g.get('urgencia')) == urg
    return bien / (2 * len(CLAS_MENSAJES)), f'{bien}/{2 * len(CLAS_MENSAJES)} etiquetas'


# ─────────────── SENCILLO ───────────────
T_FECHA = '''
import datetime as dt, pytest
from solucion import parse_fecha
def test_iso(): assert parse_fecha("2026-11-03") == dt.date(2026,11,3)
def test_barras(): assert parse_fecha("03/11/2026") == dt.date(2026,11,3)
def test_barras_corto(): assert parse_fecha("3/1/2026") == dt.date(2026,1,3)
def test_abrev(): assert parse_fecha("3 nov 2026") == dt.date(2026,11,3)
def test_largo(): assert parse_fecha("3 de noviembre de 2026") == dt.date(2026,11,3)
def test_mayus_espacios(): assert parse_fecha("  15 DE Agosto DE 2025 ") == dt.date(2025,8,15)
def test_bisiesto(): assert parse_fecha("29/02/2024") == dt.date(2024,2,29)
@pytest.mark.parametrize("m", ["31/02/2026", "", "hola", "2026-13-01", "29/02/2025"])
def test_invalidas(m):
    with pytest.raises(ValueError): parse_fecha(m)
'''
T_DEDUP = '''
from solucion import dedup_estable
def test_basico(): assert dedup_estable([3,1,3,2,1]) == [3,1,2]
def test_vacio(): assert dedup_estable([]) == []
def test_cadenas(): assert dedup_estable(list("abracadabra")) == ["a","b","r","c","d"]
def test_key(): assert dedup_estable(["Ana","ana","Luis","ANA"], key=str.lower) == ["Ana","Luis"]
def test_no_hashables(): assert dedup_estable([[1],[2],[1]]) == [[1],[2]]
def test_dicts_key(): assert dedup_estable([{"id":1,"v":"a"},{"id":1,"v":"b"},{"id":2}], key=lambda d: d["id"]) == [{"id":1,"v":"a"},{"id":2}]
def test_no_muta():
    x=[1,1,2]; dedup_estable(x); assert x==[1,1,2]
def test_generador(): assert dedup_estable(i%3 for i in range(7)) == [0,1,2]
'''
T_MEDIANA = '''
import math, pytest
from solucion import mediana
def test_impar(): assert mediana([3,1,2]) == 2
def test_par(): assert mediana([4,1,3,2]) == 2.5
def test_none(): assert mediana([None,5,None,1,3]) == 3
def test_nan(): assert mediana([float("nan"),2,4]) == 3
def test_vacio(): assert mediana([]) is None
def test_solo_nulos(): assert mediana([None,float("nan")]) is None
def test_floats(): assert math.isclose(mediana([0.1,0.2,0.3,0.4]), 0.25)
def test_texto():
    with pytest.raises(TypeError): mediana([1,"2",3])
def test_bool_no_cuenta_como_texto(): assert mediana([1,2,3]) == 2
'''

# ─────────────── CÓDIGO (mini repo) ───────────────
INV_PY = '''"""Inventario sencillo: sku -> cantidad."""
import json


class SinStock(Exception):
    pass


class Inventario:
    def __init__(self):
        self.items = {}

    def anadir(self, sku, cantidad):
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        self.items[sku] = self.items.get(sku, 0) + cantidad

    def retirar(self, sku, cantidad):
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        if self.items.get(sku, 0) < cantidad:
            raise SinStock(sku)
        self.items[sku] -= cantidad
        if self.items[sku] == 0:
            del self.items[sku]

    def cantidad(self, sku):
        return self.items.get(sku, 0)

    def total(self):
        return sum(self.items.values())

    def guardar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"items": self.items}, f)

    @classmethod
    def cargar(cls, ruta):
        inv = cls()
        with open(ruta, encoding="utf-8") as f:
            inv.items = json.load(f)["items"]
        return inv
'''
INV_TESTS = '''import pytest
from inventario import Inventario, SinStock
def test_anadir():
    i=Inventario(); i.anadir("A",3); i.anadir("A",2); assert i.cantidad("A")==5
def test_retirar():
    i=Inventario(); i.anadir("A",3); i.retirar("A",1); assert i.cantidad("A")==2
def test_retirar_todo_borra():
    i=Inventario(); i.anadir("A",3); i.retirar("A",3); assert i.cantidad("A")==0 and i.total()==0
def test_sin_stock():
    i=Inventario(); i.anadir("A",1)
    with pytest.raises(SinStock): i.retirar("A",2)
def test_cantidad_negativa():
    i=Inventario()
    with pytest.raises(ValueError): i.anadir("A",0)
def test_total():
    i=Inventario(); i.anadir("A",3); i.anadir("B",4); assert i.total()==7
def test_guardar_cargar(tmp_path):
    i=Inventario(); i.anadir("A",3); p=tmp_path/"x.json"; i.guardar(p); assert Inventario.cargar(p).cantidad("A")==3
def test_desconocido(): assert Inventario().cantidad("Z")==0
'''
INV_OCULTOS = '''import datetime as dt, json, pytest
from inventario import Inventario, SinStock
D=dt.date
def test_fefo():
    i=Inventario(); i.anadir("L",5,caduca=D(2026,12,1)); i.anadir("L",5,caduca=D(2026,11,10)); i.anadir("L",5)
    i.retirar("L",7)
    assert i.caducados(D(2026,12,2)) == {"L":3}
def test_sin_fecha_al_final():
    i=Inventario(); i.anadir("L",2); i.anadir("L",2,caduca=D(2026,1,1)); i.retirar("L",2)
    assert i.caducados(D(2030,1,1)) == {}
    assert i.cantidad("L")==2
def test_caducados_vacio(): assert Inventario().caducados(D(2026,1,1)) == {}
def test_caducados_varios():
    i=Inventario(); i.anadir("A",1,caduca=D(2026,1,1)); i.anadir("B",2,caduca=D(2026,6,1)); i.anadir("B",4,caduca=D(2025,6,1))
    assert i.caducados(D(2026,3,1)) == {"A":1,"B":4}
def test_cantidad_suma_lotes():
    i=Inventario(); i.anadir("A",1,caduca=D(2026,1,1)); i.anadir("A",2); assert i.cantidad("A")==3 and i.total()==3
def test_sin_stock_lotes():
    i=Inventario(); i.anadir("A",1,caduca=D(2026,1,1))
    with pytest.raises(SinStock): i.retirar("A",2)
    assert i.cantidad("A")==1
def test_roundtrip_v2(tmp_path):
    i=Inventario(); i.anadir("A",2,caduca=D(2026,5,5)); i.anadir("A",1); p=tmp_path/"v2.json"; i.guardar(p)
    assert json.loads(p.read_text(encoding="utf-8")).get("version")==2
    j=Inventario.cargar(p); assert j.cantidad("A")==3 and j.caducados(D(2026,6,1))=={"A":2}
def test_carga_v1(tmp_path):
    p=tmp_path/"v1.json"; p.write_text(json.dumps({"items":{"X":4,"Y":1}}),encoding="utf-8")
    j=Inventario.cargar(p); assert j.cantidad("X")==4 and j.total()==5 and j.caducados(D(2099,1,1))=={}
def test_fichero_datos_v1():
    j=Inventario.cargar("datos_v1.json"); assert j.total()==12
'''


def prep_inventario(d: Path):
    (d / 'inventario.py').write_text(INV_PY, encoding='utf-8')
    (d / 'test_inventario.py').write_text(INV_TESTS, encoding='utf-8')
    (d / 'datos_v1.json').write_text(json.dumps({'items': {'TORN-8': 7, 'TUER-8': 5}}), encoding='utf-8')
    (d / '.huella').write_text(hashlib.md5(INV_TESTS.encode()).hexdigest(), encoding='utf-8')


def comp_inventario(d, resp):
    tocado = hashlib.md5((d / 'test_inventario.py').read_text(encoding='utf-8').encode()).hexdigest() != (d / '.huella').read_text().strip() \
        if (d / 'test_inventario.py').exists() else True
    if tocado:
        (d / 'test_inventario.py').write_text(INV_TESTS, encoding='utf-8')
    viejos, dv = pytest_ratio(d, 'test_inventario.py', INV_TESTS)
    nuevos, dn = pytest_ratio(d, 'test_ocultos_inv.py', INV_OCULTOS)
    nota = 0.4 * viejos + 0.6 * nuevos - (0.2 if tocado else 0)
    return max(0.0, nota), f'antiguos {dv}, nuevos {dn}' + (' · TOCÓ los tests antiguos' if tocado else '')


# ─────────────── INVESTIGACIÓN (verdad consultada en directo) ───────────────
def _json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'centro-ia'}), timeout=30) as r:
        return json.loads(r.read())


def comp_pypi(d, resp):
    j = primer_json(resp) or {}
    bien = 0
    for p in ('fastapi', 'pydantic', 'httpx'):
        bien += str((j or {}).get(p, '')).lstrip('v').strip() == _json(f'https://pypi.org/pypi/{p}/json')['info']['version']
    v = _json('https://pypi.org/pypi/fastapi/json')['info']['version']
    fecha = _json(f'https://pypi.org/pypi/fastapi/{v}/json')['urls'][0]['upload_time'][:10]
    bien += str((j or {}).get('fastapi_fecha', ''))[:10] == fecha
    return bien / 4, f'{bien}/4 datos'


def comp_node(d, resp):
    j = primer_json(resp) or {}
    lts = [x for x in _json('https://nodejs.org/dist/index.json') if x['lts']][0]
    bien = 0
    bien += str(j.get('node_lts', '')).lstrip('v') == lts['version'].lstrip('v')
    bien += norm(j.get('nombre_clave', '')) == norm(lts['lts'])
    bien += str(j.get('fecha', ''))[:10] == lts['date']
    bien += str(j.get('vite', '')).lstrip('v') == _json('https://registry.npmjs.org/vite/latest')['version']
    return bien / 4, f'{bien}/4 datos'


# ─────────────── FRONT (comprobado en navegador) ───────────────
FRONT_PROMPT = '''Crea una página web de UN SOLO fichero llamado index.html (HTML+CSS+JS, sin librerías externas) en la carpeta {DIR}.
Debe mostrar una tabla de productos con estos datos fijos en el código:
[{"nombre":"Teclado","categoria":"perifericos","precio":49.9},{"nombre":"Ratón","categoria":"perifericos","precio":19.5},
 {"nombre":"Monitor 27","categoria":"pantallas","precio":259},{"nombre":"Monitor 24","categoria":"pantallas","precio":149},
 {"nombre":"Webcam","categoria":"perifericos","precio":39},{"nombre":"Portátil","categoria":"ordenadores","precio":899},
 {"nombre":"Torre","categoria":"ordenadores","precio":1099},{"nombre":"Alfombrilla","categoria":"perifericos","precio":9.99}]
Requisitos EXACTOS (se comprueban automáticamente):
1. La tabla es <table id="tabla"> con una fila <tr> en <tbody> por producto visible y la columna de nombre con la clase "nombre".
2. <input id="filtro"> filtra por nombre sin distinguir mayúsculas (mientras se escribe).
3. <select id="categoria"> con opción value="todas" (por defecto) y una por categoría; filtra por categoría y se combina con el filtro de texto.
4. Un <th data-col="precio">: el primer clic ordena por precio de menor a mayor, el segundo de mayor a menor.
5. <span id="contador"> muestra el número de productos visibles con el texto "N productos" (p. ej. "8 productos").
6. <div id="vacio"> visible solo cuando no hay resultados (oculto con display:none en otro caso).
Que se vea limpio y moderno.'''


def comp_front(d, resp):
    f = d / 'index.html'
    if not f.exists():
        m = re.search(r'```html\s*(.*?)```', resp or '', re.S) or re.search(r'(<!doctype html.*</html>)', resp or '', re.S | re.I)
        if not m:
            return 0.0, 'no hay index.html'
        f.write_text(m.group(1), encoding='utf-8')
    from playwright.sync_api import sync_playwright
    bien, notas = 0, []
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome', headless=True)
        pg = b.new_page()
        pg.goto(f.resolve().as_uri())
        pg.wait_for_timeout(400)

        def vis():
            return pg.locator('#tabla tbody tr:visible').count()

        def comprobar(nombre, fn):
            nonlocal bien
            try:
                if fn():
                    bien += 1
                else:
                    notas.append(nombre)
            except Exception:
                notas.append(nombre + '!')
        comprobar('filas', lambda: vis() == 8)
        comprobar('contador', lambda: pg.locator('#contador').inner_text().strip() == '8 productos')
        comprobar('filtro', lambda: (pg.fill('#filtro', 'MONITOR'), pg.wait_for_timeout(200), vis() == 2)[2])
        comprobar('combinado', lambda: (pg.fill('#filtro', 'o'), pg.select_option('#categoria', 'perifericos'),
                                        pg.wait_for_timeout(200), vis() == 2 and '2 productos' in pg.locator('#contador').inner_text())[3])
        comprobar('vacio', lambda: (pg.fill('#filtro', 'zzzz'), pg.wait_for_timeout(200),
                                    vis() == 0 and pg.locator('#vacio').is_visible())[2])

        def orden():
            pg.fill('#filtro', '')
            pg.select_option('#categoria', 'todas')
            pg.wait_for_timeout(150)
            pg.click('th[data-col="precio"]')
            pg.wait_for_timeout(150)
            asc = pg.locator('#tabla tbody tr:visible .nombre').first.inner_text().strip()
            pg.click('th[data-col="precio"]')
            pg.wait_for_timeout(150)
            desc = pg.locator('#tabla tbody tr:visible .nombre').first.inner_text().strip()
            return asc == 'Alfombrilla' and desc == 'Torre' and not pg.locator('#vacio').is_visible()
        comprobar('orden', orden)
        pg.screenshot(path=str(d / 'captura.png'), full_page=True)
        b.close()
    return bien / 6, f'{bien}/6 comprobaciones' + (' · fallan: ' + ', '.join(notas) if notas else '')


TAREAS = [
    {'id': 'extraccion', 'tipo': 'texto', 'reps': 2, 'comprobar': comp_extraccion,
     'prompt': 'Extrae de cada texto: nombre, ciudad, importe_eur (número) y fecha (YYYY-MM-DD). Devuelve SOLO una lista JSON '
               'con un objeto por texto, en el mismo orden.\n\n' + '\n'.join(f'{i + 1}. {t}' for i, t in enumerate(EXTR_TEXTOS))},
    {'id': 'clasificacion', 'tipo': 'texto', 'reps': 2, 'comprobar': comp_clasif,
     'prompt': 'Clasifica cada mensaje de cliente. categoria: factura | envio | devolucion | tecnico | otro. '
               'urgencia: alta (dinero cobrado de más, seguridad o bloqueo que impide comprar hoy) | baja. '
               'Devuelve SOLO una lista JSON de objetos {"categoria":..., "urgencia":...} en el mismo orden.\n\n'
               + '\n'.join(f'{i + 1}. {m}' for i, (m, _, _) in enumerate(CLAS_MENSAJES))},
    {'id': 'fecha', 'tipo': 'sencillo', 'reps': 2, 'comprobar': lambda d, r: pytest_ratio(d, 'test_oculto.py', T_FECHA),
     'prompt': 'En la carpeta {DIR} crea solucion.py con parse_fecha(texto) -> datetime.date que acepte "2026-11-03", '
               '"03/11/2026" o "3/1/2026" (día/mes/año), "3 nov 2026" y "3 de noviembre de 2026" (meses en español, sin '
               'distinguir mayúsculas, ignorando espacios sobrantes). Fechas imposibles o texto no válido → ValueError. '
               'Añade tus propios tests con pytest y comprueba que pasan.' + SOLO},
    {'id': 'dedup', 'tipo': 'sencillo', 'reps': 2, 'comprobar': lambda d, r: pytest_ratio(d, 'test_oculto.py', T_DEDUP),
     'prompt': 'En la carpeta {DIR} crea solucion.py con dedup_estable(items, key=None) -> list: quita duplicados conservando '
               'la primera aparición y el orden. key opcional como en sorted. Debe funcionar con elementos no hashables '
               '(listas, dicts) y con cualquier iterable (también generadores), sin modificar la entrada. '
               'Añade tus propios tests con pytest y comprueba que pasan.' + SOLO},
    {'id': 'mediana', 'tipo': 'sencillo', 'reps': 2, 'comprobar': lambda d, r: pytest_ratio(d, 'test_oculto.py', T_MEDIANA),
     'prompt': 'En la carpeta {DIR} crea solucion.py con mediana(valores) que ignore None y NaN, devuelva None si no queda '
               'ningún número, haga la media de los dos centrales si hay cantidad par, y lance TypeError si hay algún valor '
               'no numérico (p. ej. texto). Añade tus propios tests con pytest y comprueba que pasan.' + SOLO},
    {'id': 'inventario', 'tipo': 'codigo', 'reps': 2, 'preparar': prep_inventario, 'comprobar': comp_inventario,
     'timeout_min': 15,
     'prompt': 'En la carpeta {DIR} hay un pequeño proyecto (inventario.py y test_inventario.py, ejecuta pytest para verlo). '
               'Añade lotes con fecha de caducidad SIN romper los tests existentes y SIN modificar test_inventario.py:\n'
               '- anadir(sku, cantidad, caduca=None): caduca es un datetime.date opcional; cada llamada crea un lote.\n'
               '- retirar(sku, cantidad): consume primero los lotes que caducan antes (FEFO); los lotes sin fecha, al final.\n'
               '- cantidad(sku) y total() siguen sumando todo.\n'
               '- caducados(fecha) -> dict {sku: cantidad} con los lotes cuya caducidad es anterior a esa fecha.\n'
               '- guardar(ruta) escribe JSON con "version": 2 y los lotes; cargar(ruta) lee la versión 2 Y también el formato '
               'antiguo {"items": {sku: cantidad}} (como datos_v1.json), tratando esas cantidades como lotes sin fecha.\n'
               'Añade tests nuevos para todo esto y deja todos los tests en verde.' + SOLO},
    {'id': 'pypi', 'tipo': 'investigacion', 'reps': 2, 'comprobar': comp_pypi, 'timeout_min': 10,
     'prompt': 'Busca en internet (NO respondas de memoria; consulta PyPI): la versión más reciente publicada HOY de los '
               'paquetes de Python fastapi, pydantic y httpx, y la fecha (YYYY-MM-DD) en que se publicó esa versión de fastapi. '
               'Devuelve SOLO este JSON: {"fastapi": "...", "pydantic": "...", "httpx": "...", "fastapi_fecha": "YYYY-MM-DD"}' + SOLO},
    {'id': 'node', 'tipo': 'investigacion', 'reps': 2, 'comprobar': comp_node, 'timeout_min': 10,
     'prompt': 'Busca en internet (NO respondas de memoria): la versión más reciente de Node.js que sea LTS, su nombre clave '
               'de LTS y su fecha de publicación, y la última versión publicada del paquete npm "vite". '
               'Devuelve SOLO este JSON: {"node_lts": "vX.Y.Z", "nombre_clave": "...", "fecha": "YYYY-MM-DD", "vite": "X.Y.Z"}' + SOLO},
    {'id': 'tabla', 'tipo': 'front', 'reps': 2, 'comprobar': comp_front, 'timeout_min': 12,
     'prompt': FRONT_PROMPT + '\nSi no puedes crear ficheros, devuelve el HTML completo en un único bloque ```html.' + SOLO},
]

# Backend de ratón y teclado de pc-control sin dependencias (Win32 SendInput).
# Proceso persistente: lee una orden JSON por línea en stdin y responde una línea JSON en stdout.
#   {"id":1,"op":"loc"}                                   -> {"id":1,"ok":true,"x":..,"y":..}
#   {"id":2,"op":"move","x":100,"y":200}
#   {"id":3,"op":"button","button":"left","action":"click","count":2}   (action: press|release|click)
#   {"id":4,"op":"scroll","amount":3,"horizontal":false}               (positivo = abajo / derecha)
#   {"id":5,"op":"type","text":"hola"}
#   {"id":6,"op":"key","key":"ctrl","action":"press"}                  (press|release)
#   {"id":7,"op":"keys","keys":["ctrl","c"]}                           (pulsa en orden, suelta al revés)
#   {"id":8,"op":"valid","keys":["ctrl","x"]}                          (comprueba nombres)
#   {"id":9,"op":"apps"}                                  -> {"apps":[{pid,name,title}],"front":"..."}
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class Entrada {
  [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT { public int dx, dy; public uint mouseData, dwFlags, time; public IntPtr dwExtraInfo; }
  [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr dwExtraInfo; }
  [StructLayout(LayoutKind.Explicit)] public struct UNION { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public UNION u; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x, y; }
  [DllImport("user32.dll", SetLastError=true)] static extern uint SendInput(uint n, INPUT[] inputs, int size);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern short VkKeyScanW(char c);
  static void Enviar(INPUT i) { SendInput(1, new INPUT[] { i }, Marshal.SizeOf(typeof(INPUT))); }
  public static void Raton(uint flags, uint data) {
    var i = new INPUT(); i.type = 0; i.u.mi.dwFlags = flags; i.u.mi.mouseData = data; Enviar(i);
  }
  public static void Tecla(ushort vk, bool soltar, bool extendida) {
    var i = new INPUT(); i.type = 1; i.u.ki.wVk = vk;
    i.u.ki.dwFlags = (soltar ? 2u : 0u) | (extendida ? 1u : 0u); Enviar(i);
  }
  public static void Unicode(char c) {
    foreach (bool soltar in new bool[] { false, true }) {
      var i = new INPUT(); i.type = 1; i.u.ki.wScan = c; i.u.ki.dwFlags = 4u | (soltar ? 2u : 0u); Enviar(i);
    }
  }
  public static uint Pid() { uint p; GetWindowThreadProcessId(GetForegroundWindow(), out p); return p; }
}
'@
[Entrada]::SetProcessDPIAware() | Out-Null

$VK = @{ ctrl=0x11; control=0x11; alt=0x12; shift=0x10; win=0x5B; cmd=0x5B; meta=0x5B; super=0x5B;
  enter=0x0D; return=0x0D; tab=0x09; escape=0x1B; esc=0x1B; backspace=0x08; delete=0x2E; del=0x2E; insert=0x2D;
  up=0x26; down=0x28; left=0x25; right=0x27; pageup=0x21; pagedown=0x22; home=0x24; end=0x23; space=0x20;
  capslock=0x14; printscreen=0x2C; menu=0x5D }
for ($n = 1; $n -le 24; $n++) { $VK["f$n"] = 0x6F + $n }
$EXT = @(0x2E, 0x2D, 0x26, 0x28, 0x25, 0x27, 0x21, 0x22, 0x24, 0x23, 0x5B, 0x5D, 0x2C)

function Codigo([string]$k) {
  $k = $k.ToLowerInvariant()
  if ($VK.ContainsKey($k)) { return [int]$VK[$k] }
  if ($k.Length -eq 1) {
    $c = [char]$k
    if ($c -match '[a-z]') { return [int][char]$k.ToUpperInvariant() }
    if ($c -match '[0-9]') { return [int]$c }
    $r = [Entrada]::VkKeyScanW($c)
    if ($r -ne -1) { return [int]($r -band 0xFF) }
  }
  throw "Tecla desconocida: $k"
}
function Pulsar([string]$k, [bool]$soltar) { $v = Codigo $k; [Entrada]::Tecla([uint16]$v, $soltar, ($EXT -contains $v)) }

function U32([int]$v) { [BitConverter]::ToUInt32([BitConverter]::GetBytes($v), 0) }
$BOTON = @{ left = @(0x2, 0x4); right = @(0x8, 0x10); middle = @(0x20, 0x40) }

while ($true) {
  $linea = [Console]::In.ReadLine()
  if ($null -eq $linea) { break }
  if (-not $linea.Trim()) { continue }
  $r = @{ ok = $true }
  try {
    $o = $linea | ConvertFrom-Json
    $r.id = $o.id
    switch ($o.op) {
      'loc' { $p = New-Object Entrada+POINT; [Entrada]::GetCursorPos([ref]$p) | Out-Null; $r.x = $p.x; $r.y = $p.y }
      'move' { [Entrada]::SetCursorPos([int]$o.x, [int]$o.y) | Out-Null }
      'button' {
        $b = $BOTON[[string]$o.button]; if (-not $b) { throw "Botón desconocido: $($o.button)" }
        $n = if ($o.count) { [int]$o.count } else { 1 }
        switch ($o.action) {
          'press' { [Entrada]::Raton($b[0], 0) }
          'release' { [Entrada]::Raton($b[1], 0) }
          default { for ($i = 0; $i -lt $n; $i++) { [Entrada]::Raton($b[0], 0); [Entrada]::Raton($b[1], 0); Start-Sleep -Milliseconds 30 } }
        }
      }
      'scroll' {
        $d = [int]$o.amount * 120
        if ($o.horizontal) { [Entrada]::Raton(0x1000, (U32 $d)) }
        else { [Entrada]::Raton(0x800, (U32 (-$d))) }
      }
      'type' {
        foreach ($c in ([string]$o.text).ToCharArray()) {
          if ($c -eq "`n") { [Entrada]::Tecla(0x0D, $false, $false); [Entrada]::Tecla(0x0D, $true, $false) }
          elseif ($c -ne "`r") { [Entrada]::Unicode($c) }
          Start-Sleep -Milliseconds 4
        }
      }
      'key' { Pulsar ([string]$o.key) ($o.action -eq 'release') }
      'keys' {
        $ks = @($o.keys)
        foreach ($k in $ks) { Pulsar ([string]$k) $false }
        [array]::Reverse($ks)
        foreach ($k in $ks) { Pulsar ([string]$k) $true }
      }
      'valid' { foreach ($k in @($o.keys)) { Codigo ([string]$k) | Out-Null } }
      'apps' {
        $r.apps = @(Get-Process | Where-Object { $_.MainWindowHandle -ne 0 } |
          ForEach-Object { @{ pid = $_.Id; name = $_.ProcessName; title = $_.MainWindowTitle } })
        $fp = [Entrada]::Pid()
        $fr = Get-Process -Id $fp -ErrorAction SilentlyContinue
        $r.front = if ($fr) { "$($fr.ProcessName) — $($fr.MainWindowTitle)" } else { '?' }
      }
      default { throw "Orden desconocida: $($o.op)" }
    }
  } catch { $r.ok = $false; $r.error = $_.Exception.Message }
  [Console]::Out.WriteLine(($r | ConvertTo-Json -Compress -Depth 4))
  [Console]::Out.Flush()
}

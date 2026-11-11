param([string]$Out, [int]$MaxW = 1366, [int]$Quality = 75)
# Captura toda la pantalla (escritorio virtual), la reduce a $MaxW de ancho y la guarda en JPEG.
# Imprime: anchoOriginal altoOriginal anchoFinal altoFinal origenX origenY
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type -Namespace W -Name Dpi -MemberDefinition '[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();'
[W.Dpi]::SetProcessDPIAware() | Out-Null
$v = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $v.Width, $v.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($v.X, $v.Y, 0, 0, $bmp.Size)
$g.Dispose()
$w = [Math]::Min($MaxW, $v.Width); $h = [int][Math]::Round($v.Height * $w / $v.Width)
$small = New-Object System.Drawing.Bitmap $w, $h
$g2 = [System.Drawing.Graphics]::FromImage($small)
$g2.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g2.DrawImage($bmp, 0, 0, $w, $h)
$g2.Dispose(); $bmp.Dispose()
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality), ([long]$Quality)
$small.Save($Out, $codec, $ep)
$small.Dispose()
"$($v.Width) $($v.Height) $w $h $($v.X) $($v.Y)"

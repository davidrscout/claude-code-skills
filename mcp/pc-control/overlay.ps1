param([string]$Beat, [int]$ParentPid, [int]$IdleSec = 8, [switch]$Visible)
# Aviso mientras un agente de IA controla el PC (inspirado en el aviso de la app de escritorio de Claude):
#  - resplandor naranja (217,119,87) por dentro de los bordes, 3 sombras inset 50/100/150 px, latido de 2 s
#  - placa «Un agente de IA está usando tu ordenador» que aparece en el centro (x1,4), aguanta y se va a la esquina (6 s)
#  - extra: punto naranja que acompaña al ratón
# Ventanas con alfa por píxel, no se pueden pulsar, no roban el foco y no salen en capturas (salvo -Visible).
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type -ReferencedAssemblies System.Windows.Forms, System.Drawing -TypeDefinition @'
using System; using System.Drawing; using System.Drawing.Drawing2D; using System.Drawing.Imaging;
using System.Windows.Forms; using System.Runtime.InteropServices;

public class Capa : Form {
  [StructLayout(LayoutKind.Sequential)] public struct PT { public int x, y; public PT(int a,int b){x=a;y=b;} }
  [StructLayout(LayoutKind.Sequential)] public struct SZ { public int cx, cy; public SZ(int a,int b){cx=a;cy=b;} }
  [StructLayout(LayoutKind.Sequential, Pack=1)] public struct BF { public byte Op, Flags, Alpha, Format; }
  [DllImport("user32.dll")] static extern bool UpdateLayeredWindow(IntPtr h, IntPtr dst, ref PT pos, ref SZ size, IntPtr src, ref PT srcPos, int key, ref BF bf, int flags);
  [DllImport("user32.dll", EntryPoint="UpdateLayeredWindow")] static extern bool ULWAlpha(IntPtr h, IntPtr dst, IntPtr pos, IntPtr size, IntPtr src, IntPtr srcPos, int key, ref BF bf, int flags);
  [DllImport("user32.dll")] static extern IntPtr GetDC(IntPtr h);
  [DllImport("user32.dll")] static extern int ReleaseDC(IntPtr h, IntPtr dc);
  [DllImport("gdi32.dll")] static extern IntPtr CreateCompatibleDC(IntPtr dc);
  [DllImport("gdi32.dll")] static extern bool DeleteDC(IntPtr dc);
  [DllImport("gdi32.dll")] static extern IntPtr SelectObject(IntPtr dc, IntPtr o);
  [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr o);
  [DllImport("user32.dll")] static extern bool SetWindowDisplayAffinity(IntPtr h, uint a);
  public static bool Visible_ = false;
  public Capa() { FormBorderStyle = FormBorderStyle.None; ShowInTaskbar = false; TopMost = true; StartPosition = FormStartPosition.Manual; }
  protected override bool ShowWithoutActivation { get { return true; } }
  protected override CreateParams CreateParams { get { var cp = base.CreateParams; cp.ExStyle |= 0x80000 | 0x20 | 0x80 | 0x8000000 | 0x8; return cp; } }
  protected override void OnHandleCreated(EventArgs e) { base.OnHandleCreated(e); if (!Visible_) SetWindowDisplayAffinity(Handle, 0x11); }
  // Pinta el bitmap (ARGB) en (x,y) con opacidad global a (0..1)
  public void Poner(Bitmap bmp, int x, int y, double a) {
    IntPtr sdc = GetDC(IntPtr.Zero), mdc = CreateCompatibleDC(sdc), hb = bmp.GetHbitmap(Color.FromArgb(0)), old = SelectObject(mdc, hb);
    var pos = new PT(x, y); var sz = new SZ(bmp.Width, bmp.Height); var z = new PT(0, 0);
    var bf = new BF { Op = 0, Flags = 0, Alpha = (byte)Math.Max(0, Math.Min(255, a * 255)), Format = 1 };
    UpdateLayeredWindow(Handle, sdc, ref pos, ref sz, mdc, ref z, 0, ref bf, 2);
    SelectObject(mdc, old); DeleteObject(hb); DeleteDC(mdc); ReleaseDC(IntPtr.Zero, sdc);
  }
  // Cambia solo la opacidad global (barato)
  public void Alfa(double a) { var bf = new BF { Op = 0, Flags = 0, Alpha = (byte)Math.Max(0, Math.Min(255, a * 255)), Format = 1 }; ULWAlpha(Handle, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, 0, ref bf, 2); }
}

public static class Aviso {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  static readonly Color Clay = Color.FromArgb(217, 119, 87);
  static Capa glow, badge, punto; static Bitmap glowBmp; static Rectangle V;
  static DateTime t0; static DateTime? cierre = null; static string beat; static int pid, idle;
  public static string Texto = "Un agente de IA está usando tu ordenador";

  static double Phi(double z) { // CDF normal (aprox. Abramowitz-Stegun)
    double t = 1 / (1 + 0.2316419 * Math.Abs(z)), d = 0.3989423 * Math.Exp(-z * z / 2);
    double p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    return z > 0 ? 1 - p : p;
  }
  // box-shadow inset 0 0 Bpx: la sombra es el exterior difuminado con sigma = B/2
  static Bitmap HacerGlow(int W, int H) {
    double[] blur = { 65, 115, 165 }, al = { 0.7, 0.5, 0.2 }; // fotograma del 50 % del latido (el más intenso)
    var fx = new double[3][]; var fy = new double[3][];
    for (int i = 0; i < 3; i++) {
      double s = blur[i] / 2; fx[i] = new double[W]; fy[i] = new double[H];
      for (int x = 0; x < W; x++) fx[i][x] = Phi((x + 0.5) / s) + Phi((W - x - 0.5) / s) - 1;
      for (int y = 0; y < H; y++) fy[i][y] = Phi((y + 0.5) / s) + Phi((H - y - 0.5) / s) - 1;
    }
    var px = new int[W * H];
    for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) {
      double keep = 1;
      for (int i = 0; i < 3; i++) keep *= 1 - al[i] * (1 - fx[i][x] * fy[i][y]);
      int a = (int)Math.Round((1 - keep) * 255);
      px[y * W + x] = (a << 24) | (217 << 16) | (119 << 8) | 87;
    }
    var bmp = new Bitmap(W, H, PixelFormat.Format32bppArgb);
    var bd = bmp.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
    Marshal.Copy(px, 0, bd.Scan0, px.Length); bmp.UnlockBits(bd);
    return bmp;
  }
  // cubic-bezier(0.4, 0, 0.2, 1)
  static double Ease(double x) {
    double lo = 0, hi = 1, t = x;
    for (int i = 0; i < 30; i++) { t = (lo + hi) / 2; double bx = 3 * (1 - t) * (1 - t) * t * 0.4 + 3 * (1 - t) * t * t * 0.2 + t * t * t; if (bx < x) lo = t; else hi = t; }
    return 3 * (1 - t) * t * t * 1 + t * t * t;
  }
  static GraphicsPath Pastilla(RectangleF r) {
    var p = new GraphicsPath(); float d = r.Height;
    p.AddArc(r.X, r.Y, d, d, 90, 180); p.AddArc(r.Right - d, r.Y, d, d, 270, 180); p.CloseFigure(); return p;
  }
  static void PintarBadge(double t) {
    // 0-5 %: aparece; 5-88 %: quieto en el centro x1,4; 88-100 %: a la esquina, x0,8, se apaga
    double op, sc, cxF, cyF, tx; double T = t / 6.0;
    if (T >= 1) { badge.Alfa(0); return; }
    if (T < 0.05) { double e = Ease(T / 0.05); op = e; sc = 1.4; cxF = 0.5; cyF = 0.5; tx = -0.5; }
    else if (T < 0.88) { op = 1; sc = 1.4; cxF = 0.5; cyF = 0.5; tx = -0.5; }
    else { double e = Ease((T - 0.88) / 0.12); op = 1 - e; sc = 1.4 - 0.6 * e; cxF = -1; cyF = e; tx = -0.5 + 0.5 * e; }
    using (var f = new Font("Segoe UI Semibold", 13f, GraphicsUnit.Pixel)) {
      var meas = TextRenderer.MeasureText(Texto, f);
      float w = 16 + 8 + 8 + meas.Width + 16 - 6, h = 34; // padding 8/16, punto 8, hueco 8
      float left, top;
      if (cxF >= 0) { left = V.Width * 0.5f; top = V.Height * 0.5f; }
      else { left = (float)(V.Width * 0.5 + (V.Width - 280 - V.Width * 0.5) * cyF); top = (float)(V.Height * 0.5 + (40 - V.Height * 0.5) * cyF); }
      float ccx = left + w / 2 + (float)(tx * w), ccy = top + h / 2 + (float)(tx * h);
      int bw = (int)Math.Ceiling(w * sc) + 6, bh = (int)Math.Ceiling(h * sc) + 6;
      using (var bmp = new Bitmap(bw, bh, PixelFormat.Format32bppArgb))
      using (var g = Graphics.FromImage(bmp)) {
        g.SmoothingMode = SmoothingMode.AntiAlias; g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAliasGridFit;
        g.TranslateTransform(3, 3); g.ScaleTransform((float)sc, (float)sc);
        using (var path = Pastilla(new RectangleF(0, 0, w, h))) {
          using (var b = new SolidBrush(Color.FromArgb(242, 255, 247, 242))) g.FillPath(b, path);
          using (var pen = new Pen(Color.FromArgb(51, 217, 119, 87), 1f)) g.DrawPath(pen, path);
        }
        double ph = ((DateTime.Now - t0).TotalSeconds % 1.8) / 1.8, k = 0.5 - 0.5 * Math.Cos(2 * Math.PI * ph);
        float ds = (float)(8 * (1 - 0.3 * k)); int da = (int)(255 * (1 - 0.5 * k));
        using (var b = new SolidBrush(Color.FromArgb(da, Clay))) g.FillEllipse(b, 16 + (8 - ds) / 2, h / 2 - ds / 2, ds, ds);
        using (var b = new SolidBrush(Clay)) g.DrawString(Texto, f, b, 16 + 8 + 8 - 3, (h - meas.Height) / 2f);
        g.ResetTransform();
        badge.Poner(bmp, V.X + (int)(ccx - bw / 2f), V.Y + (int)(ccy - bh / 2f), op);
      }
    }
  }
  static Bitmap puntoBmp;
  static void HacerPunto() {
    puntoBmp = new Bitmap(30, 30, PixelFormat.Format32bppArgb);
    using (var g = Graphics.FromImage(puntoBmp)) {
      g.SmoothingMode = SmoothingMode.AntiAlias;
      for (int r = 14; r > 6; r--) using (var b = new SolidBrush(Color.FromArgb((int)(70 * (1 - (r - 6) / 8.0)), Clay))) g.FillEllipse(b, 15 - r, 15 - r, 2 * r, 2 * r);
      using (var b = new SolidBrush(Clay)) g.FillEllipse(b, 9, 9, 12, 12);
      using (var pen = new Pen(Color.FromArgb(240, 255, 247, 242), 2f)) g.DrawEllipse(pen, 9, 9, 12, 12);
    }
  }
  public static void Run(string b, int p, int i, bool vis) {
    beat = b; pid = p; idle = i; Capa.Visible_ = vis; V = SystemInformation.VirtualScreen;
    glowBmp = HacerGlow(V.Width, V.Height); HacerPunto();
    glow = new Capa(); badge = new Capa(); punto = new Capa();
    glow.Show(); badge.Show(); punto.Show();
    glow.Poner(glowBmp, V.X, V.Y, 0); badge.Alfa(0);
    glowBmp.Dispose(); glowBmp = null; GC.Collect(); // la ventana ya guarda su copia
    var c0 = Cursor.Position; punto.Poner(puntoBmp, c0.X + 6, c0.Y + 14, 0);
    t0 = DateTime.Now;
    var tm = new Timer(); tm.Interval = 16; int n = 0; Point ult = new Point(-1, -1);
    tm.Tick += (s, e) => {
      double t = (DateTime.Now - t0).TotalSeconds;
      if (++n % 30 == 0 && cierre == null) {
        bool vivo = true; try { System.Diagnostics.Process.GetProcessById(pid); } catch { vivo = false; }
        double edad = 999; try { edad = (DateTime.Now - System.IO.File.GetLastWriteTime(beat)).TotalSeconds; } catch {}
        if (!vivo || edad > idle) cierre = DateTime.Now;
        glow.TopMost = true; badge.TopMost = true; punto.TopMost = true;
      }
      double fade = Math.Min(1, t / 0.3);
      if (cierre != null) { double c = (DateTime.Now - cierre.Value).TotalSeconds; fade = Math.Max(0, 1 - c / 0.32); if (c > 0.35) { Application.Exit(); return; } }
      double puls = 0.5 - 0.5 * Math.Cos(2 * Math.PI * t / 2.0); // 0 en reposo, 1 a mitad de latido
      glow.Alfa(fade * (0.7 + 0.3 * puls));
      if (t < 6.1) PintarBadge(t);
      var cp = Cursor.Position;
      if (cp != ult || n % 4 == 0) { punto.Poner(puntoBmp, cp.X + 6, cp.Y + 14, fade * (0.75 + 0.25 * puls)); ult = cp; }
    };
    tm.Start();
    Application.Run();
  }
}
'@
[Aviso]::SetProcessDPIAware() | Out-Null
[Aviso]::Run($Beat, $ParentPid, $IdleSec, $Visible.IsPresent)

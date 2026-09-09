Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dir  = Join-Path $root "icons"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$blue = [System.Drawing.Color]::FromArgb(255, 31, 111, 235)
$white = [System.Drawing.Color]::FromArgb(255, 255, 255, 255)
$ink   = [System.Drawing.Color]::FromArgb(255, 206, 218, 234)

function RoundRect($g, $brush, $x, $y, $w, $h, $r) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $r * 2
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    $g.FillPath($brush, $p)
    $p.Dispose()
}

# maskable=false -> full bleed; maskable=true -> content inside 80% safe zone
function DrawIcon([int]$size, [bool]$maskable, [string]$outPath) {
    $bmp = New-Object System.Drawing.Bitmap($size, $size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

    $bg = New-Object System.Drawing.SolidBrush($blue)
    if ($maskable) {
        $g.FillRectangle($bg, 0, 0, $size, $size)
    } else {
        RoundRect $g $bg 0 0 $size $size ([int]($size * 0.22))
    }

    # newspaper sheet
    $k = if ($maskable) { 0.62 } else { 0.60 }
    $pw = [int]($size * $k)
    $ph = [int]($pw * 1.24)
    $px = [int](($size - $pw) / 2)
    $py = [int](($size - $ph) / 2)
    RoundRect $g (New-Object System.Drawing.SolidBrush($white)) $px $py $pw $ph ([int]($size * 0.05))

    # masthead bar
    $mh = [int]($ph * 0.16)
    $mx = $px + [int]($pw * 0.10)
    $mw = [int]($pw * 0.80)
    RoundRect $g (New-Object System.Drawing.SolidBrush($blue)) $mx ($py + [int]($ph * 0.12)) $mw $mh ([int]($mh / 2))

    # text lines
    $lx = $mx
    $lw = $mw
    $lh = [int]($size * 0.032)
    $ly = $py + [int]($ph * 0.12) + $mh + [int]($ph * 0.07)
    $gap = [int]($ph * 0.105)
    $brushInk = New-Object System.Drawing.SolidBrush($ink)
    for ($i = 0; $i -lt 4; $i++) {
        $w = if ($i -eq 3) { [int]($lw * 0.55) } else { $lw }
        $g.FillRectangle($brushInk, $lx, $ly, $w, $lh)
        $ly += $gap
    }

    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose(); $bmp.Dispose()
    Write-Output ("wrote " + $outPath + " (" + $size + "px)")
}

DrawIcon 512 $false (Join-Path $dir "icon-512.png")
DrawIcon 192 $false (Join-Path $dir "icon-192.png")
DrawIcon 512 $true  (Join-Path $dir "maskable-512.png")
DrawIcon 180 $false (Join-Path $dir "apple-touch-icon.png")
DrawIcon 32  $false (Join-Path $dir "favicon-32.png")

# verify
Get-ChildItem (Join-Path $dir "*.png") | ForEach-Object {
    $im = [System.Drawing.Image]::FromFile($_.FullName)
    Write-Output ("  " + $_.Name + " -> " + $im.Width + "x" + $im.Height)
    $im.Dispose()
}

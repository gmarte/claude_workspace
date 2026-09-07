# render_preview.ps1 — Export every slide of a PPTX to PNG using the installed PowerPoint (COM).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File render_preview.ps1 -Pptx "deck.pptx" -OutDir "C:\TEMP\preview" [-Width 1280]
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$Width = 1280
)

$Pptx = (Resolve-Path $Pptx).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path

$app = New-Object -ComObject PowerPoint.Application
$ownedApp = ($app.Presentations.Count -eq 0)

# Open(FileName, ReadOnly, Untitled, WithWindow)
$pres = $app.Presentations.Open($Pptx, 1, 0, 0)
try {
    $h = [int]($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
    $i = 1
    foreach ($s in $pres.Slides) {
        $out = Join-Path $OutDir ("slide{0:D2}.png" -f $i)
        $s.Export($out, "PNG", $Width, $h)
        Write-Output $out
        $i++
    }
}
finally {
    $pres.Close()
    if ($ownedApp) { $app.Quit() }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pres) | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}

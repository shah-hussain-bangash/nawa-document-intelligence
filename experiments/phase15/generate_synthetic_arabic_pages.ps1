param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Output directory already exists.' }
Add-Type -AssemblyName System.Drawing
New-Item -ItemType Directory -Path $OutputDirectory -ErrorAction Stop | Out-Null
$cases = @(
    @{ id='synthetic-a'; supplier='شركة النخيل للتقنية'; subtotal='١٢٠٠٫٠٠'; vat='٦٠٫٠٠'; total='١٢٦٠٫٠٠' },
    @{ id='synthetic-b'; supplier='شركة المدى للخدمات'; subtotal='٧٨٠٫٠٠'; vat='٣٩٫٠٠'; total='٨١٩٫٠٠' }
)
$manifest = @()
foreach ($case in $cases) {
    $image = [System.Drawing.Bitmap]::new(1600, 1050)
    $graphics = [System.Drawing.Graphics]::FromImage($image)
    $font = [System.Drawing.Font]::new('Arial', 34, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $format = [System.Drawing.StringFormat]::new()
    try {
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        $format.FormatFlags = [System.Drawing.StringFormatFlags]::DirectionRightToLeft
        $lines = @('عرض سعر تجريبي', "اسم المورد: $($case.supplier)", 'العملة: AED',
            "المجموع الفرعي: $($case.subtotal)", 'نسبة الضريبة: ٥',
            "قيمة الضريبة: $($case.vat)", "الإجمالي شامل الضريبة: $($case.total)", 'بيانات تجريبية فقط')
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $rect = [System.Drawing.RectangleF]::new(100, (80 + 105 * $i), 1400, 70)
            $graphics.DrawString($lines[$i], $font, [System.Drawing.Brushes]::Black, $rect, $format)
        }
        $path = Join-Path $OutputDirectory ($case.id + '.png')
        $image.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
        $manifest += [ordered]@{ id=$case.id; image=($case.id + '.png');
            sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();
            lines=$lines; fields=[ordered]@{supplier=$case.supplier; currency='AED'; subtotal=$case.subtotal;
                vat_rate='٥'; vat_amount=$case.vat; total=$case.total} }
    } finally {
        $format.Dispose(); $font.Dispose(); $graphics.Dispose(); $image.Dispose()
    }
}
$result = [ordered]@{ status='human_review_required'; scope='Two generated synthetic pages, not independently reviewed or representative.';
    generator='Windows GDI+ and Arial; layout and font depend on the local system.'; cases=$manifest }
$manifestFile = Join-Path $OutputDirectory 'manifest.json'
$json = $result | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($manifestFile, $json, [System.Text.UTF8Encoding]::new($false))
Write-Output 'Two synthetic pages generated; human review required.'

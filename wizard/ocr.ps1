param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)
# 本地图片 OCR（Windows.Media.Ocr，离线；使用用户配置语言）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
    $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
    $null = [Windows.Storage.Streams.IRandomAccessStreamWithContentType, Windows.Storage, ContentType = WindowsRuntime]
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
    $null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics, ContentType = WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Foundation.FoundationContract, Windows.Foundation, ContentType = WindowsRuntime]

    $awaiters = [System.WindowsRuntimeSystemExtensions].GetMethods() |
        Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 }
    $generic = $awaiters[0]

    function Await-Op($op, $resultType) {
        $task = $generic.MakeGenericMethod($resultType).Invoke($null, @($op))
        $task.Wait(-1) | Out-Null
        $task.Result
    }

    $file = Await-Op ([Windows.Storage.StorageFile]::GetFileFromPathAsync($Path)) ([Windows.Storage.StorageFile])
    $stream = Await-Op ($file.OpenReadAsync()) ([Windows.Storage.Streams.IRandomAccessStreamWithContentType])
    $decoder = Await-Op ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await-Op ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

    $fmt = $bmp.BitmapPixelFormat
    if ($fmt -ne 'Gray8' -and $fmt -ne 'Bgra8') {
        $bmp = [Windows.Graphics.Imaging.SoftwareBitmap]::Convert($bmp, [Windows.Graphics.Imaging.BitmapPixelFormat]::Gray8)
    }

    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) { throw '无法创建 OCR 引擎（本机未安装识别语言包）' }

    $result = Await-Op ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
    Write-Output ([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($result.Text)))
} catch {
    Write-Error $_.Exception.Message
    exit 1
}

# ============================================
# СТ СТ Т Т
# апуск от имени администратора для лучшего результата
# ============================================

Write-Host "УС СТ У" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

# 1. амять до очистки
Write-Host "`n[1] роверяем текущую память..." -ForegroundColor White
$memoryBefore = Get-CimInstance Win32_OperatingSystem
$freeBefore = [math]::Round($memoryBefore.FreePhysicalMemory / 1048576, 2)  # онвертируем в 
Write-Host "   Свободно: $freeBefore " -ForegroundColor Gray

# 2. обавляем функцию очистки
Write-Host "`n[2] одготавливаем очистку..." -ForegroundColor White
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class MemoryCleaner {
    [DllImport("psapi.dll")]
    public static extern bool EmptyWorkingSet(IntPtr hProcess);
}
"@

# 3. чищаем процессы (кроме системных)
Write-Host "`n[3] чищаем процессы..." -ForegroundColor White
$systemProcesses = @("Idle", "System", "svchost", "csrss", "wininit", "services", "lsass", "winlogon")
$cleanedCount = 0

foreach ($proc in Get-Process) {
    if ($proc.Name -notin $systemProcesses -and $proc.Handle -ne [IntPtr]::Zero) {
        try {
            [MemoryCleaner]::EmptyWorkingSet($proc.Handle)
            $cleanedCount++
        } catch {
            # гнорируем ошибки
        }
    }
}

Write-Host "   бработано процессов: $cleanedCount" -ForegroundColor Gray

# 4. Сборка мусора .NET
Write-Host "`n[4] апуск сборки мусора..." -ForegroundColor White
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()
[System.GC]::Collect()

# 5. амять после очистки
Write-Host "`n[5] роверяем результат..." -ForegroundColor White
$memoryAfter = Get-CimInstance Win32_OperatingSystem
$freeAfter = [math]::Round($memoryAfter.FreePhysicalMemory / 1048576, 2)
$freed = $freeAfter - $freeBefore

# 6. ыводим результаты
Write-Host "`n" + ("="*40) -ForegroundColor Cyan
Write-Host "УТТЫ СТ:" -ForegroundColor Cyan
Write-Host ("="*40) -ForegroundColor Cyan

Write-Host "о очистки:   $freeBefore " -ForegroundColor Gray
Write-Host "осле очистки: $freeAfter " -ForegroundColor Green

if ($freed -gt 0) {
    Write-Host "свобождено:   $freed " -ForegroundColor Yellow
    Write-Host "Статус: УСШ" -ForegroundColor Green
} elseif ($freed -eq 0) {
    Write-Host "свобождено:   0 " -ForegroundColor Gray
    Write-Host "Статус: Т " -ForegroundColor Gray
} else {
    Write-Host "свобождено:   $freed " -ForegroundColor Red
    Write-Host "Статус: Т УШС" -ForegroundColor Red
}

Write-Host ("="*40) -ForegroundColor Cyan
Write-Host "СТ Ш!" -ForegroundColor Cyan

# ауза (если запускается не из консоли)
if ($Host.Name -eq "ConsoleHost") {
    Write-Host "`nажмите любую клавишу для выхода..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

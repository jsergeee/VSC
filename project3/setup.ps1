# Скрипт установки и настройки
param(
    [switch]$InstallNmap,
    [switch]$CreateTask,
    [string]$TaskTime = "02:00"
)

Write-Host "=== Настройка автоматического сканера сети ===" -ForegroundColor Cyan

# Проверка прав администратора
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Требуются права администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора"
    pause
    exit 1
}

# Установка nmap
if ($InstallNmap) {
    Write-Host "`nУстановка Nmap..." -ForegroundColor Yellow
    
    # Проверка наличия winget
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install nmap.nmap
    } else {
        Write-Host "Winget не найден. Установите nmap вручную:" -ForegroundColor Yellow
        Write-Host "Скачайте с: https://nmap.org/download.html" -ForegroundColor Yellow
    }
}

# Проверка Python зависимостей
Write-Host "`nПроверка Python зависимостей..." -ForegroundColor Yellow
$requirements = @"
configparser>=5.3.0
"@

$requirements | Out-File -FilePath "requirements.txt" -Encoding UTF8
pip install -r requirements.txt

# Создание задачи в планировщике
if ($CreateTask) {
    Write-Host "`nСоздание задачи в планировщике..." -ForegroundColor Yellow
    
    $taskName = "Network Scanner\Daily Network Scan"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\run_scanner.bat`""
    
    $trigger = New-ScheduledTaskTrigger -Daily -At $TaskTime
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Password -RunLevel Highest
    
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable -WakeToRun
    
    Register-ScheduledTask -TaskName $taskName `
        -Action $action -Trigger $trigger `
        -Principal $principal -Settings $settings `
        -Description "Автоматическое ежедневное сканирование сети"
    
    Write-Host "Задача создана: $taskName" -ForegroundColor Green
}

Write-Host "`n=== Настройка завершена ===" -ForegroundColor Green
Write-Host "Конфигурация: config.ini" -ForegroundColor Yellow
Write-Host "Запуск вручную: .\run_scanner.bat" -ForegroundColor Yellow
Write-Host "Или: python scan-net.py" -ForegroundColor Yellow
pause
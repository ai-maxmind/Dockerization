function Stop-AllContainers {
    Write-Host "`nStopping all containers..."
    docker ps -aq | ForEach-Object { docker stop $_ }
    Write-Host "Done stopping!"
}

function Remove-AllContainers {
    Write-Host "`nRemoving all containers..."
    docker ps -aq | ForEach-Object { docker rm -f $_ }
    Write-Host "Done removing!"
}

function Remove-AllImages {
    Write-Host "`nRemoving all images..."
    docker images -aq | ForEach-Object { docker rmi -f $_ }
    Write-Host "Done removing!"
}

function Remove-AllVolumes {
    Write-Host "`nRemoving all volumes..."
    docker volume ls -q | ForEach-Object { docker volume rm $_ }
    Write-Host "Done removing!"
}

function Remove-Networks {
    Write-Host "`nRemoving unused networks..."
    docker network prune -f
    Write-Host "Done!"
}

function Prune-Builder {
    Write-Host "`nPruning builder cache..."
    docker builder prune -a -f
    Write-Host "Done!"
}

function Reset-AllDocker {
    Stop-AllContainers
    Remove-AllContainers
    Remove-AllImages
    Remove-AllVolumes
    Remove-Networks
    Prune-Builder
    Write-Host "`nAll done! Docker is now clean."
}

function Run-All {
    Write-Host "`nRunning ALL cleanup tasks..."
    Stop-AllContainers
    Remove-AllContainers
    Remove-AllImages
    Remove-AllVolumes
    Remove-Networks
    Prune-Builder
    Write-Host "`nALL tasks completed!"
}

function Uninstall-Docker {
    Write-Host "`nUninstalling Docker Desktop..."
    $dockerApp = winget list | Where-Object { $_ -match "Docker.DockerDesktop" }
    if ($dockerApp) {
        Write-Host "Found Docker Desktop. Starting uninstall..."
        winget uninstall --id Docker.DockerDesktop -e --silent
        Write-Host "Docker Desktop uninstallation triggered."
    } else {
        Write-Host "Docker Desktop not found via winget. You may need to uninstall manually."
    }

    Write-Host "Removing leftover Docker data folders..."
    $paths = @(
        "$env:ProgramData\DockerDesktop",
        "$env:ProgramData\Docker",
        "$env:LocalAppData\Docker",
        "$env:AppData\Docker",
        "$env:AppData\Docker Desktop",
        "$env:UserProfile\.docker"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Remove-Item -Recurse -Force $p
            Write-Host "Deleted $p"
        }
    }
    Write-Host "`nDocker uninstallation completed."
}

function Install-Docker {
    [CmdletBinding()]
    param(
        [string] $WingetId = "Docker.DockerDesktop",
        [string] $Channel = "Stable",                 
        [string] $DesiredVersion = "",                
        [switch] $SkipWSLSetup,                       
        [switch] $SkipSettings,                      
        [switch] $NoSmokeTest                       
    )

    Write-Host "`n[Install-Docker] Starting Docker Desktop installation for Windows..." -ForegroundColor Cyan

    $isAdmin = ([Security.Principal.WindowsPrincipal] `
        [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "  ! Please run this in an elevated PowerShell (Run as Administrator)." -ForegroundColor Yellow
        return
    }

    $osv = [System.Environment]::OSVersion.Version
    Write-Host ("  - Windows version: {0}" -f $osv)
    if ($osv.Major -lt 10) {
        Write-Host "  ! Requires Windows 10/11." -ForegroundColor Yellow
        return
    }

    if (-not $SkipWSLSetup) {
        try {
            Write-Host "  - Enabling Windows Subsystem for Linux (WSL) & Virtual Machine Platform..."
            Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart -All | Out-Null
            Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart -All | Out-Null
            wsl --set-default-version 2 | Out-Null
            Write-Host "  - Updating WSL kernel (if supported)..."
            try { wsl --update | Out-Null } catch { }
        } catch {
            Write-Host "  ! WSL setup encountered an issue: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  - Skipping WSL setup as requested."
    }

    $already = $false
    try {
        $ver = (Get-Command "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue)
        if ($ver) { $already = $true }
    } catch { }

    if (-not $already) {
        $wingetOk = $false
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            $wingetOk = $true
            Write-Host "  - Installing Docker Desktop via winget..."
            $args = @("install", "--id", $WingetId, "-e", "--silent")
            if ($DesiredVersion) { $args += @("--version", $DesiredVersion) }
            try {
                winget @args
            } catch {
                Write-Host "  ! winget install failed: $($_.Exception.Message)" -ForegroundColor Yellow
                $wingetOk = $false
            }
        }

        if (-not $wingetOk) {
            if (Get-Command choco -ErrorAction SilentlyContinue) {
                Write-Host "  - Installing Docker Desktop via Chocolatey..."
                try {
                    if ($DesiredVersion) {
                        choco install docker-desktop --version $DesiredVersion -y --no-progress
                    } else {
                        choco install docker-desktop -y --no-progress
                    }
                } catch {
                    Write-Host "  ! choco install failed: $($_.Exception.Message)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ! Neither winget nor choco available. Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
                return
            }
        }
    } else {
        Write-Host "  - Docker Desktop is already installed."
    }

    if (-not $SkipSettings) {
        try {
            $settingsDir = Join-Path $env:APPDATA "Docker"
            $settingsFile = Join-Path $settingsDir "settings.json"
            if (-not (Test-Path $settingsDir)) { New-Item -ItemType Directory -Path $settingsDir | Out-Null }

            $desired = @{
                "useWindowsContainers" = $false
                "autoStart"            = $true
                "wslEngineEnabled"     = $true
                "kubernetesEnabled"    = $false
                "exposeDockerAPI"      = $false
            }

            if (Test-Path $settingsFile) {
                $current = Get-Content $settingsFile -Raw | ConvertFrom-Json
                foreach ($k in $desired.Keys) {
                    $current | Add-Member -NotePropertyName $k -NotePropertyValue $desired[$k] -Force
                }
                ($current | ConvertTo-Json -Depth 6) | Set-Content -Path $settingsFile -Encoding UTF8
            } else {
                ($desired | ConvertTo-Json -Depth 6) | Set-Content -Path $settingsFile -Encoding UTF8
            }
            Write-Host "  - Written Docker Desktop settings to $settingsFile"
        } catch {
            Write-Host "  ! Failed to write settings.json: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  - Skipping Docker Desktop settings as requested."
    }

    try {
        Write-Host "  - Adding current user to 'docker-users' local group..."
        $u = "$env:USERDOMAIN\$env:USERNAME"
        if (-not (Get-LocalGroup -Name "docker-users" -ErrorAction SilentlyContinue)) {
            New-LocalGroup -Name "docker-users" -ErrorAction SilentlyContinue | Out-Null
        }
        Add-LocalGroupMember -Group "docker-users" -Member $u -ErrorAction SilentlyContinue
    } catch {
        Write-Host "  ! Could not add user to docker-users: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    $dockerDesktopExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktopExe) {
        Write-Host "  - Launching Docker Desktop..."
        Start-Process -FilePath $dockerDesktopExe -ArgumentList "--accept-license" -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 6
    } else {
        Write-Host "  ! Docker Desktop executable not found at expected path." -ForegroundColor Yellow
    }

    if (-not $NoSmokeTest) {
        Write-Host "  - Running hello-world smoke test (may require new sign-in for docker-users group)..."
        try {
            docker run --rm hello-world | Out-Null
            Write-Host "Docker hello-world OK."
        } catch {
            Write-Host "hello-world test failed. If this is your first install, sign out/in (or reboot) and try again." -ForegroundColor Yellow
        }
    }

    Write-Host "`n[Install-Docker] Completed." -ForegroundColor Green
}


do {
    Clear-Host
    Write-Host "============================="
    Write-Host "      DOCKER MANAGEMENT MENU "
    Write-Host "============================="
    Write-Host "1. Stop all containers"
    Write-Host "2. Remove all containers"
    Write-Host "3. Remove all images"
    Write-Host "4. Remove all volumes"
    Write-Host "5. Remove unused networks"
    Write-Host "6. Prune builder cache"
    Write-Host "7. Reset all Docker (Full Reset)"
    Write-Host "8. Run ALL cleanup tasks"
    Write-Host "9. Uninstall Docker Desktop"
    Write-Host "10. Install Docker Desktop"
    Write-Host "0. Exit"
    Write-Host "============================="
    $choice = Read-Host "Enter your choice (0-10)"

    switch ($choice) {
        "1" { Stop-AllContainers; Read-Host "Press Enter to continue" }
        "2" { Remove-AllContainers; Read-Host "Press Enter to continue" }
        "3" { Remove-AllImages; Read-Host "Press Enter to continue" }
        "4" { Remove-AllVolumes; Read-Host "Press Enter to continue" }
        "5" { Remove-Networks; Read-Host "Press Enter to continue" }
        "6" { Prune-Builder; Read-Host "Press Enter to continue" }
        "7" { Reset-AllDocker; Read-Host "Press Enter to continue" }
        "8" { Run-All; Read-Host "Press Enter to continue" }
        "9" { Uninstall-Docker; Read-Host "Press Enter to continue" }
        "10" { Install-Docker; Read-Host "Press Enter to continue" }
        "0" { break }
        default { Write-Host "Invalid choice! Press Enter to try again."; Read-Host }
    }
} while ($true)

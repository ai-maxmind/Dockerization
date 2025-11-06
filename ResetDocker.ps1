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
    Write-Host "`nInstalling Docker Desktop..."
    
    $dockerApp = winget list | Where-Object { $_ -match "Docker.DockerDesktop" }
    if ($dockerApp) {
        Write-Host "Docker Desktop is already installed."
        return
    }

    Write-Host "Starting installation via winget..."
    winget install --id Docker.DockerDesktop -e --silent
    Write-Host "Docker Desktop installation triggered. Please wait for completion."

    Write-Host "`nAfter installation, you may need to log out and log in again or restart your system."
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

do {
    $result = git push
    if ($result -like "*error*") {
        Write-Host "Push failed, retrying..."
        Start-Sleep -Seconds 5  # 等待5秒再重试
    } else {
        Write-Host "Push succeeded!"
    }
} while ($result -like "*error*")

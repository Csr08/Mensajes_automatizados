$python = "C:\Users\Csr\AppData\Local\Programs\Python\Python312\python.exe"
$script = "C:\Users\Csr\Desktop\mensajesWPP\whatsapp_sender.py"

Write-Host "Enviando mensajes de WhatsApp..." -ForegroundColor Green
& $python $script

Write-Host "`nPresione Enter para salir..." -ForegroundColor Gray
Read-Host

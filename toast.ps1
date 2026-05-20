Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

$title = if ($args[0]) { $args[0] } else { 'Claude Code' }
$message = if ($args[1]) { $args[1] } else { 'Need Permission - Check Terminal' }

$xml = "<toast><visual><binding template='ToastText02'><text id='1'>$title</text><text id='2'>$message</text></binding></visual></toast>"
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('PowerShell')
$toast = [Windows.UI.Notifications.ToastNotification]::new($doc)
$notifier.Show($toast)
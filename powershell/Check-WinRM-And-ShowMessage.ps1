<#
.SYNOPSIS
  Check WinRM reachability on hosts, and optionally send a benign GUI message to consenting hosts.

  WARNING: Only use the remote message function on machines you own or where you have explicit permission.
#>

function Test-WinRMHosts {
  param(
    [Parameter(Mandatory=$true)]
    [string[]]$Hosts
  )

  foreach ($h in $Hosts) {
    try {
      Test-WSMan -ComputerName $h -ErrorAction Stop | Out-Null
      Write-Output "$h : WinRM reachable"
    } catch {
      Write-Output "$h : WinRM NOT reachable or blocked"
    }
  }
}

function Invoke-RemoteMessage {
  param(
    [Parameter(Mandatory=$true)]
    [string[]]$ComputerName,

    [Parameter(Mandatory=$true)]
    [pscredential]$Credential,

    [Parameter(Mandatory=$false)]
    [string]$Message = "Friendly test message — this host consents to a demo."
  )

  $scriptBlock = {
    param($text)
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($text, "Authorized Test")
  }

  Invoke-Command -ComputerName $ComputerName -Credential $Credential -ScriptBlock $scriptBlock -ArgumentList $Message -ErrorAction Stop
}

<#
Example usage:

# 1) Check WinRM reachability:
.\Check-WinRM-And-ShowMessage.ps1
Test-WinRMHosts -Hosts @("192.168.1.10","192.168.1.11")

# 2) Show a message on a consenting host (requires WinRM enabled and credentials):
$cred = Get-Credential
Invoke-RemoteMessage -ComputerName @("192.168.1.10") -Credential $cred -Message "This is an authorized test. Consent given."
#>

"""
HELIOS - System Controls
WiFi, Bluetooth, Airplane mode, Brightness, Dark mode, Power plans
"""

import subprocess
import webbrowser
import psutil


def _ps(cmd: str, timeout: int = 15) -> tuple:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _get_wifi_adapter() -> str:
    """Return the actual Wi-Fi adapter name from the system."""
    c, o, e = _ps(
        "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*Wi-Fi*' -or "
        "$_.InterfaceDescription -like '*Wireless*' -or $_.Name -like '*Wi-Fi*' -or "
        "$_.Name -like '*WiFi*' -or $_.Name -like '*Wireless*'} | "
        "Select-Object -First 1 -ExpandProperty Name")
    return o.strip() if o.strip() else "Wi-Fi"


class SystemControls:

    # ── WiFi ───────────────────────────────────────────────────────────────
    def wifi_on(self) -> str:
        adapter = _get_wifi_adapter()
        c, o, e = _ps(
            f"Enable-NetAdapter -Name '{adapter}' -Confirm:$false -ErrorAction SilentlyContinue; "
            f"Start-Sleep -Milliseconds 800; "
            f"$s = (Get-NetAdapter -Name '{adapter}').Status; Write-Output $s")
        status = o.strip().lower()
        if status and status != "disabled":
            return f"Wi-Fi ({adapter}) turned ON. Status: {o.strip()}"
        # Netsh fallback
        c2, o2, e2 = _ps(
            f"netsh interface set interface name='{adapter}' admin=enabled 2>&1; "
            f"Write-Output 'DONE'")
        if "DONE" in o2 and not e2:
            return f"Wi-Fi ({adapter}) turned ON."
        _ps(f"Start-Process powershell -ArgumentList "
            f"'Enable-NetAdapter -Name \"{adapter}\" -Confirm:$false' -Verb RunAs -Wait")
        return (f"Wi-Fi ON requested for adapter '{adapter}'.\n"
                f"If still off, run HELIOS as Administrator.")

    def wifi_off(self) -> str:
        adapter = _get_wifi_adapter()
        c, o, e = _ps(
            f"Disable-NetAdapter -Name '{adapter}' -Confirm:$false -ErrorAction SilentlyContinue; "
            f"Start-Sleep -Milliseconds 800; "
            f"$s = (Get-NetAdapter -Name '{adapter}').Status; Write-Output $s")
        if o.strip().lower() == "disabled":
            return f"Wi-Fi ({adapter}) turned OFF."
        # Netsh fallback
        c2, o2, e2 = _ps(
            f"netsh interface set interface name='{adapter}' admin=disabled 2>&1; "
            f"Write-Output 'DONE'")
        if "DONE" in o2 and not e2:
            return f"Wi-Fi ({adapter}) turned OFF."
        _ps(f"Start-Process powershell -ArgumentList "
            f"'Disable-NetAdapter -Name \"{adapter}\" -Confirm:$false' -Verb RunAs -Wait")
        return (f"Wi-Fi OFF requested for adapter '{adapter}'.\n"
                f"If still on, run HELIOS as Administrator.")

    def wifi_status(self) -> str:
        c, o, e = _ps("netsh wlan show interfaces")
        if "connected" in o.lower():
            for line in o.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    return f"Wi-Fi connected to: {line.split(':')[1].strip()}"
            return "Wi-Fi is connected."
        adapter = _get_wifi_adapter()
        c2, o2, _ = _ps(f"(Get-NetAdapter -Name '{adapter}' -ErrorAction SilentlyContinue).Status")
        return f"Wi-Fi status: {o2.strip() or 'disconnected/off'}"

    # ── Bluetooth ─────────────────────────────────────────────────────────
    def bluetooth_on(self) -> str:
        script = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bluetooth = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bluetooth) {
    Await ($bluetooth[0].SetStateAsync('On')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
    Write-Output "BT_OK"
} else {
    Write-Output "BT_NOT_FOUND"
}
"""
        c, o, e = _ps(script, timeout=20)
        if "BT_OK" in o:
            return "Bluetooth turned ON successfully."
        # Fallback: PnP device manager
        c2, o2, e2 = _ps(
            r"Get-PnpDevice | Where-Object {$_.Class -eq 'Bluetooth'} | "
            r"Enable-PnpDevice -Confirm:$false -ErrorAction SilentlyContinue; Write-Output 'DONE'")
        if "DONE" in o2:
            return "Bluetooth enabled via device manager."
        webbrowser.open("ms-settings:bluetooth")
        return ("Bluetooth settings opened.\nPlease toggle Bluetooth ON there.\n"
                "(Radio API unavailable — may need admin rights)")

    def bluetooth_off(self) -> str:
        script = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bluetooth = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bluetooth) {
    Await ($bluetooth[0].SetStateAsync('Off')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
    Write-Output "BT_OK"
} else {
    Write-Output "BT_NOT_FOUND"
}
"""
        c, o, e = _ps(script, timeout=20)
        if "BT_OK" in o:
            return "Bluetooth turned OFF successfully."
        webbrowser.open("ms-settings:bluetooth")
        return ("Bluetooth settings opened.\nPlease toggle Bluetooth OFF there.\n"
                "(Radio API unavailable — may need admin rights)")

    def bluetooth_status(self) -> str:
        c, o, e = _ps(
            "Get-PnpDevice | Where-Object {$_.Class -eq 'Bluetooth'} | "
            "Select-Object FriendlyName,Status | Format-Table | Out-String")
        return f"Bluetooth devices:\n{o}" if o else "No Bluetooth devices found."

    # ── Airplane Mode ─────────────────────────────────────────────────────
    def airplane_mode_on(self) -> str:
        results = []
        errors = []

        wifi_adapter = _get_wifi_adapter()
        c, o, e = _ps(
            f"Disable-NetAdapter -Name '{wifi_adapter}' -Confirm:$false "
            f"-ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500; "
            f"$s=(Get-NetAdapter -Name '{wifi_adapter}').Status; Write-Output $s")
        if o.strip().lower() == "disabled":
            results.append(f"Wi-Fi ({wifi_adapter}) disabled ✓")
        else:
            c2, o2, _ = _ps(
                f"netsh interface set interface name='{wifi_adapter}' admin=disabled 2>&1; "
                f"Write-Output 'DONE'")
            if "DONE" in o2 and not _:
                results.append(f"Wi-Fi ({wifi_adapter}) disabled ✓")
            else:
                errors.append(f"Wi-Fi needs admin rights")

        bt_script = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bt = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bt) { Await ($bt[0].SetStateAsync('Off')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null; Write-Output "BT_OK" }
else { Write-Output "BT_SKIP" }
"""
        c, o, e = _ps(bt_script, timeout=15)
        if "BT_OK" in o:
            results.append("Bluetooth disabled ✓")

        if results:
            msg = "Airplane Mode ON:\n  " + "\n  ".join(results)
            if errors:
                msg += "\n  ⚠ " + ", ".join(errors)
            return msg

        webbrowser.open("ms-settings:network-airplanemode")
        return "Could not toggle automatically. Airplane Mode settings opened — please enable it there."

    def airplane_mode_off(self) -> str:
        results = []
        errors = []

        wifi_adapter = _get_wifi_adapter()
        c, o, e = _ps(
            f"Enable-NetAdapter -Name '{wifi_adapter}' -Confirm:$false "
            f"-ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500; "
            f"$s=(Get-NetAdapter -Name '{wifi_adapter}').Status; Write-Output $s")
        status = o.strip().lower()
        if status and status != "disabled":
            results.append(f"Wi-Fi ({wifi_adapter}) enabled ✓")
        else:
            c2, o2, _ = _ps(
                f"netsh interface set interface name='{wifi_adapter}' admin=enabled 2>&1; "
                f"Write-Output 'DONE'")
            if "DONE" in o2:
                results.append(f"Wi-Fi ({wifi_adapter}) enabled ✓")
            else:
                errors.append("Wi-Fi needs admin rights")

        bt_script = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bt = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }
if ($bt) { Await ($bt[0].SetStateAsync('On')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null; Write-Output "BT_OK" }
else { Write-Output "BT_SKIP" }
"""
        c, o, e = _ps(bt_script, timeout=15)
        if "BT_OK" in o:
            results.append("Bluetooth enabled ✓")

        if results:
            msg = "Airplane Mode OFF:\n  " + "\n  ".join(results)
            if errors:
                msg += "\n  ⚠ " + ", ".join(errors)
            return msg

        webbrowser.open("ms-settings:network-airplanemode")
        return "Could not toggle automatically. Airplane Mode settings opened — please disable it there."

    # ── Brightness ────────────────────────────────────────────────────────
    def set_brightness(self, level: int) -> str:
        level = max(0, min(100, level))
        c, o, e = _ps(
            f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
            f".WmiSetBrightness(1,{level})")
        return f"Brightness set to {level}%." if c == 0 else \
            f"Brightness set to {level}% (WMI). May only work on laptops."

    def brightness_up(self, amount: int = 10) -> str:
        c, o, e = _ps(
            "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness")
        try:
            current = int(o.strip())
        except Exception:
            current = 50
        return self.set_brightness(min(100, current + amount))

    def brightness_down(self, amount: int = 10) -> str:
        c, o, e = _ps(
            "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness")
        try:
            current = int(o.strip())
        except Exception:
            current = 50
        return self.set_brightness(max(0, current - amount))

    # ── Dark / Light Mode ─────────────────────────────────────────────────
    def dark_mode_on(self) -> str:
        c, o, e = _ps("""
$p = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
Set-ItemProperty -Path $p -Name 'AppsUseLightTheme' -Value 0 -Type DWord -Force
Set-ItemProperty -Path $p -Name 'SystemUsesLightTheme' -Value 0 -Type DWord -Force
Write-Output 'OK'
""")
        return "Dark mode enabled." if "OK" in o else f"Failed: {e}"

    def dark_mode_off(self) -> str:
        c, o, e = _ps("""
$p = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
Set-ItemProperty -Path $p -Name 'AppsUseLightTheme' -Value 1 -Type DWord -Force
Set-ItemProperty -Path $p -Name 'SystemUsesLightTheme' -Value 1 -Type DWord -Force
Write-Output 'OK'
""")
        return "Light mode enabled." if "OK" in o else f"Failed: {e}"

    # ── Power Plans ───────────────────────────────────────────────────────
    def power_performance(self) -> str:
        c, o, e = _ps("powercfg /setactive SCHEME_MIN; Write-Output 'OK'")
        return "Power plan: High Performance." if "OK" in o else f"Failed: {e}"

    def power_balanced(self) -> str:
        c, o, e = _ps("powercfg /setactive SCHEME_BALANCED; Write-Output 'OK'")
        return "Power plan: Balanced." if "OK" in o else f"Failed: {e}"

    def power_saver(self) -> str:
        c, o, e = _ps("powercfg /setactive SCHEME_MAX; Write-Output 'OK'")
        return "Power plan: Power Saver." if "OK" in o else f"Failed: {e}"

    # ── Settings & Network ────────────────────────────────────────────────
    def open_settings(self, page: str = "") -> str:
        pages = {
            "wifi": "ms-settings:network-wifi",
            "bluetooth": "ms-settings:bluetooth",
            "display": "ms-settings:display",
            "sound": "ms-settings:sound",
            "battery": "ms-settings:batterysaver",
            "updates": "ms-settings:windowsupdate",
            "airplane": "ms-settings:network-airplanemode",
            "storage": "ms-settings:storagesense",
        }
        webbrowser.open(pages.get(page.lower(), "ms-settings:"))
        return f"Opened {page or 'Windows'} Settings."

    def flush_dns(self) -> str:
        c, o, e = _ps("ipconfig /flushdns; Write-Output 'OK'")
        return "DNS cache flushed." if "OK" in o else f"Failed: {e}"

    def open_task_manager(self) -> str:
        subprocess.Popen(["taskmgr.exe"])
        return "Task Manager opened."

    def top_processes(self, n: int = 10) -> str:
        procs = []
        for p in psutil.process_iter(["name", "cpu_percent", "memory_info"]):
            try:
                procs.append((p.info["name"], p.info["cpu_percent"],
                               p.info["memory_info"].rss // (1024 * 1024)))
            except Exception:
                pass
        procs.sort(key=lambda x: x[1], reverse=True)
        lines = [f"Top {n} by CPU:"]
        for name, cpu, mem in procs[:n]:
            lines.append(f"  {name:<28} CPU:{cpu:5.1f}%  RAM:{mem}MB")
        return "\n".join(lines)

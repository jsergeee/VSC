#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
База данных CVE для событий безопасности Windows
"""

# База данных CVE для событий безопасности
CVE_DATABASE = {
    # Критические уязвимости, связанные с событиями безопасности
    4624: {
        "cves": [
            {
                "id": "CVE-2021-42287",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            },
            {
                "id": "CVE-2021-42291",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            }
        ]
    },
    4625: {
        "cves": [
            {
                "id": "CVE-2022-26931",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 10/11, Server 2019-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4672: {
        "cves": [
            {
                "id": "CVE-2022-21874",
                "description": "Windows Security Center API Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 10/11, Server 2019-2022",
                "remediation": "Установите обновление KB5009543 или более позднее"
            }
        ]
    },
    4688: {
        "cves": [
            {
                "id": "CVE-2022-30190",
                "description": "Microsoft Office MSHTML Remote Code Execution Vulnerability (Follina)",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5015010 или более позднее"
            }
        ]
    },
    4697: {
        "cves": [
            {
                "id": "CVE-2022-34715",
                "description": "Windows Network File System Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2012-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4698: {
        "cves": [
            {
                "id": "CVE-2022-26925",
                "description": "Windows LSA Spoofing Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4720: {
        "cves": [
            {
                "id": "CVE-2022-26919",
                "description": "Active Directory Privilege Escalation Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    4740: {
        "cves": [
            {
                "id": "CVE-2021-33781",
                "description": "Active Directory Security Feature Bypass Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5004945 или более позднее"
            }
        ]
    },
    4768: {
        "cves": [
            {
                "id": "CVE-2021-33782",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5004945 или более позднее"
            },
            {
                "id": "CVE-2022-33679",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4769: {
        "cves": [
            {
                "id": "CVE-2022-33647",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5016622 или более позднее"
            }
        ]
    },
    4771: {
        "cves": [
            {
                "id": "CVE-2021-42287",
                "description": "Active Directory Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5008602 или более позднее"
            }
        ]
    },
    4776: {
        "cves": [
            {
                "id": "CVE-2022-23258",
                "description": "Windows Print Spooler Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5011495 или более позднее"
            }
        ]
    },
    4782: {
        "cves": [
            {
                "id": "CVE-2022-24521",
                "description": "Windows Common Log File System Driver Elevation of Privilege Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5011486 или более позднее"
            }
        ]
    },
    4794: {
        "cves": [
            {
                "id": "CVE-2022-26931",
                "description": "Windows Kerberos Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Server 2008-2022",
                "remediation": "Установите обновление KB5013942 или более позднее"
            }
        ]
    },
    5038: {
        "cves": [
            {
                "id": "CVE-2022-21894",
                "description": "Secure Boot Security Feature Bypass Vulnerability",
                "severity": "Critical",
                "affected": "Windows 8-11, Server 2012-2022",
                "remediation": "Обновите прошивку UEFI и установите обновление KB5012170"
            }
        ]
    },
    5140: {
        "cves": [
            {
                "id": "CVE-2022-30136",
                "description": "Windows Network File System Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows Server 2012-2022",
                "remediation": "Установите обновление KB5015010 или более позднее"
            }
        ]
    },
    5827: {
        "cves": [
            {
                "id": "CVE-2020-1472",
                "description": "Netlogon Elevation of Privilege Vulnerability (Zerologon)",
                "severity": "Critical",
                "affected": "Windows Server 2008-2019",
                "remediation": "Установите обновление KB4565349 и включите режим защиты"
            }
        ]
    },
    5828: {
        "cves": [
            {
                "id": "CVE-2020-1472",
                "description": "Netlogon Elevation of Privilege Vulnerability (Zerologon)",
                "severity": "Critical",
                "affected": "Windows Server 2008-2019",
                "remediation": "Установите обновление KB4565349 и включите режим защиты"
            }
        ]
    },
    
    # PowerShell связанные CVE
    4103: {
        "cves": [
            {
                "id": "CVE-2022-41076",
                "description": "PowerShell Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5018410 или более позднее"
            }
        ]
    },
    4104: {
        "cves": [
            {
                "id": "CVE-2022-41076",
                "description": "PowerShell Remote Code Execution Vulnerability",
                "severity": "Critical",
                "affected": "Windows 7-11, Server 2008-2022",
                "remediation": "Установите обновление KB5018410 или более позднее"
            }
        ]
    },
    
    # Windows Defender
    1116: {
        "cves": [
            {
                "id": "CVE-2022-23278",
                "description": "Microsoft Defender Elevation of Privilege Vulnerability",
                "severity": "High",
                "affected": "Windows Defender на Windows 10/11, Server",
                "remediation": "Обновите определения и установите обновление KB5011486"
            }
        ]
    }
}

def get_cve_for_event(event_id, event_data=None):
    """Получить CVE связанные с событием с учетом контекста"""
    cves = []
    
    if event_id in CVE_DATABASE:
        for cve in CVE_DATABASE[event_id]["cves"]:
            cve_entry = cve.copy()
            
            # Дополнительный анализ на основе данных события
            if event_data:
                # Проверяем специфичные индикаторы для Zerologon
                if cve["id"] == "CVE-2020-1472" and event_id in [5827, 5828]:
                    cve_entry["confidence"] = "High"
                    cve_entry["context_indicators"] = ["Обнаружена попытка использования Zerologon"]
                
                # Проверяем для Follina
                if cve["id"] == "CVE-2022-30190" and event_id == 4688:
                    event_str = str(event_data).lower()
                    if "msdt.exe" in event_str or "computerdefault" in event_str:
                        cve_entry["confidence"] = "Critical"
                        cve_entry["context_indicators"] = ["Обнаружен запуск msdt.exe - индикатор Follina"]
                
                # Проверяем для PrintNightmare
                event_str = str(event_data).lower()
                if "spoolsv.exe" in event_str and "rpcaddprinterdriver" in event_str:
                    if "cves" not in cve_entry:
                        cve_entry["cves"] = []
                    cve_entry["cves"].append({
                        "id": "CVE-2021-34527",
                        "description": "Windows Print Spooler Remote Code Execution Vulnerability (PrintNightmare)",
                        "severity": "Critical"
                    })
            
            cves.append(cve_entry)
    
    return cves
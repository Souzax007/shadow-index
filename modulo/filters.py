from dataclasses import dataclass
from typing import Dict, List


CATEGORY_QUERIES: Dict[str, List[str]] = {
    # === OSINT CLÁSSICO ===
    "all": ["osint", "osint tool", "osint framework", "intelligence gathering"],
    "email": ["email osint", "email lookup", "email breach", "email enumeration", "email finder"],
    "username": ["username search", "username osint", "account checker", "handle lookup", "username enumeration"],
    "domain": ["domain recon", "subdomain enumeration", "dns osint", "domain mapping", "domain intelligence"],
    "social": ["social media osint", "instagram osint", "twitter osint", "social profile", "facebook osint"],
    "phone": ["phone number osint", "phone lookup", "phone reverse", "phone enumeration", "carrier lookup"],
    "ip": ["ip lookup", "ip geolocation", "ip intelligence", "whois lookup", "asn lookup"],
    "geolocation": ["geolocation", "location finder", "gps tracking", "lat long lookup"],
    
    # === RECONNAISSANCE & ENUMERAÇÃO ===
    "enumeration": ["enumeration tool", "port enumeration", "service enumeration", "user enumeration", "directory enumeration"],
    "dns": ["dns recon", "dns enumeration", "dns mapping", "dns resolver", "zone transfer"],
    "subdomain": ["subdomain enumeration", "subdomain discovery", "subdomain finder", "vhost discovery", "subdomain brute"],
    "nmap": ["nmap", "port scanning", "network mapping", "service detection", "os detection"],
    "fingerprinting": ["web fingerprinting", "server fingerprinting", "cms fingerprinting", "version detection"],
    
    # === WORDLISTS & FUZZING ===
    "wordlist": ["wordlist", "password list", "dictionary attack", "brute force list", "fuzzing wordlist"],
    "fuzzing": ["fuzzing tool", "fuzz testing", "mutation fuzzing", "payload generation", "input fuzzing"],
    "brute_force": ["brute force", "dictionary attack", "credential stuffing", "password cracking"],
    
    # === VULNERABILITIES & EXPLORAÇÃO ===
    "vulnerability": ["vulnerability scanner", "vulnerability assessment", "cve scanner", "vuln detection"],
    "sql_injection": ["sql injection", "sql injection tool", "database attack", "sql exploitation"],
    "xss": ["cross site scripting", "xss tool", "xss payload", "dom xss", "reflected xss"],
    "rce": ["remote code execution", "rce exploit", "command injection", "code execution"],
    "privilege_escalation": ["privilege escalation", "privilege escalation tool", "sudo bypass", "privilege escalation techniques"],
    "web_exploitation": ["web exploitation", "web attack", "web vulnerability", "web security tool"],
    
    # === PENTESTING FRAMEWORKS ===
    "metasploit": ["metasploit", "metasploit module", "msfvenom", "exploitation framework"],
    "pentest": ["penetration testing", "penetration test tool", "pentest framework", "security testing"],
    "burpsuite": ["burpsuite", "burp extension", "web proxy", "request interceptor"],
    "sqlmap": ["sqlmap", "sql injection automation", "sql injection scanner", "automated sql exploitation"],
    
    # === NETWORK & PROTOCOL ===
    "network": ["network tool", "network analysis", "packet analysis", "network reconnaissance"],
    "wireshark": ["wireshark", "packet capture", "network sniffer", "traffic analysis"],
    "proxy": ["proxy tool", "http proxy", "proxy server", "man in the middle"],
    "vpn": ["vpn tool", "vpn client", "vpn tunnel", "anonymization"],
    
    # === WEB SECURITY ===
    "web_scanner": ["web scanner", "web vulnerability scanner", "site scanner", "automated scanner"],
    "cms": ["cms detection", "wordpress scanner", "joomla scanner", "cms vulnerability"],
    "jwt": ["jwt vulnerability", "json web token", "jwt bypass", "token manipulation"],
    "csrf": ["csrf", "cross site request forgery", "csrf protection bypass"],
    
    # === EXPLOITATION & PAYLOADS ===
    "exploit": ["exploit", "exploit code", "exploit development", "proof of concept"],
    "payload": ["payload generator", "shell payload", "reverse shell", "web shell"],
    "reverse_shell": ["reverse shell", "bind shell", "shell generator", "interactive shell"],
    "webshell": ["web shell", "backdoor", "shell upload", "file upload exploitation"],
    
    # === CRYPTOGRAPHY & HASHING ===
    "crypto": ["cryptography", "encryption tool", "cipher", "cryptanalysis"],
    "hash": ["hash cracking", "hash function", "password hash", "hash identifier"],
    "steganography": ["steganography", "data hiding", "file hiding", "covert channel"],
    
    # === MALWARE & ANALYSIS ===
    "malware": ["malware analysis", "malware detection", "malware tool", "virus analysis"],
    "reverse_engineering": ["reverse engineering", "disassembler", "debugger", "binary analysis"],
    "sandbox": ["sandbox analysis", "malware sandbox", "dynamic analysis", "behavioral analysis"],
    
    # === SOCIAL ENGINEERING ===
    "phishing": ["phishing", "phishing tool", "phishing kit", "credential harvesting"],
    "social_engineering": ["social engineering", "se tool", "information gathering", "pretexting"],
    
    # === AUTHENTICATION & ACCESS ===
    "auth": ["authentication bypass", "auth vulnerability", "login bypass", "session hijacking"],
    "mfa": ["mfa bypass", "two factor authentication", "totp generator", "otp bypass"],
    "ldap": ["ldap injection", "ldap enumeration", "directory service", "active directory"],
    
    # === API & CLOUD ===
    "api": ["api reconnaissance", "api enumeration", "api documentation", "endpoint discovery", "api security"],
    "cloud": ["cloud security", "cloud penetration test", "aws penetration", "azure hacking"],
    "s3": ["s3 bucket enumeration", "s3 misconfiguration", "aws enumeration"],
    
    # === THREAT INTELLIGENCE ===
    "threat": ["threat intelligence", "ioc finder", "malware osint", "threat analysis"],
    "ioc": ["ioc indicator", "malware signature", "threat indicator"],
    
    # === DARK WEB & ANONYMIZATION ===
    "dark_web": ["dark web osint", "onion search", "dark web monitoring", "tor osint"],
    "tor": ["tor tool", "onion", "anonymous browsing", "tor network"],
    
    # === HARDENING & DEFENSE ===
    "hardening": ["hardening guide", "security hardening", "system hardening", "configuration security"],
    "firewall": ["firewall tool", "firewall bypass", "firewall evasion"],
    
    # === CODE & SOURCE ANALYSIS ===
    "code": ["code search", "github osint", "source code analysis", "leak detection", "secret scanning"],
    "sast": ["static analysis", "code vulnerability scanner", "source code review"],
    
    # === REPORTING & DOCUMENTATION ===
    "report": ["pentest report", "vulnerability report", "security assessment", "compliance report"],
    
    # === MISC & TOOLS ===
    "automation": ["automation framework", "security automation", "workflow automation"],
    "framework": ["framework", "security framework", "testing framework"],
    "tool": ["security tool", "hacking tool", "pentesting tool", "utility tool"],


     # === MOBILE SECURITY ===
    "android": [
        "android pentest", "android reverse engineering", "apk analysis",
        "android malware", "android debugging", "android exploitation"
    ],
    "ios": [
        "ios pentest", "iphone exploitation", "ios jailbreak",
        "ios reverse engineering", "swift analysis", "mobile security"
    ],
    "mobile": [
        "mobile application security", "mobile pentest",
        "mobile reverse engineering", "mobile exploitation"
    ],

    # === WIRELESS & RF ===
    "wifi": [
        "wifi pentest", "wireless attack", "wifi cracking",
        "wpa attack", "wireless reconnaissance"
    ],
    "bluetooth": [
        "bluetooth hacking", "bluetooth analysis",
        "bluetooth enumeration", "ble security"
    ],
    "rfid": [
        "rfid hacking", "nfc exploitation",
        "rfid cloning", "badge cloning"
    ],

    # === ACTIVE DIRECTORY ===
    "active_directory": [
        "active directory enumeration", "kerberos attack",
        "ad pentest", "bloodhound", "domain escalation"
    ],
    "kerberos": [
        "kerberos exploitation", "kerberoasting",
        "ticket attack", "golden ticket"
    ],

    # === CONTAINERS & DEVOPS ===
    "docker": [
        "docker security", "docker escape",
        "container exploitation", "docker enumeration"
    ],
    "kubernetes": [
        "kubernetes security", "k8s pentest",
        "cluster enumeration", "kubernetes exploitation"
    ],
    "devops": [
        "devsecops", "pipeline security",
        "ci cd security", "github actions security"
    ],

    # === FORENSICS ===
    "forensics": [
        "digital forensics", "memory analysis",
        "disk forensics", "incident response"
    ],
    "memory_forensics": [
        "volatility framework", "ram analysis",
        "memory dump analysis", "process investigation"
    ],
    "disk_analysis": [
        "filesystem analysis", "disk recovery",
        "partition analysis", "timeline analysis"
    ],

    # === LOGGING & SIEM ===
    "siem": [
        "siem platform", "security monitoring",
        "event correlation", "log analysis"
    ],
    "splunk": [
        "splunk security", "splunk query",
        "splunk detection", "splunk hunting"
    ],
    "elk": [
        "elk stack security", "elasticsearch security",
        "kibana analysis", "logstash monitoring"
    ],

    # === THREAT HUNTING ===
    "threat_hunting": [
        "threat hunting", "ioc hunting",
        "anomaly detection", "behavior analysis"
    ],
    "yara": [
        "yara rules", "malware signatures",
        "pattern matching", "yara detection"
    ],

    # === C2 & POST EXPLOITATION ===
    "c2": [
        "command and control", "c2 framework",
        "beacon framework", "agent communication"
    ],
    "post_exploitation": [
        "post exploitation", "lateral movement",
        "credential dumping", "persistence"
    ],

    # === EVASION ===
    "evasion": [
        "av bypass", "edr bypass",
        "sandbox evasion", "payload obfuscation"
    ],
    "obfuscation": [
        "code obfuscation", "payload encoding",
        "binary packing", "anti analysis"
    ],

    # === BUG BOUNTY ===
    "bug_bounty": [
        "bug bounty", "bug bounty automation",
        "recon workflow", "vulnerability hunting"
    ],
    "recon_automation": [
        "automated reconnaissance", "subdomain automation",
        "osint automation", "asset discovery"
    ],

    # === OS SPECIFIC ===
    "linux": [
        "linux privilege escalation", "linux hardening",
        "linux enumeration", "linux exploitation"
    ],
    "windows": [
        "windows privilege escalation", "powershell exploitation",
        "windows enumeration", "windows security"
    ],

    # === PROGRAMMING & SCRIPTING ===
    "python_security": [
        "python security tools", "python exploitation",
        "security scripting", "python malware"
    ],
    "powershell": [
        "powershell offensive", "powershell obfuscation",
        "powershell empire", "windows scripting"
    ],

    # === SCANNERS & AUTOMATION ===
    "scanner": [
        "security scanner", "network scanner",
        "asset scanner", "automated scanning"
    ],
    "automation_ai": [
        "ai security automation", "llm security",
        "ai pentest", "autonomous security"
    ],

    # === DATABASE SECURITY ===
    "database": [
        "database security", "database enumeration",
        "db exploitation", "database audit"
    ],
    "mongodb": [
        "mongodb exploitation", "mongodb enumeration",
        "nosql injection", "mongodb security"
    ],
    "redis": [
        "redis exploitation", "redis misconfiguration",
        "redis enumeration", "redis attack"
    ],

    # === ICS / SCADA ===
    "scada": [
        "scada security", "industrial control systems",
        "ics pentest", "plc exploitation"
    ],
    "iot": [
        "iot security", "firmware analysis",
        "embedded exploitation", "smart device hacking"
    ],

    # === BROWSER SECURITY ===
    "browser": [
        "browser exploitation", "browser fingerprinting",
        "extension analysis", "web browser security"
    ],
    "extension": [
        "chrome extension analysis", "firefox addon security",
        "browser plugin exploitation"
    ],

    # === AI / ML SECURITY ===
    "ai_security": [
        "ai model security", "llm jailbreak",
        "prompt injection", "machine learning attacks"
    ],
    "prompt_injection": [
        "prompt injection", "llm exploitation",
        "ai prompt attack", "model manipulation"
    ],

    # === BLOCKCHAIN ===
    "blockchain": [
        "blockchain security", "crypto wallet analysis",
        "smart contract security", "web3 security"
    ],
    "smart_contract": [
        "smart contract audit", "solidity security",
        "ethereum exploitation", "contract vulnerability"
    ],

    # === LEAKS & BREACHES ===
    "breach": [
        "data breach", "credential leak",
        "breach monitoring", "leaked database"
    ],
    "credential": [
        "credential stuffing", "credential dump",
        "password spraying", "credential analysis"
    ],

    # === SEARCH ENGINES & DORKING ===
    "google_dork": [
        "google dork", "search engine reconnaissance",
        "advanced search operators", "dorking"
    ],
    "search_engine": [
        "search engine osint", "internet indexing",
        "metadata search", "file indexing"
    ],
}


@dataclass
class SearchConfig:
    source: str
    storage_backend: str
    category: str
    topic: str
    queries: List[str]
    max_pages: int
    page_choices: List[int]
    max_requests_per_minute: int
    min_delay: float
    max_delay: float


def build_queries(category: str, topic: str) -> List[str]:
    """Monta a lista final de queries da categoria + topico livre."""
    base = CATEGORY_QUERIES.get(category, CATEGORY_QUERIES["all"]).copy()
    extra = topic.strip()
    if extra:
        base.append(extra)
    # Remove duplicadas preservando ordem
    return list(dict.fromkeys(base))

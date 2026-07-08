ROLE_PLAYBOOKS = {
    "data_engineering": {
        "name": "Data Engineering",
        "summary_focus": ["pipelines", "cloud platforms", "SQL/Python", "data quality", "analytics delivery"],
        "verbs": ["Built", "Automated", "Optimized", "Orchestrated", "Validated", "Ingested", "Transformed", "Deployed"],
        "keywords": ["ETL", "ELT", "SQL", "Python", "Spark", "Airflow", "Databricks", "Data Lake", "Data Warehouse", "Data Quality"],
        "bullet_formula": "Built/optimized pipeline + tools + data source/target + quality/performance impact.",
        "metrics": ["pipeline runtime", "data volume", "SLA", "reconciliation accuracy", "reporting latency"],
    },
    "software_engineering": {
        "name": "Software Engineering",
        "summary_focus": ["application development", "APIs", "backend/frontend", "testing", "deployment"],
        "verbs": ["Developed", "Implemented", "Refactored", "Integrated", "Deployed", "Tested", "Maintained", "Enhanced"],
        "keywords": ["Java", "Python", "JavaScript", "React", "APIs", "microservices", "CI/CD", "cloud", "testing"],
        "bullet_formula": "Developed feature/service + stack + business/user impact + reliability/performance result.",
        "metrics": ["users", "response time", "deployment frequency", "defects", "coverage"],
    },
    "network_infrastructure": {
        "name": "Network / Infrastructure",
        "summary_focus": ["LAN/WAN", "Cisco", "monitoring", "incident resolution", "security", "infrastructure upgrades"],
        "verbs": ["Configured", "Troubleshot", "Monitored", "Secured", "Implemented", "Modernized", "Resolved", "Maintained"],
        "keywords": ["Cisco", "LAN", "WAN", "VLAN", "VPN", "firewalls", "routing", "switching", "monitoring", "incident response"],
        "bullet_formula": "Configured/resolved infrastructure + technology + operational outcome + availability/security result.",
        "metrics": ["sites", "devices", "incidents", "uptime", "latency", "downtime"],
    },
    "project_leadership": {
        "name": "Infrastructure / Technical Project Leadership",
        "summary_focus": ["project timelines", "stakeholders", "milestone reviews", "resource planning", "risk management", "delivery governance"],
        "verbs": ["Coordinated", "Facilitated", "Tracked", "Governed", "Delivered", "Reviewed", "Aligned", "Escalated", "Managed"],
        "keywords": ["project timelines", "milestones", "stakeholders", "resource discrepancies", "deliverables", "quality benchmarks", "scope", "risk", "project economics"],
        "bullet_formula": "Coordinated delivery activity + teams/stakeholders + timeline/risk/change action + delivery result.",
        "metrics": ["milestones", "projects", "teams", "stakeholders", "timeline", "budget", "risks"],
    },
    "business_analysis": {
        "name": "Business / Data Analysis",
        "summary_focus": ["requirements", "stakeholders", "reporting", "dashboards", "process improvement", "data insights"],
        "verbs": ["Analyzed", "Documented", "Translated", "Validated", "Facilitated", "Reported", "Improved", "Reviewed"],
        "keywords": ["requirements", "stakeholders", "UAT", "SQL", "dashboards", "reporting", "process improvement", "data analysis"],
        "bullet_formula": "Analyzed requirement/process/data + stakeholder need + output/report + decision or process result.",
        "metrics": ["reports", "KPIs", "stakeholders", "cycle time", "accuracy", "defects"],
    },
    "cybersecurity": {
        "name": "Cybersecurity",
        "summary_focus": ["security controls", "risk", "incident response", "vulnerability remediation", "compliance"],
        "verbs": ["Secured", "Remediated", "Monitored", "Investigated", "Hardened", "Validated", "Assessed", "Implemented"],
        "keywords": ["security", "vulnerability", "incident response", "risk", "SIEM", "access control", "compliance", "hardening"],
        "bullet_formula": "Secured/remediated control or risk + tool/framework + severity/impact + compliance outcome.",
        "metrics": ["vulnerabilities", "incidents", "alerts", "controls", "risk reduction", "SLA"],
    },
    "general": {
        "name": "General Professional",
        "summary_focus": ["relevant experience", "tools", "stakeholders", "delivery", "results"],
        "verbs": ["Delivered", "Supported", "Improved", "Collaborated", "Managed", "Documented", "Resolved", "Implemented"],
        "keywords": ["communication", "operations", "support", "quality", "delivery", "stakeholders"],
        "bullet_formula": "Action + responsibility + tool/process + business result.",
        "metrics": ["volume", "time", "quality", "cost", "stakeholders"],
    },
}


def get_playbook(role_family: str) -> dict:
    return ROLE_PLAYBOOKS.get(role_family, ROLE_PLAYBOOKS["general"])

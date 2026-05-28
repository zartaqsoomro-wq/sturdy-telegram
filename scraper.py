import time
from typing import List, Dict, Any

def fetch_clinical_trials() -> List[Dict[str, Any]]:
    """
    Simulates fetching real-world clinical trial data from an external API or scraper.
    """
    # Simulate network delay
    time.sleep(1)
    
    # Mock response from a clinical trials API
    return [
        {
            "trial_id": "NCT04561234",
            "company": "Novartis",
            "phase": "Phase 3",
            "summary": "Efficacy and Safety of Kisqali in HR+/HER2- Advanced Breast Cancer.",
            "confidence_score": 0.95
        },
        {
            "trial_id": "NCT05678901",
            "company": "Pfizer",
            "phase": "Phase 2",
            "summary": "Study of Elranatamab in Patients With Multiple Myeloma.",
            "confidence_score": 0.88
        },
        {
            "trial_id": "NCT03456789",
            "company": "AstraZeneca",
            "phase": "Phase 3",
            "summary": "Osimertinib in First-line Treatment of EGFR-mutated Non-Small Cell Lung Cancer.",
            "confidence_score": 0.92
        },
        {
            "trial_id": "NCT06789012",
            "company": "Merck",
            "phase": "Phase 1/2",
            "summary": "Pembrolizumab Plus Chemotherapy for Advanced TNBC.",
            "confidence_score": 0.85
        },
        {
            "trial_id": "NCT07890123",
            "company": "Gilead",
            "phase": "Phase 2",
            "summary": "Trodelvy for Previously Treated Metastatic Urothelial Cancer.",
            "confidence_score": 0.89
        }
    ]

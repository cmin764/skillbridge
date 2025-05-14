"""
AI utilities for the skillmatch app.
"""


async def parse_cv_file(file_obj) -> dict:
    """
    Parses a CV file to extract candidate information.
    In a real implementation, this would call an LLM or NLP pipeline.
    """
    # Print debugging info
    print(f"Parsing CV - using mock data only")

    # Mock response - in production this would use AI
    return {
        'name': 'Jane Doe',
        'skills': ['Python', 'Django', 'AI'],
        'experience_years': 5
    }


async def rank_candidate(candidate_data, job_data) -> dict:
    """
    Ranks a candidate against a job posting.
    In a real implementation, this would prompt an LLM for scoring.
    """
    # Calculate overlap between candidate skills and job requirements
    candidate_skills = set(candidate_data.get('skills', []))
    job_requirements = set(job_data.get('requirements', []))

    matching_skills = candidate_skills.intersection(job_requirements)
    score = len(matching_skills) / len(job_requirements) if job_requirements else 0

    # Mock response - in production this would use AI
    return {
        'score': min(score * 100, 100),  # Scale to 0-100
        'rationale': f'Candidate has {len(matching_skills)} of {len(job_requirements)} required skills'
    }

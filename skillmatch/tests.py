"""
Tests for the SkillMatch application.
"""

from unittest import mock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import CVUpload, Candidate, Job, Match
from .services import parse_cv_file, rank_candidate


class SkillMatchIntegrationTestCase(TestCase):
    """Integration test for the full skillmatch flow."""

    def setUp(self):
        """Set up the test environment."""
        self.client = APIClient()

        # Mock the AI parsing and ranking services
        # Ensure correct import path for mocking
        self.parse_cv_patcher = mock.patch('skillmatch.services.parse_cv_file')
        self.mock_parse_cv = self.parse_cv_patcher.start()
        self.mock_parse_cv.return_value = {
            'name': 'Test Candidate',
            'skills': ['Python', 'Django', 'PostgreSQL'],
            'experience_years': 3
        }

        self.rank_candidate_patcher = mock.patch('skillmatch.services.rank_candidate')
        self.mock_rank_candidate = self.rank_candidate_patcher.start()
        self.mock_rank_candidate.return_value = {
            'score': 85.0,
            'rationale': 'Strong match on 2 of 3 required skills'
        }

    def tearDown(self):
        """Clean up after tests."""
        self.parse_cv_patcher.stop()
        self.rank_candidate_patcher.stop()

    def test_cv_upload_and_parsing(self):
        """Test uploading a CV and parsing it into a candidate."""
        # Create a test CV file
        cv_content = b"This is a test CV file content"
        cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            cv_content,
            content_type="application/pdf"
        )

        # 1. Upload the CV
        upload_response = self.client.post(
            reverse('cvupload-list'),
            {'file': cv_file},
            format='multipart'
        )
        self.assertEqual(upload_response.status_code, 201, upload_response.data)

        # Get the uploaded CV ID
        cv_id = upload_response.data['id']
        self.assertIsNotNone(cv_id)

        # 2. Parse the CV to create a candidate
        parse_url = reverse('cvupload-parse', kwargs={'pk': cv_id})
        parse_response = self.client.post(parse_url)
        self.assertEqual(parse_response.status_code, 201, parse_response.data)

        # Verify candidate was created
        candidate_id = parse_response.data['id']
        self.assertIsNotNone(candidate_id)
        self.assertEqual(parse_response.data['name'], 'Test Candidate')
        self.assertEqual(parse_response.data['skills'], ['Python', 'Django', 'PostgreSQL'])
        self.assertEqual(parse_response.data['experience_years'], 3)

        # 3. Get the candidate from the API
        candidate_url = reverse('candidate-detail', kwargs={'pk': candidate_id})
        candidate_response = self.client.get(candidate_url)
        self.assertEqual(candidate_response.status_code, 200, candidate_response.data)
        self.assertEqual(candidate_response.data['name'], 'Test Candidate')

        return candidate_id  # Return for use in the next test

    def test_job_creation(self):
        """Test creating a job posting."""
        # Create a job
        job_data = {
            'title': 'Django Developer',
            'requirements': ['Python', 'Django', 'PostgreSQL']
        }

        job_response = self.client.post(
            reverse('job-list'),
            job_data,
            format='json'
        )
        self.assertEqual(job_response.status_code, 201, job_response.data)

        # Verify job was created
        job_id = job_response.data['id']
        self.assertIsNotNone(job_id)
        self.assertEqual(job_response.data['title'], 'Django Developer')
        self.assertEqual(job_response.data['requirements'], ['Python', 'Django', 'PostgreSQL'])

        return job_id  # Return for use in the next test

    def test_candidate_job_matching(self):
        """Test matching a candidate with a job."""
        # First create a candidate and a job
        candidate_id = self.test_cv_upload_and_parsing()
        job_id = self.test_job_creation()

        # Match the candidate with the job
        match_data = {
            'candidate_id': candidate_id,
            'job_id': job_id
        }

        match_response = self.client.post(
            reverse('match-create-match'),
            match_data,
            format='json'
        )
        self.assertEqual(match_response.status_code, 201, match_response.data)

        # Verify match was created
        match_id = match_response.data['id']
        self.assertIsNotNone(match_id)
        self.assertEqual(match_response.data['score'], 85.0)
        self.assertEqual(match_response.data['candidate']['id'], candidate_id)
        self.assertEqual(match_response.data['job']['id'], job_id)

        # Test getting the match details
        match_url = reverse('match-detail', kwargs={'pk': match_id})
        match_detail_response = self.client.get(match_url)
        self.assertEqual(match_detail_response.status_code, 200, match_detail_response.data)
        self.assertEqual(match_detail_response.data['score'], 85.0)

    def test_full_matching_flow(self):
        """Test the complete flow from CV upload to matching."""
        # 1. Upload and parse CV
        cv_content = b"This is a test CV file content"
        cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            cv_content,
            content_type="application/pdf"
        )

        upload_response = self.client.post(
            reverse('cvupload-list'),
            {'file': cv_file},
            format='multipart'
        )
        self.assertEqual(upload_response.status_code, 201, upload_response.data)
        cv_id = upload_response.data['id']

        parse_url = reverse('cvupload-parse', kwargs={'pk': cv_id})
        parse_response = self.client.post(parse_url)
        self.assertEqual(parse_response.status_code, 201, parse_response.data)
        candidate_id = parse_response.data['id']

        # 2. Create a job
        job_data = {
            'title': 'Senior Developer',
            'requirements': ['Python', 'Django', 'Leadership']
        }

        job_response = self.client.post(
            reverse('job-list'),
            job_data,
            format='json'
        )
        self.assertEqual(job_response.status_code, 201, job_response.data)
        job_id = job_response.data['id']

        # 3. Match the candidate with the job
        match_data = {
            'candidate_id': candidate_id,
            'job_id': job_id
        }

        match_response = self.client.post(
            reverse('match-create-match'),
            match_data,
            format='json'
        )
        self.assertEqual(match_response.status_code, 201, match_response.data)

        # 4. Verify everything worked together
        candidates_response = self.client.get(reverse('candidate-list'))
        self.assertEqual(candidates_response.status_code, 200, candidates_response.data)
        self.assertGreaterEqual(len(candidates_response.data['results']), 1)

        jobs_response = self.client.get(reverse('job-list'))
        self.assertEqual(jobs_response.status_code, 200, jobs_response.data)
        self.assertGreaterEqual(len(jobs_response.data['results']), 1)

        matches_response = self.client.get(reverse('match-list'))
        self.assertEqual(matches_response.status_code, 200, matches_response.data)
        self.assertGreaterEqual(len(matches_response.data['results']), 1)

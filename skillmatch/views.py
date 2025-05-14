from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import sync_to_async
import asyncio
import functools

from .models import CVUpload, Candidate, Job, Match
from .serializers import (
    CVUploadSerializer, CandidateSerializer,
    JobSerializer, MatchSerializer, MatchListSerializer
)


# Decorator to make async views compatible with DRF
def async_to_sync_view(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapped


# Stub functions for AI parsing and ranking:
async def parse_cv_file(file_obj) -> dict:
    """
    Parses a CV file to extract candidate information.
    In a real implementation, this would call an LLM or NLP pipeline.
    """
    # Print debugging info
    print(f"parse_cv_file called with file object: {file_obj}")
    print(f"File object type: {type(file_obj)}")

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
    # Imagine this prompts an LLM for a score & rationale
    candidate_skills = set(candidate_data.get('skills', []))
    job_requirements = set(job_data.get('requirements', []))

    # Calculate overlap between candidate skills and job requirements
    matching_skills = candidate_skills.intersection(job_requirements)
    score = len(matching_skills) / len(job_requirements) if job_requirements else 0

    # Mock response - in production this would use AI
    return {
        'score': min(score * 100, 100),  # Scale to 0-100
        'rationale': f'Candidate has {len(matching_skills)} of {len(job_requirements)} required skills'
    }


class CVUploadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for CV uploads.
    """
    queryset = CVUpload.objects.all().order_by('-uploaded_at')
    serializer_class = CVUploadSerializer
    parser_classes = [MultiPartParser]  # handles multipart file uploads

    @action(detail=True, methods=['post'])
    @async_to_sync_view
    async def parse(self, request, pk=None):
        """
        Parses the uploaded CV into a Candidate.
        If a Candidate already exists for this CV, it updates the existing record.
        """
        print(f"Parse method called with pk={pk}")

        try:
            # Get the CV upload object
            upload = await sync_to_async(self.get_object)()
            print(f"Found upload object: {upload.id}")

            # Get the mock data
            data = await parse_cv_file(upload.file)
            print(f"Parsed data: {data}")

            # Check if a Candidate already exists for this CV
            candidate_exists = await sync_to_async(
                lambda: Candidate.objects.filter(source_cv=upload).exists()
            )()

            print(f"Candidate exists: {candidate_exists}")

            if candidate_exists:
                # Update existing candidate
                candidate = await sync_to_async(
                    lambda: Candidate.objects.get(source_cv=upload)
                )()

                # Update fields
                candidate.name = data['name']
                candidate.skills = data['skills']
                candidate.experience_years = data['experience_years']

                # Save the updated candidate
                await sync_to_async(candidate.save)()
                print(f"Updated candidate: {candidate.id}")

                # Create response serializer and get the data directly
                response_serializer = CandidateSerializer(candidate)

                # Use safe serialization
                return Response(
                    safe_serialize(response_serializer),
                    status=status.HTTP_200_OK
                )
            else:
                # Create new candidate
                print("Creating new candidate")
                data['cv_id'] = upload.id

                serializer = CandidateSerializer(data=data)
                is_valid = await sync_to_async(serializer.is_valid)(raise_exception=True)
                print(f"Serializer valid: {is_valid}")

                candidate = await sync_to_async(serializer.save)()
                print(f"Created candidate: {candidate.id}")

                # Create response serializer and use safe serialization
                response_serializer = CandidateSerializer(candidate)

                return Response(
                    safe_serialize(response_serializer),
                    status=status.HTTP_201_CREATED
                )
        except Exception as e:
            # Log the detailed error
            print(f"Error in parse method: {e}")
            import traceback
            traceback.print_exc()

            # Return error response
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for candidates (read-only).
    """
    queryset = Candidate.objects.all().order_by('-parsed_at')
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'skills']

    def _fix_status_field(self, data):
        """Fix the status field in the serialized data."""
        if isinstance(data, dict) and 'status' in data:
            # Check if status is a CharField representation
            if isinstance(data['status'], str) and data['status'].startswith('<django.db.models'):
                # Replace with actual status value
                candidates = {c.id: c.status for c in Candidate.objects.all()}
                if data.get('id') in candidates:
                    data['status'] = candidates[data['id']]
        return data

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to use safe serialization."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        # Apply direct fix for status field
        serialized_data = safe_serialize(serializer)
        fixed_data = self._fix_status_field(serialized_data)

        return Response(fixed_data)

    def list(self, request, *args, **kwargs):
        """Override list to use safe serialization."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = safe_serialize(serializer)

            # Fix status fields in each item if it's a list of dicts
            if isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
                data['results'] = [self._fix_status_field(item) for item in data['results']]

            return self.get_paginated_response(data)

        serializer = self.get_serializer(queryset, many=True)
        data = safe_serialize(serializer)

        # Fix status fields in each item if it's a list
        if isinstance(data, list):
            data = [self._fix_status_field(item) for item in data]

        return Response(data)


class JobViewSet(viewsets.ModelViewSet):
    """
    API endpoint for job postings.
    """
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'requirements']

    def create(self, request, *args, **kwargs):
        """Override create to ensure proper serialization."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        # Re-serialize with our custom serializer
        response_serializer = self.get_serializer(job)
        return Response(
            safe_serialize(response_serializer),
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Override update to ensure proper serialization."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        # Re-serialize with our custom serializer
        response_serializer = self.get_serializer(job)
        return Response(
            safe_serialize(response_serializer)
        )

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to use safe serialization."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(safe_serialize(serializer))

    def list(self, request, *args, **kwargs):
        """Override list to use safe serialization."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(safe_serialize(serializer))

        serializer = self.get_serializer(queryset, many=True)
        return Response(safe_serialize(serializer))


class MatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for candidate-job matches.
    """
    queryset = Match.objects.all().order_by('-score')

    def get_serializer_class(self):
        if self.action == 'list':
            return MatchListSerializer
        return MatchSerializer

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to use safe serialization."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(safe_serialize(serializer))

    def list(self, request, *args, **kwargs):
        """Override list to use safe serialization."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(safe_serialize(serializer))

        serializer = self.get_serializer(queryset, many=True)
        return Response(safe_serialize(serializer))

    @action(detail=False, methods=['post'])
    @async_to_sync_view
    async def create_match(self, request):
        """
        Given candidate_id and job_id, computes and stores a Match.
        If a match already exists, it updates it instead of creating a duplicate.
        """
        # Get objects using sync_to_async
        get_candidate = sync_to_async(get_object_or_404)
        get_job = sync_to_async(get_object_or_404)

        cand = await get_candidate(Candidate, pk=request.data.get('candidate_id'))
        job = await get_job(Job, pk=request.data.get('job_id'))

        # Check if a match already exists
        match_exists = await sync_to_async(
            lambda: Match.objects.filter(candidate=cand, job=job).exists()
        )()

        if match_exists:
            # Get the existing match
            match = await sync_to_async(
                lambda: Match.objects.get(candidate=cand, job=job)
            )()

            # Recalculate score (optionally)
            if request.data.get('recalculate', True):
                # Get serialized data
                cand_serializer = CandidateSerializer(cand)
                job_serializer = JobSerializer(job)
                candidate_data = await sync_to_async(lambda: cand_serializer.data)()
                job_data = await sync_to_async(lambda: job_serializer.data)()

                # Calculate match score and rationale
                result = await rank_candidate(candidate_data, job_data)

                # Update the match
                match.score = result['score']
                match.rationale = result['rationale']
                await sync_to_async(match.save)()

            # Return the existing match
            match_serializer = MatchSerializer(match)
            return Response(
                {
                    **safe_serialize(match_serializer),
                    "message": "Match already existed and was updated"
                },
                status=status.HTTP_200_OK
            )

        # Get serialized data
        cand_serializer = CandidateSerializer(cand)
        job_serializer = JobSerializer(job)
        candidate_data = await sync_to_async(lambda: cand_serializer.data)()
        job_data = await sync_to_async(lambda: job_serializer.data)()

        # Calculate match score and rationale
        result = await rank_candidate(candidate_data, job_data)

        # Create and save the match
        match = Match(
            candidate=cand,
            job=job,
            score=result['score'],
            rationale=result['rationale']
        )
        await sync_to_async(match.save)()

        # Return the serialized match
        match_serializer = MatchSerializer(match)
        return Response(
            safe_serialize(match_serializer),
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'])
    @async_to_sync_view
    async def match_candidates(self, request):
        """
        Match all active candidates to all active jobs.
        Updates existing matches with new scores.
        """
        # Get active candidates and jobs
        get_candidates = sync_to_async(lambda: list(Candidate.objects.filter(status='active')))
        get_jobs = sync_to_async(lambda: list(Job.objects.filter(status='active')))

        candidates = await get_candidates()
        jobs = await get_jobs()

        # Track created and updated matches
        created_matches = []
        updated_matches = []

        # Create matches for each candidate-job pair
        for candidate in candidates:
            for job in jobs:
                # Check if match already exists
                match_exists = await sync_to_async(
                    lambda: Match.objects.filter(candidate=candidate, job=job).exists()
                )()

                if match_exists:
                    # Update existing match
                    match = await sync_to_async(
                        lambda: Match.objects.get(candidate=candidate, job=job)
                    )()

                    # Get the data and calculate score
                    cand_serializer = CandidateSerializer(candidate)
                    job_serializer = JobSerializer(job)
                    candidate_data = await sync_to_async(lambda: cand_serializer.data)()
                    job_data = await sync_to_async(lambda: job_serializer.data)()

                    # Recalculate score and rationale
                    result = await rank_candidate(candidate_data, job_data)

                    # Update match data
                    match.score = result['score']
                    match.rationale = result['rationale']
                    await sync_to_async(match.save)()
                    updated_matches.append(match)

                else:
                    # Create new match
                    # Serialize for the ranking function
                    cand_serializer = CandidateSerializer(candidate)
                    job_serializer = JobSerializer(job)
                    candidate_data = await sync_to_async(lambda: cand_serializer.data)()
                    job_data = await sync_to_async(lambda: job_serializer.data)()

                    # Calculate match score and rationale
                    result = await rank_candidate(candidate_data, job_data)

                    # Create and save the match
                    match = Match(
                        candidate=candidate,
                        job=job,
                        score=result['score'],
                        rationale=result['rationale']
                    )
                    await sync_to_async(match.save)()
                    created_matches.append(match)

        # Return summary information
        return Response(
            {
                "message": f"Created {len(created_matches)} new matches, updated {len(updated_matches)} existing matches",
                "matches_created": len(created_matches),
                "matches_updated": len(updated_matches)
            },
            status=status.HTTP_201_CREATED if created_matches else status.HTTP_200_OK
        )


# Add this helper function to convert serializer data safely
def safe_serialize(serializer):
    """Convert serializer data to a JSON-safe format."""
    try:
        # For debugging
        print(f"Serializing {type(serializer).__name__}")

        # Handle different input types
        if hasattr(serializer, 'data'):
            # It's a serializer instance
            data = serializer.data
        else:
            # It's already data
            data = serializer

        # For models with status fields, ensure they're properly handled
        if isinstance(data, dict) and 'status' in data:
            if str(data['status']).startswith('<django.db.models.fields'):
                # Get the actual status from source if possible
                if hasattr(serializer, 'instance') and hasattr(serializer.instance, 'status'):
                    data['status'] = serializer.instance.status

        # Force conversion to primitive types
        return _deep_convert(data)
    except Exception as e:
        # Log the error and return a fallback
        print(f"Serialization error: {e}")
        import traceback
        traceback.print_exc()

        if hasattr(serializer, 'instance'):
            # Try manual model conversion as last resort
            try:
                from django.forms.models import model_to_dict
                model_dict = model_to_dict(serializer.instance)
                return _deep_convert(model_dict)
            except Exception as model_err:
                print(f"Model conversion error: {model_err}")

        return {"error": "Could not serialize data", "detail": str(e)}

# Simpler helper to convert nested structures
def _deep_convert(data):
    """Deep convert any value to JSON-serializable types."""
    if data is None:
        return None
    elif isinstance(data, (str, int, float, bool)):
        return data
    elif isinstance(data, dict):
        return {k: _deep_convert(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [_deep_convert(item) for item in data]
    else:
        # For any other type (including Django fields), use string representation
        return str(data)

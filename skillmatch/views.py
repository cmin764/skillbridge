from rest_framework import viewsets, filters, status
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.response import Response
import asyncio

from .models import CVUpload, Candidate, Job, Match
from .serializers import (
    CVUploadSerializer, CandidateSerializer,
    JobSerializer, MatchSerializer, MatchListSerializer
)
from .core import (
    safe_serialize, async_to_sync_view,
    fetch_objects, check_exists,
    SafeSerializationMixin, fetch_object_or_none, run_in_transaction
)
from .services import parse_cv_file, rank_candidate


class CVUploadViewSet(SafeSerializationMixin, viewsets.ModelViewSet):
    """
    API endpoint for CV uploads.
    """
    queryset = CVUpload.objects.all().order_by('-uploaded_at')
    serializer_class = CVUploadSerializer
    parser_classes = [MultiPartParser]  # handles multipart file uploads

    @action(detail=True, methods=['post'], url_name='parse')
    @async_to_sync_view
    async def parse(self, request, pk=None):
        """
        Parses the uploaded CV into a Candidate.
        If a Candidate already exists for this CV, it updates the existing record.
        """
        print(f"Parse method called with pk={pk}")

        try:
            # Get the CV upload object using safer fetch_object_or_none
            upload = await fetch_object_or_none(CVUpload, pk=pk)

            if not upload:
                return Response(
                    {"error": f"CVUpload with id {pk} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            print(f"Found upload object: {upload.id}")

            # Get the mock data
            data = await parse_cv_file(upload.file)
            print(f"Parsed data: {data}")

            # Check if a Candidate already exists for this CV
            candidate_exists = await check_exists(Candidate, source_cv=upload)
            print(f"Candidate exists: {candidate_exists}")

            if candidate_exists:
                # Define a function to update the candidate within a transaction
                def update_candidate():
                    candidate = Candidate.objects.get(source_cv=upload)
                    candidate.name = data['name']
                    candidate.skills = data['skills']
                    candidate.experience_years = data['experience_years']
                    candidate.save()
                    return candidate

                # Run the update in a transaction
                candidate = await run_in_transaction(update_candidate)
                print(f"Updated candidate: {candidate.id}")

                # Create response serializer and use safe serialization
                response_serializer = CandidateSerializer(candidate)
                return Response(
                    safe_serialize(response_serializer),
                    status=status.HTTP_200_OK
                )
            else:
                # Define a function to create a new candidate within a transaction
                def create_candidate():
                    serializer = CandidateSerializer(data={'name': data['name'],
                                                         'skills': data['skills'],
                                                         'experience_years': data['experience_years'],
                                                         'cv_id': upload.id})
                    serializer.is_valid(raise_exception=True)
                    return serializer.save()

                # Create new candidate in a transaction
                print("Creating new candidate")
                candidate = await run_in_transaction(create_candidate)
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


class CandidateViewSet(SafeSerializationMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for candidates (read-only).
    """
    queryset = Candidate.objects.all().order_by('-parsed_at')
    serializer_class = CandidateSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'skills']


class JobViewSet(SafeSerializationMixin, viewsets.ModelViewSet):
    """
    API endpoint for job postings.
    """
    queryset = Job.objects.all().order_by('-created_at')
    serializer_class = JobSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'requirements']


class MatchViewSet(SafeSerializationMixin, viewsets.ModelViewSet):
    """
    API endpoint for candidate-job matches.
    """
    queryset = Match.objects.all().order_by('-score')

    def get_serializer_class(self):
        if self.action == 'list':
            return MatchListSerializer
        return MatchSerializer

    @action(detail=False, methods=['post'], url_name='create-match')
    @async_to_sync_view
    async def create_match(self, request):
        """
        Given candidate_id and job_id, computes and stores a Match.
        If a match already exists, it updates it instead of creating a duplicate.
        """
        try:
            # Get the candidate and job
            candidate_id = request.data.get('candidate_id')
            job_id = request.data.get('job_id')

            # Use fetch_object_or_none for safer queries
            candidate = await fetch_object_or_none(Candidate, pk=candidate_id)
            job = await fetch_object_or_none(Job, pk=job_id)

            if not candidate:
                return Response(
                    {"error": f"Candidate with id {candidate_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not job:
                return Response(
                    {"error": f"Job with id {job_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if a match already exists
            match_exists = await check_exists(Match, candidate=candidate, job=job)

            if match_exists:
                # Define function to update match in transaction
                def update_match():
                    match = Match.objects.get(candidate=candidate, job=job)

                    # Only recalculate if requested
                    if request.data.get('recalculate', True):
                        # Get serialized data for the ranking
                        candidate_data = safe_serialize(CandidateSerializer(candidate))
                        job_data = safe_serialize(JobSerializer(job))

                        # This is async so need to get result synchronously in this function
                        loop = asyncio.new_event_loop()
                        result = loop.run_until_complete(rank_candidate(candidate_data, job_data))
                        loop.close()

                        # Update the match
                        match.score = result['score']
                        match.rationale = result['rationale']

                    match.save()
                    return match

                # Run update in transaction
                match = await run_in_transaction(update_match)

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
            candidate_data = safe_serialize(CandidateSerializer(candidate))
            job_data = safe_serialize(JobSerializer(job))

            # Calculate match score and rationale
            result = await rank_candidate(candidate_data, job_data)

            # Define function to create match in transaction
            def create_match():
                match = Match(
                    candidate=candidate,
                    job=job,
                    score=result['score'],
                    rationale=result['rationale']
                )
                match.save()
                return match

            # Create and save the match in a transaction
            match = await run_in_transaction(create_match)

            # Return the serialized match
            match_serializer = MatchSerializer(match)
            return Response(
                safe_serialize(match_serializer),
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print(f"Error in create_match: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_name='match-candidates')
    @async_to_sync_view
    async def match_candidates(self, request):
        """
        Match all active candidates to all active jobs.
        Updates existing matches with new scores.
        """
        try:
            # Get active candidates and jobs
            candidates = await fetch_objects(Candidate, status='active')
            jobs = await fetch_objects(Job, status='active')

            # Track created and updated matches
            created_matches = []
            updated_matches = []

            # Process each candidate-job pair
            for candidate in candidates:
                for job in jobs:
                    # Get serialized data for ranking
                    candidate_data = safe_serialize(CandidateSerializer(candidate))
                    job_data = safe_serialize(JobSerializer(job))

                    # Calculate match score and rationale
                    result = await rank_candidate(candidate_data, job_data)

                    # Check if match already exists
                    match_exists = await check_exists(Match, candidate=candidate, job=job)

                    if match_exists:
                        # Define function to update match in transaction
                        def update_match():
                            match = Match.objects.get(candidate=candidate, job=job)
                            match.score = result['score']
                            match.rationale = result['rationale']
                            match.save()
                            return match

                        # Update existing match in transaction
                        match = await run_in_transaction(update_match)
                        updated_matches.append(match)
                    else:
                        # Define function to create match in transaction
                        def create_match():
                            match = Match(
                                candidate=candidate,
                                job=job,
                                score=result['score'],
                                rationale=result['rationale']
                            )
                            match.save()
                            return match

                        # Create new match in transaction
                        match = await run_in_transaction(create_match)
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
        except Exception as e:
            print(f"Error in match_candidates: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import sync_to_async

from .models import CVUpload, Candidate, Job, Match
from .serializers import (
    CVUploadSerializer, CandidateSerializer,
    JobSerializer, MatchSerializer, MatchListSerializer
)
from .core import (
    safe_serialize, async_to_sync_view,
    fetch_object, fetch_objects, check_exists, save_object,
    SafeSerializationMixin
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
            # Get the CV upload object
            upload = await fetch_object(CVUpload, pk=pk)
            print(f"Found upload object: {upload.id}")

            # Get the mock data
            data = await parse_cv_file(upload.file)
            print(f"Parsed data: {data}")

            # Check if a Candidate already exists for this CV
            candidate_exists = await check_exists(Candidate, source_cv=upload)
            print(f"Candidate exists: {candidate_exists}")

            if candidate_exists:
                # Update existing candidate
                candidate = await fetch_object(Candidate, source_cv=upload)

                # Update fields
                candidate.name = data['name']
                candidate.skills = data['skills']
                candidate.experience_years = data['experience_years']

                # Save the updated candidate
                await save_object(candidate)
                print(f"Updated candidate: {candidate.id}")

                # Create response serializer and use safe serialization
                response_serializer = CandidateSerializer(candidate)
                return Response(
                    safe_serialize(response_serializer),
                    status=status.HTTP_200_OK
                )
            else:
                # Create new candidate
                print("Creating new candidate")
                data['cv_id'] = upload.id

                serializer = CandidateSerializer(data=data)
                await sync_to_async(serializer.is_valid)(raise_exception=True)
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

            candidate = await fetch_object(Candidate, pk=candidate_id)
            job = await fetch_object(Job, pk=job_id)

            # Check if a match already exists
            match_exists = await check_exists(Match, candidate=candidate, job=job)

            if match_exists:
                # Get existing match
                match = await fetch_object(Match, candidate=candidate, job=job)

                # Recalculate score (optionally)
                if request.data.get('recalculate', True):
                    # Get serialized data
                    candidate_data = safe_serialize(CandidateSerializer(candidate))
                    job_data = safe_serialize(JobSerializer(job))

                    # Calculate match score and rationale
                    result = await rank_candidate(candidate_data, job_data)

                    # Update the match
                    match.score = result['score']
                    match.rationale = result['rationale']
                    await save_object(match)

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

            # Create and save the match
            match = Match(
                candidate=candidate,
                job=job,
                score=result['score'],
                rationale=result['rationale']
            )
            await save_object(match)

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

            # Create matches for each candidate-job pair
            for candidate in candidates:
                for job in jobs:
                    # Check if match already exists
                    match_exists = await check_exists(Match, candidate=candidate, job=job)

                    if match_exists:
                        # Update existing match
                        match = await fetch_object(Match, candidate=candidate, job=job)

                        # Get the data and calculate score
                        candidate_data = safe_serialize(CandidateSerializer(candidate))
                        job_data = safe_serialize(JobSerializer(job))

                        # Recalculate score and rationale
                        result = await rank_candidate(candidate_data, job_data)

                        # Update match data
                        match.score = result['score']
                        match.rationale = result['rationale']
                        await save_object(match)
                        updated_matches.append(match)

                    else:
                        # Create new match
                        # Serialize for the ranking function
                        candidate_data = safe_serialize(CandidateSerializer(candidate))
                        job_data = safe_serialize(JobSerializer(job))

                        # Calculate match score and rationale
                        result = await rank_candidate(candidate_data, job_data)

                        # Create and save the match
                        match = Match(
                            candidate=candidate,
                            job=job,
                            score=result['score'],
                            rationale=result['rationale']
                        )
                        await save_object(match)
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

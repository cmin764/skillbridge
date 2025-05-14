from rest_framework import serializers
from .models import CVUpload, Candidate, Job, Match


class CVUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for CV uploads.
    """
    class Meta:
        model = CVUpload
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class JobSerializer(serializers.ModelSerializer):
    """
    Serializer for job postings.
    """
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        """Get the actual status value as a string."""
        return obj.status

    class Meta:
        model = Job
        fields = ['id', 'title', 'requirements', 'created_at', 'status']
        read_only_fields = ['created_at']


class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer for candidate profiles.
    """
    source_cv = CVUploadSerializer(read_only=True)
    cv_id = serializers.PrimaryKeyRelatedField(
        queryset=CVUpload.objects.all(),
        write_only=True,
        source='source_cv'
    )
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        """Get the actual status value as a string."""
        return obj.status

    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'email', 'phone', 'skills',
            'experience_years', 'source_cv', 'cv_id',
            'parsed_at', 'status'
        ]
        read_only_fields = ['parsed_at']


class MatchSerializer(serializers.ModelSerializer):
    """
    Serializer for candidate-job matches.
    """
    candidate = CandidateSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    candidate_id = serializers.PrimaryKeyRelatedField(
        queryset=Candidate.objects.all(),
        write_only=True,
        source='candidate'
    )
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        write_only=True,
        source='job'
    )

    class Meta:
        model = Match
        fields = [
            'id', 'candidate', 'job', 'candidate_id', 'job_id',
            'score', 'rationale', 'matched_at'
        ]
        read_only_fields = ['matched_at']


class MatchListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing matches.
    """
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'candidate_name', 'job_title', 'score', 'matched_at']
        read_only_fields = ['matched_at']

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class StatusMixin:
    """
    A true mixin that provides a status field with active/inactive choices.
    This doesn't inherit from models.Model to avoid multiple inheritance issues.
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
    ]

    # This will be added to the model's class attributes
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        help_text=_('Whether this record is active or inactive')
    )


class CVUpload(models.Model):
    """
    Stores raw CV files for parsing.
    """
    # DRF expects multipart/form-data uploads
    file = models.FileField(upload_to='cvs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Candidate(models.Model, StatusMixin):
    """
    Parsed candidate profile.
    """
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    skills = ArrayField(models.CharField(max_length=100), default=list)
    experience_years = models.IntegerField()
    source_cv = models.OneToOneField(CVUpload, on_delete=models.CASCADE)
    parsed_at = models.DateTimeField(auto_now_add=True)


class Job(models.Model, StatusMixin):
    """
    Job postings to match against.
    """
    title = models.CharField(max_length=200)
    requirements = ArrayField(models.CharField(max_length=100), default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class Match(models.Model):
    """
    Stores a candidate-job match with score & rationale.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Match score between 0 and 100')
    )
    rationale = models.TextField()
    matched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure candidate-job pairs are unique
        unique_together = ['candidate', 'job']

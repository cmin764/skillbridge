from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class StatusBase(models.Model):
    """
    A proper abstract mixin that provides a status field with active/inactive choices.
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('inactive', _('Inactive')),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        help_text=_('Whether this record is active or inactive')
    )

    class Meta:
        abstract = True  # Mark as abstract so no DB table is created


class CVUpload(models.Model):
    """
    Stores raw CV files for parsing.
    """
    # DRF expects multipart/form-data uploads
    file = models.FileField(upload_to='cvs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Candidate(StatusBase):
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


class Job(StatusBase):
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

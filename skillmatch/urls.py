from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'cv-uploads', views.CVUploadViewSet)
router.register(r'candidates', views.CandidateViewSet)
router.register(r'jobs', views.JobViewSet)
router.register(r'matches', views.MatchViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

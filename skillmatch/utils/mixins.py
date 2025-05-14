"""
Mixins for DRF viewsets in skillmatch app.
"""
from rest_framework.response import Response
from .serializers import safe_serialize


class SafeSerializationMixin:
    """
    Mixin that provides safe serialization for viewsets.
    Overrides retrieve and list methods to use safe_serialize.
    """

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

    def create(self, request, *args, **kwargs):
        """Override create to ensure proper serialization."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Re-serialize with our custom serializer
        response_serializer = self.get_serializer(instance)
        return Response(
            safe_serialize(response_serializer),
            status=201
        )

    def update(self, request, *args, **kwargs):
        """Override update to ensure proper serialization."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        # Re-serialize with our custom serializer
        response_serializer = self.get_serializer(updated_instance)
        return Response(
            safe_serialize(response_serializer)
        )

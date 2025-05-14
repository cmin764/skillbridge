"""
Async utilities for the skillmatch app.
"""
import functools
import asyncio
from asgiref.sync import sync_to_async


def async_to_sync_view(func):
    """
    Decorator to make async views compatible with DRF.
    Wraps async functions to be used in Django REST Framework.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapped


async def fetch_object(model_cls, **lookup):
    """
    Async helper to fetch a single object from the database.

    Example:
        user = await fetch_object(User, id=1)
    """
    get_object = sync_to_async(lambda: model_cls.objects.get(**lookup))
    return await get_object()


async def fetch_objects(model_cls, **filters):
    """
    Async helper to fetch objects from the database with filters.

    Example:
        active_users = await fetch_objects(User, is_active=True)
    """
    get_objects = sync_to_async(lambda: list(model_cls.objects.filter(**filters)))
    return await get_objects()


async def check_exists(model_cls, **lookup):
    """
    Async helper to check if an object exists.

    Example:
        exists = await check_exists(User, email='user@example.com')
    """
    check = sync_to_async(lambda: model_cls.objects.filter(**lookup).exists())
    return await check()


async def save_object(obj):
    """
    Async helper to save a model instance.

    Example:
        user.name = 'New Name'
        await save_object(user)
    """
    save_func = sync_to_async(obj.save)
    await save_func()


async def serialize_object(serializer_instance):
    """
    Async helper to safely get serializer data.

    Example:
        data = await serialize_object(UserSerializer(user))
    """
    return await sync_to_async(lambda: dict(serializer_instance.data))()

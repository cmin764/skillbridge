"""
Serialization utilities for the skillmatch app.
"""

def safe_serialize(serializer):
    """Convert serializer data to a JSON-safe format."""
    try:
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

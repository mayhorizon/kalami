"""Compression utilities for large data blobs."""

import gzip
import json

# Default compression threshold: 10KB
DEFAULT_COMPRESSION_THRESHOLD = 10240


def should_compress(data, threshold=DEFAULT_COMPRESSION_THRESHOLD):
    """Check if data should be compressed based on size.

    Args:
        data: Data to check (str, dict, list, or bytes)
        threshold: Size threshold in bytes

    Returns:
        bool: True if data exceeds threshold
    """
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data)
    elif isinstance(data, str):
        data_str = data
    elif isinstance(data, bytes):
        return len(data) > threshold
    else:
        data_str = str(data)

    return len(data_str.encode('utf-8')) > threshold


def compress_if_large(data, threshold=DEFAULT_COMPRESSION_THRESHOLD):
    """Compress data if it exceeds the threshold.

    Args:
        data: Data to compress (str, dict, list, or bytes)
        threshold: Size threshold in bytes

    Returns:
        tuple: (data_to_store, is_compressed)
            - If compressed: (compressed_bytes, True)
            - If not compressed: (json_string or original_data, False)
    """
    # Convert data to JSON string if needed
    if isinstance(data, (dict, list)):
        json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
        data_bytes = json_str.encode('utf-8')
    elif isinstance(data, str):
        json_str = data
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        json_str = None
        data_bytes = data
    else:
        json_str = json.dumps(data)
        data_bytes = json_str.encode('utf-8')

    # Check if compression is needed
    if len(data_bytes) > threshold:
        compressed = gzip.compress(data_bytes, compresslevel=6)
        return compressed, True
    else:
        # Return as string for JSON column storage
        return json_str if json_str else data_bytes.decode('utf-8', errors='replace'), False


def compress_data(data):
    """Force compression of data regardless of size.

    Args:
        data: Data to compress (str, dict, list, or bytes)

    Returns:
        bytes: Compressed data
    """
    if isinstance(data, (dict, list)):
        data_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
    elif isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        data_bytes = str(data).encode('utf-8')

    return gzip.compress(data_bytes, compresslevel=6)


def decompress_data(compressed_blob):
    """Decompress a compressed data blob.

    Args:
        compressed_blob: Compressed bytes from database

    Returns:
        str: Decompressed data as string (can be parsed as JSON if needed)
    """
    if not compressed_blob:
        return None

    try:
        decompressed_bytes = gzip.decompress(compressed_blob)
        return decompressed_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decompress data: {e}")


def get_data_from_row(row, json_col='parameters_json', compressed_col='parameters_compressed',
                      flag_col='is_compressed'):
    """Extract data from a database row, handling compression automatically.

    Args:
        row: Database row (dict-like or tuple)
        json_col: Name of JSON text column
        compressed_col: Name of compressed BLOB column
        flag_col: Name of compression flag column

    Returns:
        Parsed data (dict, list, str, or None)
    """
    try:
        # Check if row is dict-like (sqlite3.Row) or tuple
        if hasattr(row, 'keys'):
            is_compressed = row[flag_col] if flag_col in row.keys() else False
            json_data = row[json_col] if json_col in row.keys() else None
            compressed_data = row[compressed_col] if compressed_col in row.keys() else None
        else:
            # Handle tuple-based rows (requires knowing column order)
            return None

        if is_compressed and compressed_data:
            # Decompress and parse JSON
            decompressed_str = decompress_data(compressed_data)
            try:
                return json.loads(decompressed_str)
            except json.JSONDecodeError:
                return decompressed_str
        elif json_data:
            # Parse JSON from text column
            try:
                return json.loads(json_data)
            except json.JSONDecodeError:
                return json_data
        else:
            return None

    except Exception as e:
        print(f"Error extracting data from row: {e}")
        return None


def format_size(size_bytes):
    """Format byte size as human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., "1.5 KB", "2.3 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

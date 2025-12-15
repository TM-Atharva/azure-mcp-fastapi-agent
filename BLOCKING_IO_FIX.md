# Fix for Hanging /me and /agents Endpoints

## Problem

The `/api/auth/me` and `/api/agents` endpoints were hanging indefinitely, causing the UI to keep loading.

## Root Cause

The issue was **blocking I/O calls made within async functions**. The Azure Table Storage SDK and Azure credential operations are synchronous (blocking) but were being called directly from async functions without proper handling.

This blocks the entire FastAPI event loop, preventing it from handling other requests or operations.

### Affected Operations:

1. **Authentication (`/api/auth/me`)**: `table_storage.create_user()` call in `get_or_create_user()`
2. **Agent Listing (`/api/agents`)**: `table_storage.create_or_update_agent()` in `_sync_agent_to_db()`
3. **Chat Operations**: Multiple `table_storage.*` calls in session and message endpoints

## Solution

Wrap all blocking I/O calls with `asyncio.to_thread()` to run them in a thread pool, preventing event loop blocking.

### Files Modified:

#### 1. `backend/auth.py`

- Added `import asyncio`
- Wrapped `table_storage.create_user()` in `get_or_create_user()` method:

```python
user_data = await asyncio.to_thread(
    table_storage.create_user,
    azure_id=azure_id,
    email=email,
    name=name
)
```

#### 2. `backend/azure_foundry.py`

- Added `import asyncio`
- Wrapped `table_storage.create_or_update_agent()` in `_sync_agent_to_db()` method
- Wrapped `table_storage.get_agent_by_id()` in `get_agent_by_id()` method

#### 3. `backend/main.py`

- Added `import asyncio`
- Wrapped all blocking table storage calls throughout:
  - `create_chat_session()`: `table_storage.create_session()`
  - `list_user_sessions()`: `table_storage.get_user_sessions()`
  - `get_session_history()`: `table_storage.get_session_by_id()`, `table_storage.get_session_messages()`
  - `send_message()`: All session and message operations
  - `delete_session()`: `table_storage.delete_session()`

## How It Works

`asyncio.to_thread()` (available in Python 3.9+) runs a synchronous function in a separate thread pool executor, allowing the async event loop to continue processing other requests while the blocking operation completes.

## Testing

After this fix:

- ✅ `/api/auth/me` should respond immediately with user profile
- ✅ `/api/agents` should respond with agent list
- ✅ All chat operations should work without hanging
- ✅ Multiple concurrent requests should be handled properly

## Performance Notes

- Thread pool operations are lightweight for I/O operations
- Azure Table Storage operations are typically fast (< 100ms)
- This solution maintains FastAPI's async/await model while properly handling synchronous dependencies

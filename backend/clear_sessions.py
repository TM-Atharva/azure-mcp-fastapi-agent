"""
Utility script to clear all test sessions from Azure Table Storage.

This will delete all sessions and messages, giving you a fresh start.
"""

from table_storage import table_storage
from azure.data.tables import TableClient

def clear_all_sessions():
    """Delete all sessions and messages"""
    print("Clearing all sessions and messages...")
    
    # Get sessions table
    sessions_table = table_storage._get_table_client("sessions")
    messages_table = table_storage._get_table_client("messages")
    
    # Delete all sessions
    sessions = list(sessions_table.list_entities())
    print(f"Found {len(sessions)} sessions to delete")
    
    for session in sessions:
        try:
            sessions_table.delete_entity(
                partition_key=session["PartitionKey"],
                row_key=session["RowKey"]
            )
            print(f"  ✓ Deleted session: {session.get('title', 'Untitled')}")
        except Exception as e:
            print(f"  ✗ Error deleting session: {e}")
    
    # Delete all messages
    messages = list(messages_table.list_entities())
    print(f"\nFound {len(messages)} messages to delete")
    
    for message in messages:
        try:
            messages_table.delete_entity(
                partition_key=message["PartitionKey"],
                row_key=message["RowKey"]
            )
        except Exception as e:
            print(f"  ✗ Error deleting message: {e}")
    
    print(f"\n✓ Cleared {len(sessions)} sessions and {len(messages)} messages")
    print("You can now start fresh!")

if __name__ == "__main__":
    confirm = input("This will delete ALL sessions and messages. Continue? (yes/no): ")
    if confirm.lower() == "yes":
        clear_all_sessions()
    else:
        print("Cancelled.")

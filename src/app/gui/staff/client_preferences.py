import streamlit as st
from typing import Any

from app.auth.account_manager import AccountManager
from app.gui.shared.toolbar import require_role
from app.users.user import UserAccess
from util.admin_utils import log_sensitive_access


def search_clients(
    query: str,
    account_manager: AccountManager,
) -> list[dict[str, Any]]:
    search_text = query.strip().casefold()
    if not search_text:
        return []

    return [
        account
        for account in account_manager.list_accounts("Client")
        if any(
            search_text in str(account.get(field, "")).casefold()
            for field in ("_name", "_account_number", "_phone_number")
        )
    ]


def show_client_preferences() -> None:
    require_role(UserAccess.STAFF)

    st.title("Client Preferences")
    st.caption(
        "Search client dietary preferences by name, account ID, or phone "
        "number. Results are limited to client accounts."
    )

    query = st.text_input("Client name, account ID, or phone number")
    if not query.strip():
        st.info("Enter a client identifier to search.")
        return

    actor = st.session_state.get("account", {})
    actor_id = str(actor.get("_account_number", "unknown"))
    actor_role = str(st.session_state.get("user_role", UserAccess.STAFF))
    log_sensitive_access(
        "view",
        actor_id,
        actor_role,
        "client_directory",
        "search",
    )
    clients = search_clients(query, st.session_state.account_manager)
    if not clients:
        st.info("No matching clients found.")
        return

    for client in clients:
        log_sensitive_access(
            "view",
            actor_id,
            actor_role,
            "client_preferences",
            str(client.get("_account_number", "unknown")),
        )
        preferences = client.get("_food_constraints", [])
        preference_text = (
            ", ".join(str(preference) for preference in preferences)
            if preferences
            else "None recorded"
        )

        with st.container(border=True):
            st.subheader(str(client.get("_name", "Unnamed client")))
            st.write("**Account ID:**", client.get("_account_number", ""))
            st.write("**Phone:**", client.get("_phone_number", ""))
            st.write("**Food preferences:**", preference_text)


if __name__ == "__main__":
    show_client_preferences()

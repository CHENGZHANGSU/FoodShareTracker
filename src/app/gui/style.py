"""Shared FoodShare Tracker styling for light and dark themes."""

import streamlit as st


def apply_app_style() -> None:
    """Apply the shared responsive palette and component styles."""
    st.markdown(
        """
        <style>
        :root {
            color-scheme: light;
            --fs-primary: #176b5b;
            --fs-primary-hover: #105346;
            --fs-primary-button-text: #ffffff;
            --fs-button-bg: #e3eee8;
            --fs-button-hover: #d3e5db;
            --fs-button-text: #24574b;
            --fs-accent: #e9852b;
            --fs-accent-hover: #cf6c16;
            --fs-accent-button-bg: #f8e6d4;
            --fs-accent-button-hover: #f3d7bc;
            --fs-accent-button-text: #704019;
            --fs-text: #24332f;
            --fs-muted: #60736d;
            --fs-background: #f7f8f4;
            --fs-surface: #ffffff;
            --fs-surface-soft: #edf3ed;
            --fs-border: #d8e2d9;
            --fs-focus: #e9852b;
            --fs-danger: #b42318;
            --fs-danger-soft: #fcebea;
            --fs-shadow: 0 8px 24px rgba(23, 65, 54, 0.08);
        }

        :root[data-theme="dark"],
        body[data-theme="dark"],
        [data-theme="dark"] {
            color-scheme: dark;
            --fs-primary: #70c5ad;
            --fs-primary-hover: #91dbc5;
            --fs-primary-button-text: #14231d;
            --fs-button-bg: #294239;
            --fs-button-hover: #354f45;
            --fs-button-text: #d8f2e6;
            --fs-accent: #ffad62;
            --fs-accent-hover: #ffc18a;
            --fs-accent-button-bg: #493421;
            --fs-accent-button-hover: #5a412a;
            --fs-accent-button-text: #ffe4c6;
            --fs-text: #edf4ef;
            --fs-muted: #b4c4bb;
            --fs-background: #111a17;
            --fs-surface: #1a2722;
            --fs-surface-soft: #22332c;
            --fs-border: #35483f;
            --fs-focus: #ffad62;
            --fs-danger: #ff8b82;
            --fs-danger-soft: #422723;
            --fs-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
        }

        @media (prefers-color-scheme: dark) {
            :root:not([data-theme="light"]) {
                color-scheme: dark;
                --fs-primary: #70c5ad;
                --fs-primary-hover: #91dbc5;
                --fs-primary-button-text: #14231d;
                --fs-button-bg: #294239;
                --fs-button-hover: #354f45;
                --fs-button-text: #d8f2e6;
                --fs-accent: #ffad62;
                --fs-accent-hover: #ffc18a;
                --fs-accent-button-bg: #493421;
                --fs-accent-button-hover: #5a412a;
                --fs-accent-button-text: #ffe4c6;
                --fs-text: #edf4ef;
                --fs-muted: #b4c4bb;
                --fs-background: #111a17;
                --fs-surface: #1a2722;
                --fs-surface-soft: #22332c;
                --fs-border: #35483f;
                --fs-focus: #ffad62;
                --fs-danger: #ff8b82;
                --fs-danger-soft: #422723;
                --fs-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);
            }
        }

        body .stApp {
            background: var(--fs-background);
            color: var(--fs-text);
        }

        body .stApp, body .stApp p, body .stApp label, body .stApp li,
        body .stApp small, body .stApp [data-testid="stMarkdownContainer"] {
            color: var(--fs-text);
        }

        body .stApp h1, body .stApp h2, body .stApp h3, body .stApp h4 {
            color: var(--fs-primary);
            letter-spacing: -0.025em;
        }

        body .stApp h1 {
            font-weight: 750;
        }

        body .stApp a {
            color: var(--fs-primary);
            text-decoration-color: var(--fs-accent);
            text-underline-offset: 0.18em;
        }

        body .stApp a:hover {
            color: var(--fs-primary-hover);
        }

        body .stApp [data-testid="stButton"] button,
        body .stApp [data-testid="stFormSubmitButton"] button,
        body .stApp [data-testid="stDownloadButton"] button {
            min-height: 2.45rem;
            padding: 0.45rem 1rem;
            border: 1px solid var(--fs-border);
            border-radius: 0.75rem;
            background: var(--fs-surface);
            color: var(--fs-primary);
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 650;
            line-height: 1.25;
            transition: background-color 140ms ease, border-color 140ms ease,
                color 140ms ease, transform 140ms ease, box-shadow 140ms ease;
        }

        body .stApp [data-testid="stButton"] button:not(:disabled):hover,
        body .stApp [data-testid="stFormSubmitButton"] button:not(:disabled):hover,
        body .stApp [data-testid="stDownloadButton"] button:not(:disabled):hover {
            border-color: var(--fs-primary);
            background: var(--fs-surface-soft);
            color: var(--fs-primary-hover);
            transform: translateY(-1px);
            box-shadow: var(--fs-shadow);
        }

        body .stApp [data-testid="stButton"] button:focus-visible,
        body .stApp [data-testid="stFormSubmitButton"] button:focus-visible,
        body .stApp [data-testid="stDownloadButton"] button:focus-visible,
        body .stApp input:focus-visible,
        body .stApp textarea:focus-visible,
        body .stApp [role="combobox"]:focus-visible {
            outline: 3px solid var(--fs-focus);
            outline-offset: 2px;
        }

        body .stApp [data-testid="stButton"] button:disabled,
        body .stApp [data-testid="stFormSubmitButton"] button:disabled,
        body .stApp [data-testid="stDownloadButton"] button:disabled {
            border-color: var(--fs-border);
            background: var(--fs-surface-soft);
            color: var(--fs-muted);
            cursor: not-allowed;
            opacity: 0.75;
            box-shadow: none;
            transform: none;
        }

        body .stApp button[kind="primary"]:not(:disabled),
        body .stApp [data-testid="stBaseButton-primary"]:not(:disabled),
        body .stApp [data-testid="stFormSubmitButton"] button[kind="primary"]:not(:disabled) {
            border-color: var(--fs-primary);
            background: var(--fs-primary);
            color: var(--fs-primary-button-text);
        }

        body .stApp button[kind="primary"]:not(:disabled):hover,
        body .stApp [data-testid="stBaseButton-primary"]:not(:disabled):hover,
        body .stApp [data-testid="stFormSubmitButton"] button[kind="primary"]:not(:disabled):hover {
            border-color: var(--fs-primary-hover);
            background: var(--fs-primary-hover);
            color: var(--fs-primary-button-text);
        }

        body .stApp [data-testid="stBaseButton-secondary"] {
            background: var(--fs-surface);
            color: var(--fs-primary);
        }

        body .stApp .st-key-disable_login_access button:not(:disabled) {
            border-color: var(--fs-danger-soft);
            background: var(--fs-danger-soft);
            color: var(--fs-danger);
        }

        body .stApp .st-key-disable_login_access button:not(:disabled):hover {
            border-color: var(--fs-danger);
            background: var(--fs-danger-soft);
            color: var(--fs-danger);
        }

        body .stApp input, body .stApp textarea,
        body .stApp [data-baseweb="select"] > div,
        body .stApp [data-baseweb="input"] > div {
            border-color: var(--fs-border);
            border-radius: 0.65rem;
            background-color: var(--fs-surface);
            color: var(--fs-text);
        }

        body .stApp input,
        body .stApp textarea,
        body .stApp [data-baseweb="select"],
        body .stApp [data-baseweb="input"] {
            font: inherit;
        }

        body .stApp input:disabled,
        body .stApp textarea:disabled,
        body .stApp [data-baseweb="select"] [aria-disabled="true"],
        body .stApp [data-baseweb="input"] [aria-disabled="true"] {
            background-color: var(--fs-surface-soft);
            color: var(--fs-muted);
            cursor: not-allowed;
        }

        body .stApp [data-testid="stTextInput"],
        body .stApp [data-testid="stTextArea"],
        body .stApp [data-testid="stSelectbox"],
        body .stApp [data-testid="stMultiSelect"],
        body .stApp [data-testid="stNumberInput"],
        body .stApp [data-testid="stDateInput"] {
            margin-bottom: 0.8rem;
        }

        body .stApp [data-testid="stWidgetLabel"] p,
        body .stApp [data-testid="stWidgetLabel"] label {
            color: var(--fs-text);
            font-size: 0.94rem;
            font-weight: 600;
        }

        body .stApp [data-baseweb="input"] input,
        body .stApp textarea,
        body .stApp [data-baseweb="select"] input {
            color: var(--fs-text) !important;
            caret-color: var(--fs-primary);
        }

        body .stApp input::placeholder,
        body .stApp textarea::placeholder {
            color: var(--fs-muted) !important;
            opacity: 0.8;
        }

        body .stApp [data-baseweb="select"] > div {
            min-height: 2.8rem;
            border-color: var(--fs-border);
            background-color: var(--fs-surface);
            color: var(--fs-text);
        }

        body .stApp [data-baseweb="select"] [role="combobox"] {
            color: var(--fs-text);
        }

        body .stApp [data-baseweb="select"] [aria-selected="true"] {
            background: var(--fs-surface-soft);
            color: var(--fs-primary);
        }

        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] ul {
            border: 1px solid var(--fs-border);
            border-radius: 0.7rem;
            background: var(--fs-surface);
            box-shadow: var(--fs-shadow);
        }

        [data-baseweb="popover"] [role="option"] {
            background: var(--fs-surface);
            color: var(--fs-text);
        }

        [data-baseweb="popover"] [role="option"]:hover,
        [data-baseweb="popover"] [role="option"][aria-selected="true"] {
            background: var(--fs-surface-soft);
            color: var(--fs-primary);
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem !important;
            min-height: 1.9rem !important;
            margin: 0.15rem !important;
            padding: 0.15rem 0.4rem 0.15rem 0.65rem !important;
            border: 1px solid var(--fs-border) !important;
            border-radius: 999px !important;
            background: var(--fs-surface-soft) !important;
            background-color: var(--fs-surface-soft) !important;
            background-image: none !important;
            color: var(--fs-primary) !important;
            font-size: 0.86rem !important;
            font-weight: 650 !important;
            line-height: 1.3 !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] * {
            box-sizing: border-box;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.15rem;
            min-height: 3rem;
            padding: 0.35rem 0.5rem;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] > span {
            color: var(--fs-primary) !important;
            font-size: 0.86rem !important;
            font-weight: 650;
            line-height: 1.3;
            padding: 0 !important;
            margin: 0 0.2rem 0 0 !important;
            white-space: nowrap;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 1.1rem !important;
            width: 1.1rem !important;
            min-width: 1.1rem !important;
            height: 1.1rem !important;
            min-height: 1.1rem !important;
            max-height: 1.1rem !important;
            margin: 0 0 0 0.15rem !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 50% !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            color: var(--fs-primary) !important;
            font-size: 0.75rem !important;
            line-height: 1 !important;
            box-shadow: none !important;
            transform: none !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] button svg {
            width: 0.65rem !important;
            height: 0.65rem !important;
            fill: currentColor !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] button:hover {
            border: 0 !important;
            background: var(--fs-button-hover) !important;
            background-color: var(--fs-button-hover) !important;
            color: var(--fs-primary) !important;
            box-shadow: none !important;
            transform: none !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] button:focus-visible {
            outline: 2px solid var(--fs-focus) !important;
            outline-offset: 1px !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] button[aria-label*="Remove"] {
            flex: 0 0 1.1rem !important;
            width: 1.1rem !important;
            min-width: 1.1rem !important;
            height: 1.1rem !important;
            min-height: 1.1rem !important;
            aspect-ratio: 1 !important;
            align-self: center !important;
        }

        body .stApp [data-testid="stMultiSelect"] [data-baseweb="tag"] > span {
            flex: 0 1 auto !important;
            min-width: 0 !important;
        }

        body .stApp [data-testid="stAlert"] {
            width: min(100%, 46rem);
            margin: 0.75rem auto;
            border: 1px solid var(--fs-border);
            border-radius: 0.8rem;
            text-align: center;
        }

        body .stApp [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
            text-align: center;
        }

        body .stApp [data-testid="stMetric"] {
            padding: 1rem 1.1rem;
            border: 1px solid var(--fs-border);
            border-radius: 1rem;
            background: var(--fs-surface);
            box-shadow: var(--fs-shadow);
        }

        body .stApp [data-testid="stMetricLabel"] {
            color: var(--fs-muted);
        }

        body .stApp [data-testid="stMetricValue"] {
            color: var(--fs-primary);
            font-weight: 750;
        }

        body .stApp [data-testid="stExpander"],
        body .stApp [data-testid="stPopover"],
        body .stApp [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--fs-border);
            border-radius: 0.9rem;
        }

        body .stApp [data-testid="stDataFrame"],
        body .stApp [data-testid="stTable"] {
            border: 1px solid var(--fs-border);
            border-radius: 0.75rem;
            overflow: hidden;
        }

        body .stApp hr {
            border-color: var(--fs-border);
        }

        body .stApp [data-testid="stAlert"] {
            border-radius: 0.8rem;
        }

        body .stApp .adjust-hero,
        body .stApp .details-hero,
        body .stApp .orders-hero,
        body .stApp .dashboard-hero,
        body .stApp .catalogue-hero,
        body .stApp .receive-hero {
            border-color: var(--fs-border);
            background: linear-gradient(120deg, var(--fs-surface-soft), var(--fs-surface));
        }

        body .stApp .alert-normal {
            background: var(--fs-surface-soft);
            color: var(--fs-primary);
        }

        body .stApp .alert-warning {
            background: color-mix(in srgb, var(--fs-accent) 18%, var(--fs-surface));
            color: var(--fs-text);
        }

        body .stApp .alert-critical {
            background: var(--fs-danger-soft);
            color: var(--fs-danger);
        }

        .fs-section {
            margin: 0.5rem 0 1rem;
            padding: clamp(1.25rem, 4vw, 2.5rem);
            border: 1px solid var(--fs-border);
            border-radius: 1.25rem;
            background:
                radial-gradient(circle at 90% 10%, rgba(233, 133, 43, 0.12), transparent 32%),
                linear-gradient(135deg, var(--fs-surface-soft), var(--fs-surface));
            box-shadow: var(--fs-shadow);
            text-align: center;
        }

        .fs-section h2 {
            margin: 0 0 0.4rem;
            font-size: clamp(1.5rem, 3vw, 2rem);
        }

        .fs-section p {
            margin: 0;
            color: var(--fs-muted);
        }

        .fs-brand-mark {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            color: var(--fs-primary);
            font-size: 1.1rem;
            font-weight: 750;
        }

        .fs-brand-mark span {
            color: var(--fs-accent);
        }

        .fs-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 1.25rem;
            padding: 1rem 1.25rem;
            border: 1px solid var(--fs-border);
            border-radius: 1rem;
            background: var(--fs-surface-soft);
            color: var(--fs-muted);
            font-size: 0.9rem;
        }

        @media (max-width: 640px) {
            .stApp [data-testid="stButton"] button,
            .stApp [data-testid="stFormSubmitButton"] button,
            .stApp [data-testid="stDownloadButton"] button {
                padding-inline: 0.7rem;
            }
            .fs-topbar {
                align-items: flex-start;
                flex-direction: column;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .stApp [data-testid="stButton"] button,
            .stApp [data-testid="stFormSubmitButton"] button,
            .stApp [data-testid="stDownloadButton"] button {
                transition: none;
            }
            .stApp [data-testid="stButton"] button:hover,
            .stApp [data-testid="stFormSubmitButton"] button:hover,
            .stApp [data-testid="stDownloadButton"] button:hover {
                transform: none;
            }
        }

        body .stApp [data-testid="stImage"] img {
            border: 1px solid var(--fs-border);
            border-radius: 1rem;
            background: #ffffff;
            box-shadow: var(--fs-shadow);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_logo() -> None:
    st.image("assets/food_share_logo.png", width=180)


def markdown_nav(active_section: str = "home") -> None:
    if active_section not in {"home", "about", "resources"}:
        active_section = "home"
    active_selector = f'div[class*="st-key-nav_{active_section.title()}_"]'
    st.markdown(
        """
        <style>
        body .stApp div[class*="st-key-nav_"] button {
            min-width: 5.5rem;
            border-color: transparent;
            background: transparent;
            color: var(--fs-primary);
        }
        body .stApp ACTIVE_SELECTOR button {
            border-color: var(--fs-button-bg);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp ACTIVE_SELECTOR button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-hover);
            color: var(--fs-button-text);
        }
        </style>
        """.replace("ACTIVE_SELECTOR", active_selector),
        unsafe_allow_html=True,
    )


def markdown_header() -> None:
    st.markdown(
        """
        <style>
        body .stApp .st-key-register button {
            border-color: var(--fs-accent-button-bg);
            background: var(--fs-accent-button-bg);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-register button:hover {
            border-color: var(--fs-accent-button-hover);
            background: var(--fs-accent-button-hover);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-login button {
            border-color: var(--fs-button-bg);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-login button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-hover);
            color: var(--fs-button-text);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_image() -> None:
    st.image(
        "assets/food_share_logo.png",
        width=260,
        caption="Sharing good food, strengthening our community.",
    )


def show_dashboard_header(title: str, fallback_name: str) -> None:
    account = st.session_state.get("account", {})
    name = account.get("_name", fallback_name) if isinstance(account, dict) else fallback_name
    st.markdown(
        """
        <style>
        .fs-dashboard-hero {
            background: linear-gradient(
                120deg,
                var(--fs-surface-soft),
                var(--fs-surface)
            );
            padding: 1.75rem 1.875rem;
            border: 1px solid var(--fs-border);
            border-radius: 1.125rem;
            margin-bottom: 1.375rem;
        }
        .fs-dashboard-hero h1 {
            color: var(--fs-primary);
            font-size: 1.875rem;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="fs-dashboard-hero"><h1>{title}</h1></div>',
        unsafe_allow_html=True,
    )
    st.write(f"Welcome, {name}.")


def apply_staff_dashboard_style() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: var(--fs-surface);
            border: 1px solid var(--fs-border);
            padding: 15px;
            border-radius: 13px;
        }

        .alert-normal {
            background: var(--fs-surface-soft);
            border-left: 5px solid var(--fs-primary);
            color: var(--fs-text);
            border-radius: 10px;
            padding: 13px 15px;
            margin: 8px 0 12px 0;
        }

        .alert-warning {
            background: var(--fs-accent-button-bg);
            border-left: 5px solid var(--fs-accent);
            color: var(--fs-accent-button-text);
            border-radius: 10px;
            padding: 13px 15px;
            margin: 8px 0 12px 0;
        }

        .alert-critical {
            background: var(--fs-danger-soft);
            border-left: 5px solid var(--fs-danger);
            color: var(--fs-danger);
            border-radius: 10px;
            padding: 13px 15px;
            margin: 8px 0 12px 0;
        }

        .section-caption {
            color: var(--fs-muted);
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_section() -> None:
    st.markdown(
        """
        <section class="fs-section">
            <h2>Good food is better when it is shared</h2>
            <p>Connecting food, people, and local communities.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def markdown_bar() -> None:
    st.markdown(
        """
        <footer class="fs-topbar">
            <div class="fs-brand-mark">Food<span>Share</span> Tracker</div>
            <div>Reducing food waste. Supporting our community.</div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def markdown_button() -> None:
    st.markdown(
        """
        <style>
        body .stApp .st-key-helps_page button,
        body .stApp .st-key-to_login button,
        body .stApp .st-key-to_register button,
        body .stApp .st-key-change_password button,
        body .stApp .st-key-edit_profile button {
            border-color: var(--fs-border);
            background: var(--fs-surface-soft);
            color: var(--fs-primary);
        }
        body .stApp .st-key-to_login button,
        body .stApp .st-key-to_register button {
            border-color: var(--fs-button-bg);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-to_login button:hover,
        body .stApp .st-key-to_register button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-hover);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-register_account button,
        body .stApp .st-key-login_account button {
            border-color: var(--fs-accent-button-bg);
            background: var(--fs-accent-button-bg);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-register_account button:hover,
        body .stApp .st-key-login_account button:hover {
            border-color: var(--fs-accent-button-hover);
            background: var(--fs-accent-button-hover);
            color: var(--fs-accent-button-text);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_home() -> None:
    st.markdown(
        """
        <style>
        body .stApp .st-key-home_page button,
        body .stApp .st-key-client_order_home button {
            border-color: var(--fs-button-bg);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-home_page button:hover,
        body .stApp .st-key-client_order_home button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-hover);
            color: var(--fs-button-text);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_help_links() -> None:
    st.markdown(
        """
        <style>
        body .stApp .st-key-help_dashboard_link button {
            border-color: var(--fs-accent-button-bg);
            background: var(--fs-accent-button-bg);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-help_dashboard_link button:hover {
            border-color: var(--fs-accent-button-hover);
            background: var(--fs-accent-button-hover);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-help_dashboard_login button {
            border-color: var(--fs-accent-button-bg);
            background: var(--fs-accent-button-bg);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-help_dashboard_login button:hover {
            border-color: var(--fs-accent-button-hover);
            background: var(--fs-accent-button-hover);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-home_page button {
            border-color: var(--fs-button-bg);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-home_page button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-hover);
            color: var(--fs-button-text);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def markdown_logout() -> None:
    st.markdown(
        """
        <style>
        body .stApp .st-key-logout button {
            border-color: var(--fs-danger-soft);
            background: var(--fs-danger-soft);
            color: var(--fs-danger);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def makrdown_options() -> None:
    st.markdown(
        """
        <style>
        body .stApp div[class*="st-key-option_"] button,
        body .stApp .st-key-back_ordering button,
        body .stApp .st-key-client_order_helps button {
            border-color: var(--fs-border);
            background: var(--fs-surface-soft);
            color: var(--fs-primary);
        }
        body .stApp div[class*="st-key-option_"] button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        body .stApp .st-key-back_ordering button {
            border-color: var(--fs-accent-button-bg);
            background: var(--fs-accent-button-bg);
            color: var(--fs-accent-button-text);
        }
        body .stApp .st-key-back_ordering button:hover {
            border-color: var(--fs-accent-button-hover);
            background: var(--fs-accent-button-hover);
            color: var(--fs-accent-button-text);
        }
        body .stApp div[class*="st-key-option_Helps"] button,
        body .stApp .st-key-client_order_helps button {
            border-color: var(--fs-border);
            background: var(--fs-surface);
            color: var(--fs-primary);
        }
        body .stApp div[class*="st-key-option_Helps"] button:hover,
        body .stApp .st-key-client_order_helps button:hover {
            border-color: var(--fs-button-hover);
            background: var(--fs-button-bg);
            color: var(--fs-button-text);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

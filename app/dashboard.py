from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from claude_analytics.dashboard.data import load_dashboard_data


st.set_page_config(
    page_title="Claude Code Analytics",
    page_icon="CC",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(232, 126, 42, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(0, 140, 255, 0.16), transparent 28%),
                linear-gradient(180deg, #f6f3ee 0%, #f9f8f4 100%);
        }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        .hero-card {
            padding: 1.4rem 1.6rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(18, 44, 52, 0.95), rgba(35, 74, 68, 0.92));
            color: #f9f4ea;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 18px 50px rgba(18, 44, 52, 0.18);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            opacity: 0.84;
            line-height: 1.5;
        }
        .metric-card {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(18, 44, 52, 0.08);
            border-radius: 18px;
            padding: 1rem 1rem 0.8rem 1rem;
            box-shadow: 0 8px 30px rgba(35, 44, 52, 0.06);
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #17373b;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False, ttl=300)
def get_dashboard_payload() -> dict[str, object]:
    return load_dashboard_data()


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Claude Code Analytics Platform</div>
            <div class="hero-subtitle">
                Interactive usage intelligence across adoption, cost, models, tools, reliability, and session behavior.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(payload: dict[str, object]) -> None:
    overview = payload["overview"].to_dict()
    cards = [
        ("Employees", f"{overview['total_employees']:,}"),
        ("Active Users", f"{overview['active_users']:,}"),
        ("Sessions", f"{overview['total_sessions']:,}"),
        ("Events", f"{overview['total_events']:,}"),
        ("Total Cost", f"${overview['total_cost_usd']:,.2f}"),
        ("API Error Rate", f"{overview['api_error_rate_pct']:.2f}%"),
    ]
    cols = st.columns(len(cards))
    for col, (label, value) in zip(cols, cards):
        with col:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(label, value)
            st.markdown("</div>", unsafe_allow_html=True)

    trend_df: pd.DataFrame = payload["daily_trend"].copy()
    peak_hours_df: pd.DataFrame = payload["peak_hours"].copy()
    practice_df: pd.DataFrame = payload["adoption_practice"].copy()

    left, right = st.columns((1.8, 1.1))
    with left:
        st.markdown('<div class="section-title">Daily Usage Trend</div>', unsafe_allow_html=True)
        trend_chart = px.line(
            trend_df,
            x="event_date",
            y=["total_cost_usd", "total_sessions"],
            markers=True,
            color_discrete_sequence=["#cf6a32", "#1c7c74"],
        )
        trend_chart.update_layout(
            legend_title_text="",
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            yaxis_title="Value",
            xaxis_title="Date",
        )
        st.plotly_chart(trend_chart, use_container_width=True)
    with right:
        st.markdown('<div class="section-title">Peak Usage Hours</div>', unsafe_allow_html=True)
        peak_chart = px.bar(
            peak_hours_df,
            x="event_hour",
            y="total_events",
            color="active_users",
            color_continuous_scale="Tealgrn",
        )
        peak_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title="Hour of Day",
            yaxis_title="Events",
        )
        st.plotly_chart(peak_chart, use_container_width=True)

    st.markdown('<div class="section-title">Top Practices by Cost</div>', unsafe_allow_html=True)
    practice_chart = px.bar(
        practice_df.sort_values("total_cost_usd", ascending=False),
        x="dimension",
        y="total_cost_usd",
        color="active_users",
        color_continuous_scale="Sunsetdark",
    )
    practice_chart.update_layout(
        margin=dict(l=10, r=10, t=16, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.75)",
        xaxis_title="Practice",
        yaxis_title="Total Cost (USD)",
    )
    st.plotly_chart(practice_chart, use_container_width=True)


def render_adoption(payload: dict[str, object]) -> None:
    st.markdown('<div class="section-title">Adoption Breakdown</div>', unsafe_allow_html=True)
    option_map = {
        "Practice": payload["adoption_practice"],
        "Level": payload["adoption_level"],
        "Location": payload["adoption_location"],
        "Terminal": payload["adoption_terminal"],
        "OS": payload["adoption_os"],
    }
    dimension = st.selectbox("View adoption by", list(option_map), index=0)
    df: pd.DataFrame = option_map[dimension].copy()

    left, right = st.columns((1.2, 1))
    with left:
        adoption_chart = px.bar(
            df.sort_values("total_sessions", ascending=False),
            x="dimension",
            y=["active_users", "total_sessions"],
            barmode="group",
            color_discrete_sequence=["#1c7c74", "#cf6a32"],
        )
        adoption_chart.update_layout(
            legend_title_text="",
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title=dimension,
            yaxis_title="Count",
        )
        st.plotly_chart(adoption_chart, use_container_width=True)
    with right:
        cost_chart = px.pie(
            df,
            names="dimension",
            values="total_cost_usd",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Tealgrn,
        )
        cost_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(cost_chart, use_container_width=True)

    st.dataframe(
        df.rename(
            columns={
                "dimension": dimension,
                "active_users": "Active Users",
                "total_sessions": "Sessions",
                "total_events": "Events",
                "total_cost_usd": "Cost (USD)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_models_tools(payload: dict[str, object]) -> None:
    models_df: pd.DataFrame = payload["models"].copy()
    tools_df: pd.DataFrame = payload["tools"].copy()

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="section-title">Models & Cost</div>', unsafe_allow_html=True)
        model_chart = px.scatter(
            models_df,
            x="total_input_tokens",
            y="total_cost_usd",
            size="api_requests",
            color="model",
            hover_name="model",
        )
        model_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title="Input Tokens",
            yaxis_title="Total Cost (USD)",
        )
        st.plotly_chart(model_chart, use_container_width=True)
        st.dataframe(models_df, use_container_width=True, hide_index=True)
    with right:
        st.markdown('<div class="section-title">Tools & Success Rate</div>', unsafe_allow_html=True)
        tool_chart = px.bar(
            tools_df.head(10),
            x="tool_name",
            y="tool_decisions",
            color="success_rate_pct",
            color_continuous_scale="Brwnyl",
        )
        tool_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title="Tool",
            yaxis_title="Decisions",
        )
        st.plotly_chart(tool_chart, use_container_width=True)
        st.dataframe(tools_df, use_container_width=True, hide_index=True)


def render_reliability_sessions(payload: dict[str, object]) -> None:
    errors_df: pd.DataFrame = payload["errors"].copy()
    sessions_df: pd.DataFrame = payload["top_sessions"].copy()

    left, right = st.columns((1, 1.2))
    with left:
        st.markdown('<div class="section-title">Reliability</div>', unsafe_allow_html=True)
        error_chart = px.bar(
            errors_df,
            x="status_code",
            y="error_count",
            color="status_code",
            hover_data={"error_message": True},
            color_discrete_sequence=["#b23a48", "#cf6a32", "#1c7c74", "#2f4858", "#8d6a9f"],
        )
        error_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title="Status Code",
            yaxis_title="API Error Count",
            showlegend=False,
        )
        st.plotly_chart(error_chart, use_container_width=True)
        st.dataframe(errors_df, use_container_width=True, hide_index=True)
    with right:
        st.markdown('<div class="section-title">Top Sessions</div>', unsafe_allow_html=True)
        session_chart = px.bar(
            sessions_df,
            x="total_cost_usd",
            y="session_id",
            color="employee_practice",
            orientation="h",
        )
        session_chart.update_layout(
            margin=dict(l=10, r=10, t=16, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(255,255,255,0.75)",
            xaxis_title="Total Cost (USD)",
            yaxis_title="Session",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(session_chart, use_container_width=True)
        st.dataframe(sessions_df, use_container_width=True, hide_index=True)


def main() -> None:
    inject_styles()
    render_hero()
    payload = get_dashboard_payload()

    with st.sidebar:
        st.markdown("### Dashboard Scope")
        st.caption("Data source: PostgreSQL analytics backend loaded from synthetic Claude Code telemetry.")
        st.markdown(
            "- Overview KPIs\n"
            "- Adoption segmentation\n"
            "- Model and tool behavior\n"
            "- Reliability patterns\n"
            "- Session highlights"
        )

    overview_tab, adoption_tab, models_tab, reliability_tab = st.tabs(
        ["Overview", "Adoption", "Models & Tools", "Reliability & Sessions"]
    )

    with overview_tab:
        render_overview(payload)
    with adoption_tab:
        render_adoption(payload)
    with models_tab:
        render_models_tools(payload)
    with reliability_tab:
        render_reliability_sessions(payload)


if __name__ == "__main__":
    main()

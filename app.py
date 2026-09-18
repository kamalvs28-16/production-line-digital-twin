import streamlit as st
import pandas as pd
import plotly.express as px

from simulator import run_simulation

# Optional recommendation module
try:
    from recommendations import generate_recommendations
    RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    RECOMMENDATIONS_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LineLens Twin",
    page_icon="🏭",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("🏭 LineLens Twin")
st.subheader("Production Line Digital Twin & Bottleneck Intelligence")

st.write(
    "A simulation-based manufacturing analytics system for "
    "bottleneck detection, delay analysis, downtime propagation, "
    "throughput analysis and what-if decision support."
)


# ============================================================
# PRODUCTION FLOW
# ============================================================

st.markdown(
    """
### 🏭 Production Flow

**Cutting → Drilling → Assembly → Inspection**
"""
)


# ============================================================
# PRODUCTION STAGES
# ============================================================

stages = [
    "Cutting",
    "Drilling",
    "Assembly",
    "Inspection"
]


# ============================================================
# BASELINE PARAMETERS
# ============================================================

baseline_times = {
    "Cutting": 2.0,
    "Drilling": 3.0,
    "Assembly": 2.5,
    "Inspection": 1.5
}

baseline_capacity = {
    "Cutting": 1,
    "Drilling": 1,
    "Assembly": 1,
    "Inspection": 1
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙️ What-if Controls")

st.sidebar.write(
    "Change production conditions and observe the "
    "simulated effect on the manufacturing line."
)


changed_machine = st.sidebar.selectbox(
    "Machine to modify",
    stages,
    index=1
)


new_process_time = st.sidebar.slider(
    "Processing time (minutes/unit)",
    min_value=0.5,
    max_value=8.0,
    value=float(baseline_times[changed_machine]),
    step=0.1
)


new_capacity = st.sidebar.slider(
    "Parallel machines",
    min_value=1,
    max_value=3,
    value=1,
    step=1
)


# ============================================================
# DOWNTIME SETTINGS
# ============================================================

downtime_option = st.sidebar.selectbox(
    "Machine with downtime",
    ["None"] + stages
)


if downtime_option == "None":
    downtime_machine = None
else:
    downtime_machine = downtime_option


downtime_start = st.sidebar.slider(
    "Downtime starts at minute",
    min_value=0,
    max_value=420,
    value=180,
    step=10
)


downtime_duration = st.sidebar.slider(
    "Downtime duration (minutes)",
    min_value=0,
    max_value=120,
    value=30,
    step=5
)


# ============================================================
# SIMULATION DURATION
# ============================================================

simulation_minutes = st.sidebar.selectbox(
    "Simulation duration",
    [240, 480, 720],
    index=1
)


# ============================================================
# CREATE SCENARIO
# ============================================================

scenario_times = baseline_times.copy()
scenario_capacity = baseline_capacity.copy()

scenario_times[changed_machine] = new_process_time
scenario_capacity[changed_machine] = new_capacity


# ============================================================
# BASELINE SIMULATION
# ============================================================

baseline_kpis, baseline_summary, baseline_events = run_simulation(
    process_times=baseline_times,
    capacities=baseline_capacity,
    simulation_minutes=simulation_minutes,
    seed=42
)


# ============================================================
# WHAT-IF SIMULATION
# ============================================================

scenario_kpis, scenario_summary, scenario_events = run_simulation(
    process_times=scenario_times,
    capacities=scenario_capacity,
    downtime_machine=downtime_machine,
    downtime_start=downtime_start,
    downtime_duration=downtime_duration,
    simulation_minutes=simulation_minutes,
    seed=42
)


# ============================================================
# VALIDATION
# ============================================================

if not baseline_kpis or not scenario_kpis:

    st.error(
        "Simulation did not generate enough production data. "
        "Please increase the simulation duration."
    )

    st.stop()


# ============================================================
# KPI CALCULATIONS
# ============================================================

baseline_completed = baseline_kpis["completed_units"]
scenario_completed = scenario_kpis["completed_units"]

baseline_throughput = baseline_kpis["throughput_per_hour"]
scenario_throughput = scenario_kpis["throughput_per_hour"]

throughput_difference = (
    scenario_throughput - baseline_throughput
)

completed_difference = (
    scenario_completed - baseline_completed
)

throughput_loss = max(
    baseline_completed - scenario_completed,
    0
)


# ============================================================
# STAGE COMPARISON
# ============================================================

comparison = pd.merge(
    baseline_summary[
        [
            "stage",
            "avg_process_time_min",
            "avg_waiting_time_min",
            "avg_queue_length",
            "utilization_pct",
            "units_processed"
        ]
    ],
    scenario_summary[
        [
            "stage",
            "avg_process_time_min",
            "avg_waiting_time_min",
            "avg_queue_length",
            "utilization_pct",
            "units_processed"
        ]
    ],
    on="stage",
    suffixes=("_baseline", "_scenario")
)


# ============================================================
# DELAY ANALYSIS
# ============================================================

comparison["processing_time_difference"] = (
    comparison["avg_process_time_min_scenario"]
    -
    comparison["avg_process_time_min_baseline"]
)

comparison["waiting_time_difference"] = (
    comparison["avg_waiting_time_min_scenario"]
    -
    comparison["avg_waiting_time_min_baseline"]
)

comparison["queue_difference"] = (
    comparison["avg_queue_length_scenario"]
    -
    comparison["avg_queue_length_baseline"]
)

comparison["utilization_difference"] = (
    comparison["utilization_pct_scenario"]
    -
    comparison["utilization_pct_baseline"]
)

comparison["total_time_baseline"] = (
    comparison["avg_process_time_min_baseline"]
    +
    comparison["avg_waiting_time_min_baseline"]
)

comparison["total_time_scenario"] = (
    comparison["avg_process_time_min_scenario"]
    +
    comparison["avg_waiting_time_min_scenario"]
)

comparison["total_time_difference"] = (
    comparison["total_time_scenario"]
    -
    comparison["total_time_baseline"]
)


# ============================================================
# BOTTLENECK
# ============================================================

bottleneck = scenario_kpis["bottleneck"]

bottleneck_data = comparison[
    comparison["stage"] == bottleneck
]


if not bottleneck_data.empty:

    bottleneck_row = bottleneck_data.iloc[0]

    bottleneck_baseline_wait = float(
        bottleneck_row["avg_waiting_time_min_baseline"]
    )

    bottleneck_scenario_wait = float(
        bottleneck_row["avg_waiting_time_min_scenario"]
    )

    bottleneck_wait_difference = float(
        bottleneck_row["waiting_time_difference"]
    )

    bottleneck_baseline_total = float(
        bottleneck_row["total_time_baseline"]
    )

    bottleneck_scenario_total = float(
        bottleneck_row["total_time_scenario"]
    )

    bottleneck_total_difference = float(
        bottleneck_row["total_time_difference"]
    )

    bottleneck_util = float(
        bottleneck_row["utilization_pct_scenario"]
    )

    bottleneck_queue = float(
        bottleneck_row["avg_queue_length_scenario"]
    )

else:

    bottleneck_baseline_wait = 0
    bottleneck_scenario_wait = 0
    bottleneck_wait_difference = 0
    bottleneck_baseline_total = 0
    bottleneck_scenario_total = 0
    bottleneck_total_difference = 0
    bottleneck_util = 0
    bottleneck_queue = 0


# ============================================================
# CURRENT SCENARIO
# ============================================================

st.subheader("🔬 Current Simulation Scenario")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Modified Machine",
        changed_machine
    )

with c2:
    st.metric(
        "Processing Time",
        f"{new_process_time:.1f} min"
    )

with c3:
    st.metric(
        "Parallel Machines",
        new_capacity
    )

with c4:

    if downtime_machine:

        st.metric(
            "Downtime",
            f"{downtime_duration} min"
        )

    else:

        st.metric(
            "Downtime",
            "None"
        )


# ============================================================
# MAIN KPIs
# ============================================================

st.subheader("📊 Decision KPIs")

k1, k2, k3, k4 = st.columns(4)

with k1:

    st.metric(
        "Scenario Throughput",
        f"{scenario_throughput:.2f} units/hour",
        f"{throughput_difference:+.2f}"
    )

with k2:

    st.metric(
        "Completed Units",
        scenario_completed,
        f"{completed_difference:+d}"
    )

with k3:

    st.metric(
        "Detected Bottleneck",
        bottleneck
    )

with k4:

    st.metric(
        "Throughput Loss",
        f"{throughput_loss} units"
    )


# ============================================================
# BOTTLENECK DELAY ANALYSIS
# ============================================================

st.subheader("⏱️ Bottleneck Delay Analysis")

d1, d2, d3, d4 = st.columns(4)

with d1:

    st.metric(
        "Baseline Waiting",
        f"{bottleneck_baseline_wait:.2f} min"
    )

with d2:

    st.metric(
        "Scenario Waiting",
        f"{bottleneck_scenario_wait:.2f} min"
    )

with d3:

    st.metric(
        "Delay Difference",
        f"{bottleneck_wait_difference:+.2f} min"
    )

with d4:

    st.metric(
        "Total Time Difference",
        f"{bottleneck_total_difference:+.2f} min"
    )


# ============================================================
# DELAY EXPLANATION
# ============================================================

if bottleneck_wait_difference > 0.01:

    st.warning(
        f"⚠️ **{bottleneck} delay increased by "
        f"{bottleneck_wait_difference:.2f} minutes.** "
        f"Baseline waiting time was "
        f"{bottleneck_baseline_wait:.2f} minutes and "
        f"scenario waiting time is "
        f"{bottleneck_scenario_wait:.2f} minutes."
    )

elif bottleneck_wait_difference < -0.01:

    st.success(
        f"✅ **{bottleneck} waiting time decreased by "
        f"{abs(bottleneck_wait_difference):.2f} minutes.**"
    )

else:

    st.info(
        f"ℹ️ Waiting-time difference at {bottleneck} "
        f"is approximately zero."
    )


# ============================================================
# STAGE DELAY TABLE
# ============================================================

st.subheader("📋 Stage-by-Stage Delay Comparison")

delay_table = comparison[
    [
        "stage",
        "avg_process_time_min_baseline",
        "avg_process_time_min_scenario",
        "avg_waiting_time_min_baseline",
        "avg_waiting_time_min_scenario",
        "waiting_time_difference",
        "total_time_baseline",
        "total_time_scenario",
        "total_time_difference"
    ]
].copy()


delay_table.columns = [
    "Stage",
    "Baseline Processing",
    "Scenario Processing",
    "Baseline Waiting",
    "Scenario Waiting",
    "Delay Difference",
    "Baseline Total Time",
    "Scenario Total Time",
    "Total Time Difference"
]


st.dataframe(
    delay_table.round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# WAITING TIME CHART
# ============================================================

st.subheader("📈 Waiting Time Comparison")

delay_chart = comparison[
    [
        "stage",
        "avg_waiting_time_min_baseline",
        "avg_waiting_time_min_scenario"
    ]
].copy()


delay_chart = delay_chart.melt(
    id_vars="stage",
    value_vars=[
        "avg_waiting_time_min_baseline",
        "avg_waiting_time_min_scenario"
    ],
    var_name="Scenario",
    value_name="Waiting Time (minutes)"
)


delay_chart["Scenario"] = delay_chart["Scenario"].replace(
    {
        "avg_waiting_time_min_baseline": "Baseline",
        "avg_waiting_time_min_scenario": "What-if"
    }
)


fig_delay = px.bar(
    delay_chart,
    x="stage",
    y="Waiting Time (minutes)",
    color="Scenario",
    barmode="group",
    text="Waiting Time (minutes)",
    title="Waiting / Delay at Each Production Stage"
)


fig_delay.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)


st.plotly_chart(
    fig_delay,
    use_container_width=True
)


# ============================================================
# PROCESSING TIME CHART
# ============================================================

st.subheader("⚙️ Processing Time Comparison")

process_chart = comparison[
    [
        "stage",
        "avg_process_time_min_baseline",
        "avg_process_time_min_scenario"
    ]
].copy()


process_chart = process_chart.melt(
    id_vars="stage",
    value_vars=[
        "avg_process_time_min_baseline",
        "avg_process_time_min_scenario"
    ],
    var_name="Scenario",
    value_name="Processing Time (minutes)"
)


process_chart["Scenario"] = process_chart["Scenario"].replace(
    {
        "avg_process_time_min_baseline": "Baseline",
        "avg_process_time_min_scenario": "What-if"
    }
)


fig_process = px.bar(
    process_chart,
    x="stage",
    y="Processing Time (minutes)",
    color="Scenario",
    barmode="group",
    text="Processing Time (minutes)",
    title="Processing Time by Production Stage"
)


fig_process.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)


st.plotly_chart(
    fig_process,
    use_container_width=True
)


# ============================================================
# TOTAL TIME CHART
# ============================================================

st.subheader("🕒 Total Stage Time")

total_chart = comparison[
    [
        "stage",
        "total_time_baseline",
        "total_time_scenario"
    ]
].copy()


total_chart = total_chart.melt(
    id_vars="stage",
    value_vars=[
        "total_time_baseline",
        "total_time_scenario"
    ],
    var_name="Scenario",
    value_name="Total Time (minutes)"
)


total_chart["Scenario"] = total_chart["Scenario"].replace(
    {
        "total_time_baseline": "Baseline",
        "total_time_scenario": "What-if"
    }
)


fig_total = px.bar(
    total_chart,
    x="stage",
    y="Total Time (minutes)",
    color="Scenario",
    barmode="group",
    text="Total Time (minutes)",
    title="Processing + Waiting Time"
)


fig_total.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)


st.plotly_chart(
    fig_total,
    use_container_width=True
)


# ============================================================
# UTILIZATION
# ============================================================

st.subheader("🚦 Resource Utilization")

util_chart = comparison[
    [
        "stage",
        "utilization_pct_baseline",
        "utilization_pct_scenario"
    ]
].copy()


util_chart = util_chart.melt(
    id_vars="stage",
    value_vars=[
        "utilization_pct_baseline",
        "utilization_pct_scenario"
    ],
    var_name="Scenario",
    value_name="Utilization (%)"
)


util_chart["Scenario"] = util_chart["Scenario"].replace(
    {
        "utilization_pct_baseline": "Baseline",
        "utilization_pct_scenario": "What-if"
    }
)


fig_util = px.bar(
    util_chart,
    x="stage",
    y="Utilization (%)",
    color="Scenario",
    barmode="group",
    text="Utilization (%)",
    title="Machine Utilization"
)


fig_util.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside"
)


fig_util.update_yaxes(
    range=[0, 110]
)


st.plotly_chart(
    fig_util,
    use_container_width=True
)


# ============================================================
# QUEUE LENGTH
# ============================================================

st.subheader("📦 Queue Growth")

queue_chart = comparison[
    [
        "stage",
        "avg_queue_length_baseline",
        "avg_queue_length_scenario"
    ]
].copy()


queue_chart = queue_chart.melt(
    id_vars="stage",
    value_vars=[
        "avg_queue_length_baseline",
        "avg_queue_length_scenario"
    ],
    var_name="Scenario",
    value_name="Average Queue Length"
)


queue_chart["Scenario"] = queue_chart["Scenario"].replace(
    {
        "avg_queue_length_baseline": "Baseline",
        "avg_queue_length_scenario": "What-if"
    }
)


fig_queue = px.bar(
    queue_chart,
    x="stage",
    y="Average Queue Length",
    color="Scenario",
    barmode="group",
    text="Average Queue Length",
    title="Average Queue Length by Stage"
)


fig_queue.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)


st.plotly_chart(
    fig_queue,
    use_container_width=True
)


# ============================================================
# BOTTLENECK INTELLIGENCE
# ============================================================

st.subheader("🔎 Bottleneck Intelligence")

st.info(
    f"""
### Detected Bottleneck: **{bottleneck}**

**Utilization:** {bottleneck_util:.1f}%

**Average Waiting Time:** {bottleneck_scenario_wait:.2f} minutes

**Average Queue Length:** {bottleneck_queue:.2f} units

**Total Stage Time:** {bottleneck_scenario_total:.2f} minutes

**Waiting Difference:** {bottleneck_wait_difference:+.2f} minutes

**Total Time Difference:** {bottleneck_total_difference:+.2f} minutes
"""
)


# ============================================================
# DECISION SUPPORT
# ============================================================

st.subheader("💡 Decision Support")


if RECOMMENDATIONS_AVAILABLE:

    try:

        recommendations = generate_recommendations(
            kpis=scenario_kpis,
            summary=scenario_summary,
            changed_machine=changed_machine,
            new_process_time=new_process_time,
            baseline_times=baseline_times,
            new_capacity=new_capacity,
            baseline_capacity=baseline_capacity,
            downtime_machine=downtime_machine,
            downtime_duration=downtime_duration
        )

        if recommendations:

            for rec in recommendations:

                priority = rec.get(
                    "priority",
                    "MEDIUM"
                )

                action = rec.get(
                    "action",
                    "Review the affected production stage."
                )

                reason = rec.get(
                    "reason",
                    ""
                )

                if priority == "HIGH":

                    st.error(
                        f"🔴 **HIGH PRIORITY**\n\n"
                        f"**Action:** {action}\n\n"
                        f"**Reason:** {reason}"
                    )

                elif priority == "MEDIUM":

                    st.warning(
                        f"🟡 **MEDIUM PRIORITY**\n\n"
                        f"**Action:** {action}\n\n"
                        f"**Reason:** {reason}"
                    )

                else:

                    st.success(
                        f"🟢 **LOW PRIORITY**\n\n"
                        f"**Action:** {action}\n\n"
                        f"**Reason:** {reason}"
                    )

        else:

            st.info(
                "No additional recommendations were generated."
            )

    except Exception as e:

        st.warning(
            f"Recommendation module could not be executed: {e}"
        )

else:

    if bottleneck_util >= 90:

        st.warning(
            f"Capacity Review: {bottleneck} has "
            f"{bottleneck_util:.1f}% utilization. "
            f"Test additional parallel machine capacity."
        )

    if bottleneck_wait_difference > 1:

        st.warning(
            f"Delay Review: waiting time at {bottleneck} "
            f"increased by {bottleneck_wait_difference:.2f} minutes."
        )

    if throughput_loss > 0:

        st.info(
            f"Throughput Impact: the scenario produces "
            f"{throughput_loss} fewer completed units "
            f"than the baseline."
        )


# ============================================================
# DOWNTIME PROPAGATION
# ============================================================

st.subheader("🔴 Downtime Propagation")


if downtime_machine and downtime_duration > 0:

    downstream_stages = stages[
        stages.index(downtime_machine) + 1:
    ]

    downstream_wait = scenario_kpis.get(
        "avg_downstream_wait_min",
        0
    )

    st.warning(
        f"""
### Downtime Event

**Machine:** {downtime_machine}

**Start:** {downtime_start} minutes

**Duration:** {downtime_duration} minutes

**End:** {downtime_start + downtime_duration} minutes
"""
    )

    st.metric(
        "Average Downstream Waiting",
        f"{downstream_wait:.2f} minutes"
    )

    if downstream_stages:

        st.write(
            "**Affected downstream stages:** "
            + " → ".join(downstream_stages)
        )

    st.markdown(
        """
### Propagation Logic

**Downtime**

↓

**Production interruption**

↓

**Queue / waiting changes**

↓

**Downstream impact**

↓

**Throughput impact**
"""
    )

else:

    st.success(
        "No downtime event is enabled in the current scenario."
    )


# ============================================================
# THROUGHPUT COMPARISON
# ============================================================

st.subheader("⚖️ Baseline vs What-if Throughput")

throughput_df = pd.DataFrame(
    {
        "Scenario": [
            "Baseline",
            "What-if"
        ],
        "Throughput": [
            baseline_throughput,
            scenario_throughput
        ]
    }
)


fig_throughput = px.bar(
    throughput_df,
    x="Scenario",
    y="Throughput",
    text="Throughput",
    title="Production Throughput Comparison"
)


fig_throughput.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)


st.plotly_chart(
    fig_throughput,
    use_container_width=True
)


# ============================================================
# STAGE LEVEL TABLE
# ============================================================

st.subheader("🏭 Stage-Level Intelligence")

display_summary = scenario_summary.copy()

st.dataframe(
    display_summary.round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PRODUCTION TIMELINE
# ============================================================

st.subheader("⏱️ Production Flow Timeline")


if not scenario_events.empty:

    timeline = scenario_events.copy()

    timeline = timeline.head(120)

    timeline["Start"] = (
        pd.Timestamp("2026-01-01")
        +
        pd.to_timedelta(
            timeline["start_time"],
            unit="m"
        )
    )

    timeline["Finish"] = (
        pd.Timestamp("2026-01-01")
        +
        pd.to_timedelta(
            timeline["end_time"],
            unit="m"
        )
    )

    timeline["Unit"] = (
        "Unit "
        +
        timeline["unit_id"].astype(str)
    )

    fig_timeline = px.timeline(
        timeline,
        x_start="Start",
        x_end="Finish",
        y="Unit",
        color="stage",
        hover_data=[
            "waiting_time",
            "processing_time"
        ],
        title="Production Event Timeline"
    )

    fig_timeline.update_yaxes(
        autorange="reversed"
    )

    st.plotly_chart(
        fig_timeline,
        use_container_width=True
    )

else:

    st.info(
        "No production events available."
    )


# ============================================================
# EVENT LOG
# ============================================================

st.subheader("📋 Production Event Log")

st.dataframe(
    scenario_events.head(100).round(2),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD CSV
# ============================================================

csv_data = scenario_events.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="📥 Download Scenario Event Log",
    data=csv_data,
    file_name="production_twin_event_log.csv",
    mime="text/csv"
)


# ============================================================
# PROJECT CAPABILITIES
# ============================================================

st.divider()

st.subheader("🎯 LineLens Twin Capabilities")

cap1, cap2, cap3, cap4, cap5 = st.columns(5)


with cap1:

    st.markdown(
        "**🚦 Bottleneck Detection**\n\n"
        "Identifies production stages with high operational pressure."
    )


with cap2:

    st.markdown(
        "**⏱️ Delay Analysis**\n\n"
        "Measures waiting time and additional delay."
    )


with cap3:

    st.markdown(
        "**🔴 Downtime Propagation**\n\n"
        "Shows downstream effects of machine downtime."
    )


with cap4:

    st.markdown(
        "**📦 Throughput Analysis**\n\n"
        "Quantifies production output and throughput losses."
    )


with cap5:

    st.markdown(
        "**🔬 What-if Simulation**\n\n"
        "Tests operational changes before physical implementation."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "LineLens Twin | SI-02 Production Line Digital Twin & "
    "Bottleneck Intelligence"
)
def generate_recommendations(
    kpis,
    summary,
    changed_machine,
    new_process_time,
    baseline_times,
    new_capacity,
    baseline_capacity,
    downtime_machine,
    downtime_duration,
):
    """
    Generate operational recommendations based on
    digital-twin simulation results.
    """

    recommendations = []

    bottleneck = kpis.get(
        "bottleneck",
        "None"
    )

    # ---------------------------------------------------------
    # Find bottleneck information
    # ---------------------------------------------------------

    bottleneck_row = None

    if not summary.empty:

        rows = summary[
            summary["stage"] == bottleneck
        ]

        if not rows.empty:
            bottleneck_row = rows.iloc[0]

    # ---------------------------------------------------------
    # Recommendation 1:
    # High utilization
    # ---------------------------------------------------------

    if bottleneck_row is not None:

        utilization = float(
            bottleneck_row[
                "utilization_pct"
            ]
        )

        if utilization >= 90:

            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": (
                        f"Increase capacity at {bottleneck}"
                    ),
                    "reason": (
                        f"{bottleneck} has "
                        f"{utilization:.1f}% utilization."
                    ),
                }
            )

    # ---------------------------------------------------------
    # Recommendation 2:
    # High waiting time
    # ---------------------------------------------------------

    if bottleneck_row is not None:

        waiting = float(
            bottleneck_row[
                "avg_waiting_time_min"
            ]
        )

        if waiting >= 5:

            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": (
                        f"Reduce queue formation at {bottleneck}"
                    ),
                    "reason": (
                        f"Average waiting time is "
                        f"{waiting:.2f} minutes."
                    ),
                }
            )

    # ---------------------------------------------------------
    # Recommendation 3:
    # Processing time increased
    # ---------------------------------------------------------

    baseline_process_time = float(
        baseline_times[
            changed_machine
        ]
    )

    if new_process_time > baseline_process_time:

        increase = (
            (
                new_process_time
                -
                baseline_process_time
            )
            /
            baseline_process_time
        ) * 100

        recommendations.append(
            {
                "priority": "HIGH",
                "action": (
                    f"Reduce processing time at "
                    f"{changed_machine}"
                ),
                "reason": (
                    f"Processing time increased by "
                    f"{increase:.1f}% from the baseline."
                ),
            }
        )

    # ---------------------------------------------------------
    # Recommendation 4:
    # Additional capacity
    # ---------------------------------------------------------

    baseline_machine_capacity = int(
        baseline_capacity[
            changed_machine
        ]
    )

    if new_capacity > baseline_machine_capacity:

        recommendations.append(
            {
                "priority": "MEDIUM",
                "action": (
                    f"Evaluate the additional "
                    f"capacity at {changed_machine}"
                ),
                "reason": (
                    f"The scenario uses "
                    f"{new_capacity} parallel machines "
                    f"instead of "
                    f"{baseline_machine_capacity}."
                ),
            }
        )

    # ---------------------------------------------------------
    # Recommendation 5:
    # Downtime
    # ---------------------------------------------------------

    if (
        downtime_machine is not None
        and downtime_duration > 0
    ):

        recommendations.append(
            {
                "priority": "HIGH",
                "action": (
                    f"Reduce downtime risk at "
                    f"{downtime_machine}"
                ),
                "reason": (
                    f"The simulated downtime is "
                    f"{downtime_duration} minutes."
                ),
            }
        )

    # ---------------------------------------------------------
    # Recommendation 6:
    # Throughput loss
    # ---------------------------------------------------------

    throughput_loss = int(
        kpis.get(
            "throughput_loss",
            0
        )
    )

    if throughput_loss > 0:

        recommendations.append(
            {
                "priority": "HIGH",
                "action": (
                    "Investigate the cause of "
                    "throughput loss"
                ),
                "reason": (
                    f"The scenario loses approximately "
                    f"{throughput_loss} units compared "
                    f"with expected production."
                ),
            }
        )

    # ---------------------------------------------------------
    # Default recommendation
    # ---------------------------------------------------------

    if not recommendations:

        recommendations.append(
            {
                "priority": "LOW",
                "action": (
                    "Production condition is stable"
                ),
                "reason": (
                    "No major operational pressure "
                    "was detected in the simulated scenario."
                ),
            }
        )

    return recommendations
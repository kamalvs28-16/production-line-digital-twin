"""
LineLens Twin - Production Decision Support

This module analyzes simulation results and generates
rule-based operational recommendations.

The recommendation engine uses:
- Bottleneck utilization
- Waiting time
- Queue length
- Machine downtime
- Processing-time changes
- Machine-capacity changes

It does not use a trained machine-learning model.
"""


def generate_recommendations(
    kpis,
    summary,
    changed_machine,
    new_process_time,
    baseline_times,
    new_capacity,
    baseline_capacity,
    downtime_machine,
    downtime_duration
):
    """
    Generate production-line recommendations from simulation results.

    Parameters
    ----------
    kpis : dict
        KPI results from the production simulation.

    summary : pandas.DataFrame
        Stage-level simulation summary.

    changed_machine : str
        Machine/stage selected for the What-If scenario.

    new_process_time : float
        Processing time selected for the scenario.

    baseline_times : dict
        Original processing times for each stage.

    new_capacity : int
        Machine capacity selected for the scenario.

    baseline_capacity : dict
        Original machine capacity for each stage.

    downtime_machine : str or None
        Stage experiencing downtime.

    downtime_duration : float
        Duration of downtime in minutes.

    Returns
    -------
    list
        List of recommendation dictionaries containing:
        priority, action, and reason.
    """

    recommendations = []

    # =========================================================
    # 1. BASIC VALIDATION
    # =========================================================

    if kpis is None:
        kpis = {}

    if summary is None:
        return [{
            "priority": "LOW",
            "action": "Continue monitoring the production line.",
            "reason": "Stage-level simulation data is not available."
        }]

    # =========================================================
    # 2. GET BOTTLENECK
    # =========================================================

    bottleneck = kpis.get("bottleneck", "Unknown")

    # =========================================================
    # 3. BOTTLENECK ANALYSIS
    # =========================================================

    if bottleneck != "Unknown" and "stage" in summary.columns:

        bottleneck_rows = summary[
            summary["stage"] == bottleneck
        ]

        if not bottleneck_rows.empty:

            row = bottleneck_rows.iloc[0]

            # ---------------------------------------------
            # Get utilization
            # ---------------------------------------------

            utilization = float(
                row.get("utilization_pct", 0)
            )

            # ---------------------------------------------
            # Get waiting time
            # ---------------------------------------------

            waiting_time = float(
                row.get("avg_waiting_time_min", 0)
            )

            # ---------------------------------------------
            # Get queue length
            # ---------------------------------------------

            queue_length = float(
                row.get("avg_queue_length", 0)
            )

            # =================================================
            # 3A. HIGH UTILIZATION
            # =================================================

            if utilization >= 90:

                recommendations.append({
                    "priority": "HIGH",
                    "action": (
                        f"Consider increasing machine capacity at "
                        f"{bottleneck} or reducing its processing time."
                    ),
                    "reason": (
                        f"{bottleneck} is operating at very high "
                        f"resource utilization ({utilization:.1f}%). "
                        "This can restrict production flow."
                    )
                })

            elif utilization >= 80:

                recommendations.append({
                    "priority": "HIGH",
                    "action": (
                        f"Investigate capacity improvement at "
                        f"{bottleneck}."
                    ),
                    "reason": (
                        f"{bottleneck} has high resource utilization "
                        f"({utilization:.1f}%)."
                    )
                })

            # =================================================
            # 3B. WAITING TIME
            # =================================================

            if waiting_time >= 5:

                recommendations.append({
                    "priority": "HIGH",
                    "action": (
                        f"Investigate excessive waiting time at "
                        f"{bottleneck} and evaluate additional capacity."
                    ),
                    "reason": (
                        f"Average waiting time at {bottleneck} is "
                        f"{waiting_time:.2f} minutes."
                    )
                })

            elif waiting_time >= 1:

                recommendations.append({
                    "priority": "MEDIUM",
                    "action": (
                        f"Investigate queue formation at "
                        f"{bottleneck}."
                    ),
                    "reason": (
                        f"Products wait an average of "
                        f"{waiting_time:.2f} minutes at this stage."
                    )
                })

            # =================================================
            # 3C. QUEUE BUILDUP
            # =================================================

            if queue_length >= 5:

                recommendations.append({
                    "priority": "HIGH",
                    "action": (
                        f"Evaluate additional capacity or process "
                        f"optimization at {bottleneck}."
                    ),
                    "reason": (
                        f"The average queue length at {bottleneck} "
                        f"is {queue_length:.2f} units."
                    )
                })

            elif queue_length >= 2:

                recommendations.append({
                    "priority": "MEDIUM",
                    "action": (
                        f"Monitor queue buildup at {bottleneck}."
                    ),
                    "reason": (
                        f"The average queue length at {bottleneck} "
                        f"is {queue_length:.2f} units."
                    )
                })

    # =========================================================
    # 4. DOWNTIME ANALYSIS
    # =========================================================

    if downtime_machine and downtime_duration > 0:

        if downtime_duration >= 30:

            recommendations.append({
                "priority": "HIGH",
                "action": (
                    f"Review downtime mitigation for "
                    f"{downtime_machine}. Consider preventive "
                    "maintenance or backup capacity."
                ),
                "reason": (
                    f"The scenario introduces {downtime_duration:.0f} "
                    f"minutes of downtime at {downtime_machine}."
                )
            })

        else:

            recommendations.append({
                "priority": "MEDIUM",
                "action": (
                    f"Monitor the impact of downtime at "
                    f"{downtime_machine}."
                ),
                "reason": (
                    f"The scenario includes "
                    f"{downtime_duration:.0f} minutes of downtime."
                )
            })

    # =========================================================
    # 5. PROCESSING-TIME CHANGE
    # =========================================================

    if (
        changed_machine in baseline_times
        and new_process_time is not None
    ):

        original_time = float(
            baseline_times[changed_machine]
        )

        new_time = float(new_process_time)

        # ---------------------------------------------
        # Processing time increased
        # ---------------------------------------------

        if new_time > original_time:

            increase = new_time - original_time
            increase_pct = (
                increase / original_time * 100
                if original_time > 0
                else 0
            )

            priority = (
                "HIGH"
                if increase_pct >= 50
                else "MEDIUM"
            )

            recommendations.append({
                "priority": priority,
                "action": (
                    f"Investigate the increased processing time "
                    f"at {changed_machine}."
                ),
                "reason": (
                    f"Processing time increased from "
                    f"{original_time:.2f} to {new_time:.2f} minutes "
                    f"({increase_pct:.1f}% increase)."
                )
            })

        # ---------------------------------------------
        # Processing time decreased
        # ---------------------------------------------

        elif new_time < original_time:

            reduction = original_time - new_time
            reduction_pct = (
                reduction / original_time * 100
                if original_time > 0
                else 0
            )

            recommendations.append({
                "priority": "LOW",
                "action": (
                    f"Evaluate the process improvement at "
                    f"{changed_machine}."
                ),
                "reason": (
                    f"Processing time decreased from "
                    f"{original_time:.2f} to {new_time:.2f} minutes "
                    f"({reduction_pct:.1f}% reduction)."
                )
            })

    # =========================================================
    # 6. MACHINE CAPACITY CHANGE
    # =========================================================

    if (
        changed_machine in baseline_capacity
        and new_capacity is not None
    ):

        original_capacity = int(
            baseline_capacity[changed_machine]
        )

        current_capacity = int(new_capacity)

        # ---------------------------------------------
        # Capacity increased
        # ---------------------------------------------

        if current_capacity > original_capacity:

            recommendations.append({
                "priority": "LOW",
                "action": (
                    f"Evaluate the additional capacity at "
                    f"{changed_machine} using the What-If results."
                ),
                "reason": (
                    f"Machine capacity changed from "
                    f"{original_capacity} to {current_capacity}."
                )
            })

        # ---------------------------------------------
        # Capacity decreased
        # ---------------------------------------------

        elif current_capacity < original_capacity:

            recommendations.append({
                "priority": "HIGH",
                "action": (
                    f"Review the reduced capacity at "
                    f"{changed_machine}."
                ),
                "reason": (
                    f"Machine capacity decreased from "
                    f"{original_capacity} to {current_capacity}."
                )
            })

    # =========================================================
    # 7. THROUGHPUT CHECK
    # =========================================================

    throughput = float(
        kpis.get("throughput_per_hour", 0)
    )

    completed_units = int(
        kpis.get("completed_units", 0)
    )

    if throughput <= 0 or completed_units <= 0:

        recommendations.append({
            "priority": "HIGH",
            "action": (
                "Investigate the production flow because "
                "the simulation produced no completed output."
            ),
            "reason": (
                "The simulated completed-unit count or throughput "
                "is zero."
            )
        })

    # =========================================================
    # 8. TOTAL DOWNTIME CHECK
    # =========================================================

    total_downtime = float(
        kpis.get("total_downtime_min", 0)
    )

    if total_downtime > 0 and not downtime_machine:

        recommendations.append({
            "priority": "MEDIUM",
            "action": (
                "Investigate the reported downtime and identify "
                "the affected production stage."
            ),
            "reason": (
                f"The simulation reports {total_downtime:.1f} "
                "minutes of downtime."
            )
        })

    # =========================================================
    # 9. DEFAULT RECOMMENDATION
    # =========================================================

    if not recommendations:

        recommendations.append({
            "priority": "LOW",
            "action": (
                "Continue monitoring the production line "
                "and compare alternative scenarios."
            ),
            "reason": (
                "No major threshold-based production issue "
                "was detected in the current scenario."
            )
        })

    # =========================================================
    # 10. REMOVE DUPLICATE RECOMMENDATIONS
    # =========================================================

    unique_recommendations = []

    seen = set()

    for recommendation in recommendations:

        key = (
            recommendation["priority"],
            recommendation["action"],
            recommendation["reason"]
        )

        if key not in seen:

            seen.add(key)
            unique_recommendations.append(
                recommendation
            )

    # =========================================================
    # 11. PRIORITY ORDER
    # =========================================================

    priority_order = {
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    unique_recommendations.sort(
        key=lambda x: priority_order.get(
            x.get("priority", "LOW"),
            3
        )
    )

    return unique_recommendations
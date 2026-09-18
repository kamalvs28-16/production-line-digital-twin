import simpy
import numpy as np
import pandas as pd


def run_simulation(
    process_times,
    capacities,
    downtime_machine=None,
    downtime_start=120,
    downtime_duration=0,
    simulation_minutes=480,
    arrival_interval=1.8,
    seed=42,
):
    """
    Production Line Digital Twin Simulation

    Production flow:
        Cutting -> Drilling -> Assembly -> Inspection

    Returns:
        kpis, summary, events
    """

    rng = np.random.default_rng(seed)
    env = simpy.Environment()

    stages = list(process_times.keys())

    # ---------------------------------------------------------
    # MACHINE RESOURCES
    # ---------------------------------------------------------

    machines = {
        stage: simpy.Resource(
            env,
            capacity=max(1, int(capacities[stage]))
        )
        for stage in stages
    }

    # ---------------------------------------------------------
    # EVENT LOG
    # ---------------------------------------------------------

    event_log = []

    # ---------------------------------------------------------
    # MACHINE STATISTICS
    # ---------------------------------------------------------

    machine_stats = {
        stage: {
            "busy_time": 0.0,
            "units": 0,
            "queue_samples": []
        }
        for stage in stages
    }

    # ---------------------------------------------------------
    # DOWNTIME
    # ---------------------------------------------------------

    downtime_windows = {}

    if (
        downtime_machine in stages
        and downtime_duration > 0
    ):
        downtime_windows[downtime_machine] = (
            float(downtime_start),
            float(downtime_start + downtime_duration)
        )

    # ---------------------------------------------------------
    # DOWNTIME CHECK
    # ---------------------------------------------------------

    def machine_available_time(stage, current_time):

        if stage not in downtime_windows:
            return 0.0

        start, end = downtime_windows[stage]

        if start <= current_time < end:
            return end - current_time

        return 0.0

    # ---------------------------------------------------------
    # PRODUCT PROCESS
    # ---------------------------------------------------------

    def product(unit_id):

        for stage in stages:

            queue_enter = env.now

            # Current queue length
            machine_stats[stage]["queue_samples"].append(
                len(machines[stage].queue)
            )

            # Request machine
            with machines[stage].request() as request:

                yield request

                # Waiting time
                waiting_time = env.now - queue_enter

                # If machine is down, wait until it becomes available
                unavailable_for = machine_available_time(
                    stage,
                    env.now
                )

                if unavailable_for > 0:
                    yield env.timeout(unavailable_for)

                # Processing starts
                start_time = env.now

                base_time = float(process_times[stage])

                # 8% processing-time variability
                actual_time = max(
                    0.1,
                    rng.normal(
                        base_time,
                        base_time * 0.08
                    )
                )

                # Process the unit
                yield env.timeout(actual_time)

                # Processing ends
                end_time = env.now

                machine_stats[stage]["busy_time"] += actual_time
                machine_stats[stage]["units"] += 1

                event_log.append({
                    "unit_id": unit_id,
                    "stage": stage,
                    "queue_enter": queue_enter,
                    "start_time": start_time,
                    "end_time": end_time,
                    "waiting_time": waiting_time,
                    "processing_time": actual_time
                })

    # ---------------------------------------------------------
    # PRODUCT ARRIVAL SOURCE
    # ---------------------------------------------------------

    def source():

        unit_id = 1

        while True:

            env.process(
                product(unit_id)
            )

            unit_id += 1

            yield env.timeout(
                arrival_interval
            )

    # Start source
    env.process(source())

    # Run simulation
    env.run(
        until=simulation_minutes
    )

    # ---------------------------------------------------------
    # EVENT DATAFRAME
    # ---------------------------------------------------------

    events = pd.DataFrame(event_log)

    if events.empty:

        return (
            {},
            pd.DataFrame(),
            pd.DataFrame()
        )

    # ---------------------------------------------------------
    # COMPLETED UNITS
    # ---------------------------------------------------------

    final_stage = stages[-1]

    completed = events[
        events["stage"] == final_stage
    ]

    completed_units = int(
        completed["unit_id"].nunique()
    )

    # ---------------------------------------------------------
    # THROUGHPUT
    # ---------------------------------------------------------

    simulation_hours = simulation_minutes / 60

    throughput_per_hour = (
        completed_units / simulation_hours
    )

    # ---------------------------------------------------------
    # STAGE SUMMARY
    # ---------------------------------------------------------

    stage_summary = []

    for stage in stages:

        stage_events = events[
            events["stage"] == stage
        ]

        if stage_events.empty:

            avg_process_time = 0.0
            avg_waiting_time = 0.0

        else:

            avg_process_time = float(
                stage_events["processing_time"].mean()
            )

            avg_waiting_time = float(
                stage_events["waiting_time"].mean()
            )

        downtime_for_stage = (
            downtime_duration
            if stage == downtime_machine
            else 0
        )

        available_time = max(
            simulation_minutes - downtime_for_stage,
            0.1
        )

        capacity = max(
            1,
            int(capacities[stage])
        )

        utilization = (
            machine_stats[stage]["busy_time"]
            /
            (available_time * capacity)
            * 100
        )

        queue_samples = machine_stats[stage]["queue_samples"]

        avg_queue = (
            float(np.mean(queue_samples))
            if queue_samples
            else 0.0
        )

        stage_summary.append({

            "stage": stage,

            "capacity": capacity,

            "avg_process_time_min":
                round(avg_process_time, 3),

            "avg_waiting_time_min":
                round(avg_waiting_time, 3),

            "avg_queue_length":
                round(avg_queue, 3),

            "units_processed":
                machine_stats[stage]["units"],

            "utilization_pct":
                round(
                    min(utilization, 100),
                    2
                ),

            "downtime_min":
                downtime_for_stage
        })

    summary = pd.DataFrame(
        stage_summary
    )

    # ---------------------------------------------------------
    # BOTTLENECK
    # ---------------------------------------------------------

    if not summary.empty:

        bottleneck = (
            summary
            .sort_values(
                [
                    "utilization_pct",
                    "avg_waiting_time_min"
                ],
                ascending=False
            )
            .iloc[0]["stage"]
        )

    else:

        bottleneck = "N/A"

    # ---------------------------------------------------------
    # DOWNSTREAM WAIT
    # ---------------------------------------------------------

    downstream_wait = 0.0

    if (
        downtime_machine in stages
        and downtime_duration > 0
    ):

        downtime_index = stages.index(
            downtime_machine
        )

        downstream = stages[
            downtime_index + 1:
        ]

        if downstream:

            downstream_events = events[
                events["stage"].isin(downstream)
            ]

            if not downstream_events.empty:

                downstream_wait = float(
                    downstream_events[
                        "waiting_time"
                    ].mean()
                )

    # ---------------------------------------------------------
    # KPI RESULTS
    # ---------------------------------------------------------

    kpis = {

        "completed_units":
            completed_units,

        "throughput_per_hour":
            round(
                throughput_per_hour,
                2
            ),

        "bottleneck":
            bottleneck,

        "avg_downstream_wait_min":
            round(
                downstream_wait,
                2
            ),

        "total_downtime_min":
            float(downtime_duration)
    }

    return (
        kpis,
        summary,
        events
    )
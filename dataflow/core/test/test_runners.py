import asyncio
import logging
from typing import List, Optional, Tuple

import numpy as np
import pytest

import core.real_time as creatime
import core.real_time_example as cretiexa
import dataflow.core.builders_example as dtfcobuexa
import dataflow.core.result_bundle as dtfcorebun
import dataflow.core.runners as dtfcorrunn
import dataflow.core.visitors as dtfcorvisi
import helpers.datetime_ as hdateti
import helpers.hasyncio as hasynci
import helpers.unit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################


class TestRollingFitPredictDagRunner1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test the DagRunner using `ArmaReturnsBuilder`
        """
        dag_builder = dtfcobuexa.ArmaReturnsBuilder()
        config = dag_builder.get_config_template()
        dag_builder.get_dag(config)
        #
        dag_runner = dtfcorrunn.RollingFitPredictDagRunner(
            config=config,
            dag_builder=dag_builder,
            start="2010-01-04 09:30",
            end="2010-01-04 15:30",
            retraining_freq="H",
            retraining_lookback=4,
        )
        result_bundles = list(dag_runner.fit_predict())
        np.testing.assert_equal(len(result_bundles), 2)


# #############################################################################


class TestIncrementalDagRunner1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test the DagRunner using `ArmaReturnsBuilder`.
        """
        dag_builder = dtfcobuexa.ArmaReturnsBuilder()
        config = dag_builder.get_config_template()
        # Create DAG and generate fit state.
        dag = dag_builder.get_dag(config)
        nid = dag.get_unique_sink()
        dag.run_leq_node(nid, "fit")
        fit_state = dtfcorvisi.get_fit_state(dag)
        #
        dag_runner = dtfcorrunn.IncrementalDagRunner(
            config=config,
            dag_builder=dag_builder,
            start="2010-01-04 15:30",
            end="2010-01-04 15:45",
            freq="5T",
            fit_state=fit_state,
        )
        result_bundles = list(dag_runner.predict())
        self.assertEqual(len(result_bundles), 4)
        # Check that dataframe results of `col` do not retroactively change
        # over successive prediction steps (which would suggest future
        # peeking).
        col = "vwap_ret_0_vol_2_hat"
        for rb_i, rb_i_next in zip(result_bundles[:-1], result_bundles[1:]):
            srs_i = rb_i.result_df[col]
            srs_i_next = rb_i_next.result_df[col]
            self.assertTrue(srs_i.compare(srs_i_next[:-1]).empty)


# #############################################################################


class TestRealTimeDagRunner1(hunitest.TestCase):
    """
    - Create a naive DAG pipeline with a node generating random data and
      processing the data through a pass-through node
    - Create an event loop replaying time
    - Run the DAG with a `RealTimeDagRunner`
    - Check that the output is what is expected

    We simulate this in real and simulated time.
    """

    def test_simulated_replayed_time1(self) -> None:
        """
        Use simulated replayed time.
        """
        with hasynci.solipsism_context() as event_loop:
            events, result_bundles = self._helper(event_loop)
        self._check(events, result_bundles)

    # TODO(gp): Enable this but make it trigger more often.
    @pytest.mark.skip(reason="Too slow for real time")
    def test_replayed_time1(self) -> None:
        """
        Use replayed time.
        """
        event_loop = None
        events, result_bundles = self._helper(event_loop)
        # It's difficult to check the output of any real-time test, so we don't
        # verify the output.
        _ = events, result_bundles

    @staticmethod
    def _helper(
        event_loop: Optional[asyncio.AbstractEventLoop],
    ) -> Tuple[creatime.Events, List[dtfcorebun.ResultBundle]]:
        """
        Test `RealTimeDagRunner` using a simple DAG triggering every 2 seconds.
        """
        # Get a naive pipeline as DAG.
        dag_builder = dtfcobuexa.MvnReturnsBuilder()
        config = dag_builder.get_config_template()
        # Set up the event loop.
        sleep_interval_in_secs = 1.0
        execute_rt_loop_kwargs = (
            cretiexa.get_replayed_time_execute_rt_loop_kwargs(
                sleep_interval_in_secs, event_loop=event_loop
            )
        )
        dag_runner_kwargs = {
            "config": config,
            "dag_builder": dag_builder,
            "fit_state": None,
            "execute_rt_loop_kwargs": execute_rt_loop_kwargs,
            "dst_dir": None,
        }
        # Align on a second boundary.
        get_wall_clock_time = lambda: hdateti.get_current_time(
            tz="ET", event_loop=event_loop
        )
        grid_time_in_secs = 1
        creatime.align_on_time_grid(
            get_wall_clock_time, grid_time_in_secs, event_loop=event_loop
        )
        # Run.
        dag_runner = dtfcorrunn.RealTimeDagRunner(**dag_runner_kwargs)
        result_bundles = hasynci.run(dag_runner.predict(), event_loop=event_loop)
        events = dag_runner.events
        #
        _LOG.debug("events=\n%s", events)
        _LOG.debug("result_bundles=\n%s", result_bundles)
        return events, result_bundles

    # TODO(gp): Centralize this.
    def _check(
        self,
        events: creatime.Events,
        result_bundles: List[dtfcorebun.ResultBundle],
    ) -> None:
        # Check the events.
        actual = "\n".join(
            [
                event.to_str(
                    include_tenths_of_secs=False, include_wall_clock_time=False
                )
                for event in events
            ]
        )
        expected = r"""
        num_it=1 current_time='2010-01-04 09:30:00'
        num_it=2 current_time='2010-01-04 09:30:01'
        num_it=3 current_time='2010-01-04 09:30:02'"""
        self.assert_equal(actual, expected, dedent=True)
        # Check the result bundles.
        actual = []
        result_bundles_as_str = "\n".join(map(str, result_bundles))
        actual.append("result_bundles=\n%s" % result_bundles_as_str)
        actual = "\n".join(map(str, actual))
        self.check_string(actual)
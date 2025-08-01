import pytest
import logging
import random
from tests.common.fixtures.conn_graph_facts import conn_graph_facts, fanout_graph_facts, \
    fanout_graph_facts_multidut     # noqa: F401
from tests.common.snappi_tests.snappi_fixtures import snappi_api_serv_ip, snappi_api_serv_port, \
    get_snappi_ports_single_dut, snappi_testbed_config, \
    get_snappi_ports_multi_dut, is_snappi_multidut, snappi_port_selection, tgen_port_info, \
    snappi_api, snappi_dut_base_config, get_snappi_ports, get_snappi_ports_for_rdma, cleanup_config  # noqa: F401
from tests.common.snappi_tests.qos_fixtures import prio_dscp_map, \
    lossless_prio_list, disable_pfcwd                                                                # noqa: F401
from tests.snappi_tests.pfc.files.m2o_fluctuating_lossless_helper import run_m2o_fluctuating_lossless_test
from tests.common.snappi_tests.snappi_test_params import SnappiTestParams
from tests.snappi_tests.cisco.helper import disable_voq_watchdog                  # noqa: F401
logger = logging.getLogger(__name__)
pytestmark = [pytest.mark.topology('multidut-tgen', 'tgen')]


@pytest.fixture(autouse=True, scope='module')
def number_of_tx_rx_ports():
    yield (1, 2)


def test_m2o_fluctuating_lossless(snappi_api,                   # noqa: F811
                                  conn_graph_facts,             # noqa: F811
                                  fanout_graph_facts_multidut,  # noqa: F811
                                  duthosts,
                                  prio_dscp_map,                # noqa: F811
                                  lossless_prio_list,           # noqa: F811
                                  get_snappi_ports,             # noqa: F811
                                  tbinfo,                       # noqa: F811
                                  disable_pfcwd,                # noqa: F811
                                  tgen_port_info):              # noqa: F811

    """
    Run PFC Fluctuating Lossless Traffic Congestion with many to one traffic pattern

    Args:
        snappi_api (pytest fixture): SNAPPI session
        snappi_testbed_config (pytest fixture): testbed configuration information
        conn_graph_facts (pytest fixture): connection graph
        fanout_graph_facts_multidut (pytest fixture): fanout graph
        duthosts (pytest fixture): list of DUTs
        lossy_prio_list (pytest fixture): list of lossy priorities
        prio_dscp_map (pytest fixture): priority vs. DSCP map (key = priority)
        tbinfo (pytest fixture): fixture provides information about testbed
        get_snappi_ports (pytest fixture): gets snappi ports and connected DUT port info and returns as a list

    Brief Description:
        This test uses the m2o_fluctuating_lossless_helper.py file and generates 4 Background traffic and
        2 Test flow traffic. The background traffic will include four lossy traffic streams, with any priorities
        0..2 and 5..6, each having 20% bandwidth for a total of 80% of the port line rate. The test data traffic
        will include two lossless traffic flows, with the SONiC default lossless priorities of 3 and 4. Each of
        lossless traffic flows will be shaped to have line rate of 20% and 10%, so that there are periods where
        both lossless flows contribute a bandwidth of 30% (which should cause over-subscription on the egress port).
        The __gen_traffic() generates the flows. run_traffic() starts the flows and returns the flows stats.
        The verify_m2o_oversubscribtion_results() takes in the flows stats and verifies the loss criteria
        mentioned in the flag. Ex: 'loss': '10' means the flows tohave 10% loss, 'loss': '0' means there shouldn't
        be any loss

    Returns:
        N/A
    """
    testbed_config, port_config_list, snappi_ports = tgen_port_info

    all_prio_list = prio_dscp_map.keys()
    test_prio_list = lossless_prio_list
    pause_prio_list = test_prio_list
    bg_prio_list = random.sample([x for x in all_prio_list if x not in pause_prio_list], 4)
    logger.info('Selected two random lossy background priorities:{}'.format(bg_prio_list))

    snappi_extra_params = SnappiTestParams()
    snappi_extra_params.multi_dut_params.multi_dut_ports = snappi_ports

    try:
        run_m2o_fluctuating_lossless_test(
            api=snappi_api,
            testbed_config=testbed_config,
            port_config_list=port_config_list,
            conn_data=conn_graph_facts,
            fanout_data=fanout_graph_facts_multidut,
            dut_port=snappi_ports[0]['peer_port'],
            pause_prio_list=pause_prio_list,
            test_prio_list=test_prio_list,
            bg_prio_list=bg_prio_list,
            prio_dscp_map=prio_dscp_map,
            snappi_extra_params=snappi_extra_params
        )
    finally:
        cleanup_config(duthosts, snappi_ports)

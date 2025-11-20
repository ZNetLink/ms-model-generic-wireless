import miaosuan as ms
from miaosuan.engine.simobj import (
    SimObj,
)


def _get_channel_index(channel: SimObj) -> int:
    if hasattr(channel, "get_index"):
        return channel.get_index()
    return getattr(channel, "index", 0)

@ms.pipeline_stage("generic_wireless_closure")
def generic_wireless_closure(packet) -> None:
    # 获取该数据包的传输距离
    start_dist = ms.td_get(packet, ms.OPC_TDA_RA_START_DIST)
    end_dist = ms.td_get(packet, ms.OPC_TDA_RA_END_DIST)

    # 获取该数据包的最远传输距离
    transmit_dist = ms.pk_nfd_get_float64(packet, "Transmit Distance")

    # 若数据包传输距离超过门限，则表示传输失败
    if transmit_dist < start_dist or transmit_dist < end_dist:
        ms.td_set(packet, ms.OPC_TDA_RA_CLOSURE, False)
        return

    # 否则，表示传输成功
    ms.td_set(packet, ms.OPC_TDA_RA_CLOSURE, True)


@ms.pipeline_stage("generic_wireless_ecc")
def generic_wireless_ecc(packet) -> None:
    # 获取信道闭合情况
    accept = ms.td_get(packet, ms.OPC_TDA_RA_CLOSURE)
    # 直接根据信道闭合情况设置数据包接受情况
    ms.td_set(packet, ms.OPC_TDA_RA_PK_ACCEPT, accept)


@ms.pipeline_stage("generic_wireless_rxgroup")
def generic_wireless_rx_group(tx_channel: SimObj, rx_channel: SimObj) -> bool:
    # 如果收信机和发信机处于同一节点内，则不为配对收发信机
    # note: 这里与OP不同，channel -> module -> node，只需要两次parent获取到节点，OP需要3次
    tx_parent = tx_channel.get_parent()
    rx_parent = rx_channel.get_parent()
    tx_node = tx_parent.get_parent()
    rx_node = rx_parent.get_parent()

    if tx_node == rx_node:
        return False

    # 获取发信机信道的参数
    tx_index = _get_channel_index(tx_channel)
    rx_index = _get_channel_index(rx_channel)

    tx_base_freq = tx_parent.get_attr_double(f"channel[{tx_index}].min frequency")
    rx_base_freq = rx_parent.get_attr_double(f"channel[{rx_index}].min frequency")

    # 如果发信机或收信机的频段为0.01，则表示其被关闭，不配对
    if tx_base_freq == 0.01 or rx_base_freq == 0.01:
        return False

    # 获取收发信机详细属性
    tx_bandwidth = tx_parent.get_attr_double(f"channel[{tx_index}].bandwidth")
    rx_bandwidth = rx_parent.get_attr_double(f"channel[{rx_index}].bandwidth")
    tx_data_rate = tx_parent.get_attr_double(f"channel[{tx_index}].data rate")
    rx_data_rate = rx_parent.get_attr_double(f"channel[{rx_index}].data rate")
    tx_code = tx_parent.get_attr_double(f"channel[{tx_index}].spreading code")
    rx_code = rx_parent.get_attr_double(f"channel[{rx_index}].spreading code")

    # 只有频率，带宽，数据速率，扩频码一致的情况下，才认为可配对
    if (
        tx_base_freq != rx_base_freq
        or tx_bandwidth != rx_bandwidth
        or tx_data_rate != rx_data_rate
        or tx_code != rx_code
    ):
        return False

    return True


@ms.pipeline_stage("generic_wireless_txdel")
def generic_wireless_txdel(packet) -> None:
    tx_data_rate = ms.td_get(packet, ms.OPC_TDA_RA_TX_DRATE)
    pk_len = ms.pk_total_size_get(packet)

    tx_delay = float(pk_len) / float(tx_data_rate)

    ms.td_set(packet, ms.OPC_TDA_RA_TX_DELAY, tx_delay)

    # todo: dump routes

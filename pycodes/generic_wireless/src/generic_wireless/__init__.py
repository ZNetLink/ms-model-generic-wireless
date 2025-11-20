import logging
from typing import Optional

import miaosuan as ms
from miaosuan.engine.engine import INTRPT_TYPE_SELF, INTRPT_TYPE_STRM, Stream
from miaosuan.engine.radio_transceivers import radio_tx_channel_rx_group_compute
from miaosuan.engine.simobj import (
    OBJ_TYPE_PROCESSOR,
    OBJ_TYPE_QUEUE,
    OBJ_TYPE_RA_RX,
    OBJ_TYPE_RA_TX,
    OBJ_TYPE_RA_TX_CH,
    SimObj,
)
from miaosuan.mms.auto_addr import aa_address_handle_get, aa_address_resolve
from miaosuan.mms.process_registry import AttrType, pr_attr_set, pr_register

from . import pipeline

logger = logging.getLogger(__name__)

EPSILON = 1e-9
BROADCAST_ADDRESS = 0xFFFF_FFFFFFFF

@ms.process_model("generic_wireless")
class GenericWirelessProcess:
    def __init__(self) -> None:
        self.my_module: Optional[SimObj] = None
        self.my_module_name: str = ""
        self.my_node: Optional[SimObj] = None
        self.my_node_name: str = ""
        self.my_pro_handle = None
        self.proc_model_name: str = "generic_wireless"
        self.addr_handle = None
        self.my_mac_address: int = -1
        self.llc_ici = None
        self.rx_obj: Optional[SimObj] = None
        self.tx_obj: Optional[SimObj] = None
        self.my_arp_obj: Optional[SimObj] = None
        self.own_pr_handle = None

        self.from_arp_stream: int = -1
        self.to_arp_stream: int = -1
        self.tx_out_stream: int = -1
        self.rx_in_stream: int = -1

        self.working_status: bool = True
        self.data_rate: float = 0.0
        self.base_freq: float = 0.0
        self.bandwidth: float = 0.0
        self.modulation: str = ""
        self.transmit_distance: float = 0.0
        self.transmit_power: float = 0.0
        self.receiver_sensitivity: float = 0.0
        self.buffer_size: int = 0
        self.max_receive_lifetime: float = 0.0



    @ms.state_enter("Init", begin=True)
    def enter_init(self) -> None:
        self._sv_init()
        self._transceiver_init()
        ms.intrpt_schedule_self(ms.sim_time(), 0)

    @ms.state_enter("Register")
    def enter_register(self) -> None:
        if self.addr_handle is None or self.my_module is None:
            raise RuntimeError("GenericWirelessProcess: address handle not initialized")

        # 获取自动分配的MAC地址
        self.my_mac_address = aa_address_resolve(self.addr_handle, self.my_module, self.my_mac_address)

        if self.my_node is None or self.my_pro_handle is None:
            raise RuntimeError("GenericWirelessProcess: missing node or process context during registration")

        handle = pr_register(
            self.my_node.get_id(),
            self.my_module.get_id(),
            self.my_pro_handle,
            self.proc_model_name,
        )

        self.own_pr_handle = handle

        pr_attr_set(handle, "protocol", AttrType.STRING, "mac")
        pr_attr_set(handle, "mac_type", AttrType.STRING, "tdma")
        pr_attr_set(handle, "address", AttrType.INT64, self.my_mac_address)
        pr_attr_set(handle, "module objid", AttrType.OBJ_ID, self.my_module.get_id())
        pr_attr_set(handle, "node objid", AttrType.OBJ_ID, self.my_node.get_id())
        pr_attr_set(handle, "auto address handle", AttrType.POINTER, self.addr_handle)
        pr_attr_set(handle, "node name", AttrType.STRING, self.my_node_name)
        if self.tx_obj is None or self.rx_obj is None:
            raise RuntimeError("GenericWirelessProcess: transceiver not initialized before registration")
        pr_attr_set(handle, "tx_objid", AttrType.OBJ_ID, self.tx_obj.get_id())
        pr_attr_set(handle, "rx_objid", AttrType.OBJ_ID, self.rx_obj.get_id())
        pr_attr_set(handle, "domain_id", AttrType.NUMBER, self.base_freq)

        ms.intrpt_schedule_self(ms.sim_time() + EPSILON, 0)

    @ms.state_enter("Obtain")
    def enter_obtain(self) -> None:
        if self.my_module is None or self.own_pr_handle is None:
            raise RuntimeError("GenericWirelessProcess: module or process handle not initialized")

        # 获取自动分配的MAC地址
        self.my_mac_address = self.my_module.get_attr_int("Address")

        pr_attr_set(self.own_pr_handle, "address", AttrType.INT64, self.my_mac_address)
        pr_attr_set(self.own_pr_handle, "ratx_objid", AttrType.OBJ_ID, self.tx_obj.get_id())
        pr_attr_set(self.own_pr_handle, "rarx_objid", AttrType.OBJ_ID, self.rx_obj.get_id())

        ms.intrpt_schedule_self(ms.sim_time() + EPSILON, 0)

    @ms.state_enter("RefreshRx")
    def enter_refresh_rx(self) -> None:
        if self.tx_obj is None:
            raise RuntimeError("GenericWirelessProcess: transmitter object missing during refresh")

        # 刷新设置了工作频段和工作频宽的无线收发信机组
        tx_channel = ms.topo_child(self.tx_obj, OBJ_TYPE_RA_TX_CH, 0)
        radio_tx_channel_rx_group_compute(tx_channel, None)

        ms.intrpt_schedule_self(ms.sim_time(), 0)

    @ms.state_enter("Idle")
    def enter_idle(self) -> None:
        pass

    @ms.state_enter("Disabled")
    def enter_disabled(self) -> None:
        pass

    @ms.transition("Init", "Register")
    def init_to_register(self) -> bool:
        return self.working_status

    @ms.transition("Init", "Disabled")
    def init_to_disabled(self) -> bool:
        return not self.working_status

    @ms.transition("Register", "Obtain")
    def register_to_obtain(self) -> bool:
        return True

    @ms.transition("Obtain", "RefreshRx")
    def obtain_to_refresh_rx(self) -> bool:
        return True

    @ms.transition("RefreshRx", "Idle")
    def refresh_rx_to_idle(self) -> bool:
        return True

    @ms.transition("Idle", "Idle")
    def idle_to_idle(self) -> bool:
        return True

    @ms.transition("Disabled", "Disabled")
    def disabled_to_disabled(self) -> bool:
        return True

    @ms.state_exit("Idle")
    def exit_idle(self) -> None:
        intrpt_type = ms.intrpt_type()
        if intrpt_type == INTRPT_TYPE_SELF:
            code = ms.intrpt_code()
            # 更新工作状态
            if code == 1:
                self.working_status = True
            elif code == 0:
                self.working_status = False
        elif intrpt_type == INTRPT_TYPE_STRM and ms.intrpt_strm() == self.from_arp_stream:
            # 收到来自上层的数据包
            self._process_higher_pkt()
        elif intrpt_type == INTRPT_TYPE_STRM and ms.intrpt_strm() == self.rx_in_stream:
            # 获取来自ARP的MAC地址
            self._process_lower_pkt()

    @ms.state_exit("Disabled")
    def exit_disabled(self) -> None:
        # 如果处于禁用状态，则销毁所有收到的数据包
        if ms.intrpt_type() == INTRPT_TYPE_STRM:
            print(
                f"GenericWirelessProcess: {self.my_module_name} is in disabled state, destroying all received packets"
            )
            packet = ms.pk_get(ms.intrpt_strm())
            ms.pk_destroy(packet)

    def _sv_init(self) -> None:
        self.my_module = ms.self_obj()
        if not isinstance(self.my_module, SimObj):
            raise RuntimeError("GenericWirelessProcess: missing module context")
        self.my_module_name = self.my_module.get_attr_string("name")
        self.my_node = ms.topo_parent(self.my_module)
        if not isinstance(self.my_node, SimObj):
            raise RuntimeError("GenericWirelessProcess: module has no parent node")
        self.my_node_name = self.my_node.get_attr_string("name")
        self.my_pro_handle = ms.pro_self()
        self.proc_model_name = self.my_module.get_attr_string("process model")

        self.addr_handle = aa_address_handle_get("MAC Address", "Address")
        self.llc_ici = ms.ici_create("generic_wireless_mac_ici")
        self.my_mac_address = self.my_module.get_attr_int("Address")

        self.working_status = self.my_module.get_attr_bool("电台工作参数.工作状态")
        self.data_rate = self.my_module.get_attr_double("电台工作参数.数据速率") * 1000  # kbps to bps
        self.base_freq = self.my_module.get_attr_double("电台工作参数.工作频段")
        self.bandwidth = self.my_module.get_attr_double("电台工作参数.工作频宽")
        self.modulation = self.my_module.get_attr_string("电台工作参数.调制解调方案")
        self.transmit_distance = self.my_module.get_attr_double("电台工作参数.最大传输距离") * 1000  # km to m
        self.transmit_power = self.my_module.get_attr_double("电台工作参数.传输功率")
        self.receiver_sensitivity = self.my_module.get_attr_double("电台工作参数.接收灵敏度")
        self.buffer_size = self.my_module.get_attr_int("电台工作参数.缓存大小")
        self.max_receive_lifetime = self.my_module.get_attr_double("电台工作参数.分片生存时间")

        # 获取失效恢复状态的配置项数量，然后循环获取
        recover_config_cnt = self.my_module.get_attr_array_count("电台工作参数.失效/恢复状态")
        for index in range(recover_config_cnt):
            time_point = self.my_module.get_attr_double(f"电台工作参数.失效/恢复状态[{index}].时间")
            status = self.my_module.get_attr_int(f"电台工作参数.失效/恢复状态[{index}].状态")
            ms.intrpt_schedule_self(time_point, status)

    def _transceiver_init(self) -> None:
        if self.my_module is None:
            raise RuntimeError("GenericWirelessProcess: module not initialized")

        tx_obj: Optional[SimObj] = None
        rx_obj: Optional[SimObj] = None
        upper_layer_obj: Optional[SimObj] = None
        tx_cnt = rx_cnt = upper_layer_cnt = 0

        out_streams = ms.get_out_streams() or {}
        for stream in out_streams.values():
            if not isinstance(stream, Stream):
                continue
            peer = stream.dst
            if peer is None:
                continue
            obj_type = peer.get_obj_type()
            if obj_type == OBJ_TYPE_RA_TX:
                tx_cnt += 1
                tx_obj = peer
                self.tx_out_stream = stream.src_index
            elif obj_type in (OBJ_TYPE_PROCESSOR, OBJ_TYPE_QUEUE):
                upper_layer_cnt += 1
                upper_layer_obj = peer
                self.to_arp_stream = stream.src_index
            else:
                logger.warning("Unexpected connected module: %s", peer.get_id())

        if upper_layer_cnt != 1 or upper_layer_obj is None:
            logger.warning("GenericWirelessProcess: upperLayerCnt != 1, upperLayerCnt = %d", upper_layer_cnt)
            raise RuntimeError("GenericWirelessProcess: upperLayerCnt != 1")

        in_streams = ms.get_in_streams() or {}
        for stream in in_streams.values():
            if not isinstance(stream, Stream):
                continue
            peer = stream.src
            if peer is None:
                continue
            obj_type = peer.get_obj_type()
            if obj_type == OBJ_TYPE_RA_RX:
                rx_cnt += 1
                rx_obj = peer
                self.rx_in_stream = stream.dst_index
            elif obj_type in (OBJ_TYPE_PROCESSOR, OBJ_TYPE_QUEUE):
                if peer is not upper_layer_obj:
                    logger.warning(
                        "GenericWirelessProcess: upperLayerCnt != 1, upperLayerCnt = %d", upper_layer_cnt
                    )
                    raise RuntimeError("GenericWirelessProcess: upperLayerCnt != 1")
                self.from_arp_stream = stream.dst_index
                self.my_arp_obj = peer
            else:
                logger.warning("Unexpected connected module: %s", peer.get_id())

        if tx_cnt != 1 or tx_obj is None:
            logger.warning(
                "GenericWirelessProcess: %s does not have exactly one transmitter", self.my_module_name
            )
            raise RuntimeError("GenericWirelessProcess does not have exactly one transmitter: " + self.my_module_name)
        if rx_cnt != 1 or rx_obj is None:
            logger.warning(
                "GenericWirelessProcess: %s does not have exactly one receiver", self.my_module_name
            )
            raise RuntimeError("GenericWirelessProcess does not have exactly one receiver: " + self.my_module_name)

        tx_channels = tx_obj.get_attr_array_count("channel")
        if tx_channels != 1:
            logger.warning(
                "GenericWirelessProcess: %s does not have exactly one tx channel", self.my_module_name
            )
            raise RuntimeError("GenericWirelessProcess does not have exactly one tx channel: " + self.my_module_name)
        rx_channels = rx_obj.get_attr_array_count("channel")
        if rx_channels != 1:
            logger.warning(
                "GenericWirelessProcess: %s does not have exactly one rx channel", self.my_module_name
            )
            raise RuntimeError("GenericWirelessProcess does not have exactly one rx channel: " + self.my_module_name)

        self.tx_obj = tx_obj
        self.rx_obj = rx_obj

        tx_obj.set_attr_double("channel[0].power", self.transmit_power)
        tx_obj.set_attr_double("channel[0].data rate", self.data_rate)
        tx_obj.set_attr_double("channel[0].bandwidth", self.bandwidth)
        tx_obj.set_attr_double("channel[0].min frequency", self.base_freq)
        tx_obj.set_attr_int("channel[0].pk capacity", self.buffer_size)

        rx_obj.set_attr_double("channel[0].data rate", self.data_rate)
        rx_obj.set_attr_double("channel[0].bandwidth", self.bandwidth)
        rx_obj.set_attr_double("channel[0].min frequency", self.base_freq)

        # 判断工作状态，如果不是工作状态，则设置工作频率为0.01,后续rxgroup管道模型将进一步处理
        if not self.working_status:
            tx_obj.set_attr_double("channel[0].min frequency", 0.01)
            rx_obj.set_attr_double("channel[0].min frequency", 0.01)

    def _process_higher_pkt(self) -> None:
        # 获取上层数据包指针
        ip_pkt = ms.pk_get(ms.intrpt_strm())

        # 判断工作状态，如果为“关闭”，则直接销毁IP包
        if not self.working_status:
            ms.pk_destroy(ip_pkt)
            return

        # 获取数据包大小
        # pkt_size = ms.pk_total_size_get(ip_pkt)

        # 获取ICI指针和其承载的信息
        arp_ici = ms.intrpt_ici()
        dest_addr = arp_ici.get_int("dest_addr")
        protocol_type = arp_ici.get_int("protocol_type")

        # todo: 我觉得这个逻辑有点问题，不应该在这里打IP包的时间戳吧
        # 将IP数据包进行MAC封装
        mac_pkt = self._encap_mac_packet(ip_pkt, int(dest_addr), int(protocol_type))

        # todo: 记录统计量

        # 将MAC层数据包发送到tx发信机
        ms.pk_send(mac_pkt, self.tx_out_stream)

    def _encap_mac_packet(self, ip_pkt, dest_addr: int, protocol_type: int):
        mac_pkt = ms.pk_create_fmt("generic_wireless_mac")

        ms.pk_nfd_set_int(mac_pkt, "source address", self.my_mac_address)
        ms.pk_nfd_set_int(mac_pkt, "dest address", dest_addr)
        ms.pk_nfd_set_int(mac_pkt, "protocol type", protocol_type)
        ms.pk_nfd_set_string(mac_pkt, "Modulation Index", self.modulation)
        ms.pk_nfd_set_float64(mac_pkt, "Transmit Distance", float(self.transmit_distance))
        ms.pk_nfd_set_packet(mac_pkt, "data", ip_pkt)

        ms.pk_stamp(mac_pkt)

        return mac_pkt

    def _process_lower_pkt(self) -> None:
        mac_pkt = ms.pk_get(ms.intrpt_strm())
        # 判断工作状态，如果为“关闭”，则直接销毁mac包
        if not self.working_status:
            ms.pk_destroy(mac_pkt)
            return

        # todo: 记录统计量
        # fmt.Printf("GenericWirelessProcess: 收到MAC数据包，延迟为%f\\n", ms.sim_time() - ms.pk_stamp_time_get(mac_pkt))

        # 获取mac包目的地址
        dest_address = ms.pk_nfd_get_int(mac_pkt, "dest address")
        # 如果该数据包目的地址不为本节点和广播地址，则直接销毁
        if dest_address != self.my_mac_address and dest_address != BROADCAST_ADDRESS:
            ms.pk_destroy(mac_pkt)
            return

        # 提取数据包的字段信息
        source_address = ms.pk_nfd_get_int(mac_pkt, "source address")
        protocol_type = ms.pk_nfd_get_int(mac_pkt, "protocol type")
        ip_pkt = ms.pk_nfd_get_packet(mac_pkt, "data")

        # 解出IP包并向上层发送
        self._send_ip_pkt_to_upper(ip_pkt, int(source_address), int(dest_address), int(protocol_type))

        # 销毁收到的MAC数据包
        ms.pk_destroy(mac_pkt)

    def _send_ip_pkt_to_upper(self, ip_pkt, source_address: int, dest_address: int, protocol_type: int) -> None:
        # todo: 记录吞吐量信息

        # todo: 记录MAC层数据包队列时延
        # e2e_delay = ms.sim_time() - ms.pk_stamp_time_get(ip_pkt)

        # 设置与ARP关联的ICI属性
        self.llc_ici.set_int("src_addr", source_address)
        self.llc_ici.set_int("dest_addr", dest_address)
        self.llc_ici.set_int("protocol_type", protocol_type)

        # 将该IP报文发往上层
        ms.ici_install(self.llc_ici)
        ms.pk_send(ip_pkt, self.to_arp_stream)
        ms.ici_install(None)


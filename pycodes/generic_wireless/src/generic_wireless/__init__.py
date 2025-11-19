import miaosuan as ms

from .model import GenericWirelessProcess
from .pipelines import (
    generic_wireless_closure,
    generic_wireless_ecc,
    generic_wireless_rx_group,
    generic_wireless_txdel,
)


ms.register_process_model("generic_wireless", lambda: GenericWirelessProcess())
ms.register_pipeline_stage_model("generic_wireless_closure", generic_wireless_closure)
ms.register_pipeline_stage_model("generic_wireless_ecc", generic_wireless_ecc)
ms.register_pipeline_stage_model("generic_wireless_rxgroup", generic_wireless_rx_group)
ms.register_pipeline_stage_model("generic_wireless_txdel", generic_wireless_txdel)

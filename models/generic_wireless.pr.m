{
  "interface": {
    "begsim_intrpt": true,
    "priority": 0
  },
  "attributes": [
    {
      "name": "Address",
      "label": "MAC地址",
      "type": "int",
      "desc": "",
      "unit": "",
      "validator": "",
      "defaultValue": -2,
      "symbolMap": [
        {
          "key": "Auto Assigned",
          "value": -2
        }
      ],
      "allowOtherValues": true
    },
    {
      "name": "电台工作参数",
      "label": "电台工作参数",
      "type": "object",
      "desc": "",
      "unit": "",
      "validator": "",
      "defaultValue": {},
      "symbolMap": [],
      "allowOtherValues": true,
      "children": [
        {
          "name": "工作状态",
          "label": "工作状态",
          "type": "bool",
          "desc": "",
          "unit": "",
          "validator": "",
          "defaultValue": false,
          "symbolMap": [
            {
              "value": false,
              "label": "关闭"
            },
            {
              "value": true,
              "label": "工作"
            }
          ],
          "allowOtherValues": false
        },
        {
          "name": "数据速率",
          "label": "数据速率",
          "type": "float",
          "unit": "kbps",
          "validator": "",
          "defaultValue": 38.4,
          "symbolMap": [
          ],
          "allowOtherValues": false
        },
        {
          "name": "工作频段",
          "label": "工作频段",
          "type": "float",
          "unit": "MHz",
          "validator": "",
          "defaultValue": 30.0,
          "symbolMap": [
          ],
          "allowOtherValues": true
        },
        {
          "name": "工作频宽",
          "label": "工作频宽",
          "type": "float",
          "unit": "kHz",
          "validator": "",
          "defaultValue": 100.0,
          "symbolMap": [
          ],
          "allowOtherValues": true
        },
        {
          "name": "调制解调方案",
          "label": "调制解调方案",
          "type": "string",
          "desc": "调制解调方案",
          "unit": "",
          "validator": "",
          "defaultValue": "BPSK",
          "symbolMap": [
            {
              "value": "BPSK",
              "label": "BPSK"
            },
            {
              "value": "QPSK",
              "label": "QPSK"
            },
            {
              "value": "16QAM",
              "label": "16QAM"
            },
            {
              "value": "64QAM",
              "label": "64QAM"
            }
          ],
          "allowOtherValues": false
        },
        {
          "name": "最大传输距离",
          "label": "最大传输距离",
          "type": "float",
          "unit": "公里",
          "validator": "",
          "defaultValue": 999999999.0,
          "symbolMap": [
            {
              "value": 999999999.0,
              "label": "无限制"
            }
          ],
          "allowOtherValues": true
        },
        {
          "name": "传输功率",
          "label": "传输功率",
          "type": "float",
          "unit": "瓦特",
          "validator": "",
          "defaultValue": 30.0,
          "symbolMap": [],
          "allowOtherValues": true
        },
        {
          "name": "接收灵敏度",
          "label": "接收灵敏度",
          "type": "float",
          "unit": "dBm",
          "validator": "",
          "defaultValue": -100.0,
          "symbolMap": [],
          "allowOtherValues": true
        },
        {
          "name": "缓存大小",
          "label": "缓存大小",
          "type": "int",
          "unit": "包",
          "validator": "",
          "defaultValue": 1000,
          "symbolMap": [],
          "allowOtherValues": true
        },
        {
          "name": "分片生存时间",
          "label": "分片生存时间",
          "type": "float",
          "unit": "秒",
          "validator": "",
          "defaultValue": 20.0,
          "symbolMap": [],
          "allowOtherValues": true
        },
        {
          "name": "失效/恢复状态",
          "label": "失效/恢复状态",
          "type": "array",
          "desc": "失效/恢复状态",
          "unit": "",
          "validator": "",
          "defaultValue": [],
          "symbolMap": [],
          "allowOtherValues": true,
          "children": [
            {
              "name": "时间",
              "label": "时间",
              "type": "float",
              "unit": "秒",
              "validator": "",
              "defaultValue": 0.0,
              "symbolMap": [],
              "allowOtherValues": true
            },
            {
              "name": "状态",
              "label": "状态",
              "type": "int",
              "desc": "",
              "unit": "",
              "validator": "",
              "defaultValue": 0,
              "symbolMap": [
                {
                  "value": 0,
                  "label": "失效"
                },
                {
                  "value": 1,
                  "label": "恢复"
                }
              ],
              "allowOtherValues": false
            }
          ]
        }
      ]
    }
  ]
}
#!/bin/bash

# 检查jq是否已经安装
if ! command -v jq &> /dev/null
then
    echo "jq 没有安装，正在安装..."
    sudo apt update
    sudo apt install -y jq
else
    echo "jq 已经安装"
fi

# 定义文件路径
file2="/etc/sing-box/conf/02_route.json"

# 定义要添加的JSON对象
json_obj2='{
    "route":{
        "rule_set":[
            {
                "tag":"geosite-openai",
                "type":"remote",
                "format":"binary",
                "url":"https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-openai.srs"
            },
            {
                "tag":"geosite-disney",
                "type":"remote",
                "format":"binary",
                "url":"https://raw.githubusercontent.com/SagerNet/sing-geosite/rule-set/geosite-disney.srs"
            }
        ],
        "rules":[
            {
                "domain":"api.openai.com",
                "outbound":"direct"
            },
            {
                "rule_set":"geosite-openai",
                "outbound":"direct"
            },
            {
                "rule_set":"geosite-disney",
                "outbound":"direct"
            }
        ]
    }
}'

# 获取当前的日期和时间
datetime=$(date +%Y%m%d%H%M%S)

# 检查文件是否存在并创建备份
if [ ! -f "$file2" ]; then
    echo "文件 $file2 不存在"
    exit 1
fi

# 创建备份
cp $file2 $file2.bak.$datetime
echo "已成功创建备份 $file2.bak.$datetime"

# 清空02_route.json文件并添加新的JSON对象
echo "$json_obj2" > $file2
echo "已成功修改 $file2 文件"

# 重启sing-box服务
echo "即将重启sing-box服务"
sudo systemctl restart sing-box

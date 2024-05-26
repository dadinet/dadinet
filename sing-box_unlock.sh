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
file1="/etc/sing-box/conf/01_outbounds.json"
file2="/etc/sing-box/conf/02_route.json"

# 定义要添加的JSON对象
json_obj1='{
    "type": "socks",
    "tag": "local-warp",
    "server": "127.0.0.1",
    "server_port": 40000
}'

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
                "outbound":"local-warp"
            },
            {
                "rule_set":"geosite-openai",
                "outbound":"local-warp"
            },
            {
                "rule_set":"geosite-disney",
                "outbound":"local-warp"
            }
        ]
    }
}'

# 获取当前的日期和时间
datetime=$(date +%Y%m%d%H%M%S)

# 检查文件是否存在并创建备份
for file in $file1 $file2
do
    if [ ! -f "$file" ]; then
        echo "文件 $file 不存在"
        exit 1
    fi

    # 创建备份
    cp $file $file.bak.$datetime
    echo "已成功创建备份 $file.bak.$datetime"
done

# 检查是否已经存在local-warp出站规则
if jq -e '.outbounds[] | select(.tag=="local-warp")' $file1 > /dev/null; then
    echo "local-warp出站规则已经存在，退出修改"
else
    # 将新的出站规则添加到outbounds数组的开始位置
    jq --argjson obj "$json_obj1" '.outbounds = [$obj] + .outbounds' $file1 > temp.json && mv temp.json $file1
    echo "已成功添加local-warp出站规则"

    # 清空02_route.json文件并添加新的JSON对象
    echo "$json_obj2" > $file2
    echo "已成功修改 $file2 文件"
fi

# 重启sing-box服务
echo "即将重启sing-box服务"
sudo systemctl restart sing-box


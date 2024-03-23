import os
import tarfile
import time

# 定时 0 */6 * * *

# 设置要备份的目录
dirs_to_backup = ["/Qb/config/qBittorrent",
                  "/Tr/config/resume",
                  "/Tr/config/torrents"]

# 设置备份文件的目录
backup_dir = "/disk4/Qb_Tr种子备份/"

# 设置文件的过期天数
days_old = 2

# 获取当前时间作为备份文件的名称
backup_name = time.strftime("%Y%m%d%H%M%S")

# 创建备份文件的完整路径
backup_file = os.path.join(backup_dir, backup_name + ".tar.gz")

# 创建tar文件
with tarfile.open(backup_file, "w:gz") as tar:
    for dir in dirs_to_backup:
        tar.add(dir)

print("备份完成，文件已保存为：", backup_file)

# 获取当前时间
now = time.time()

# 遍历备份目录中的所有文件
for filename in os.listdir(backup_dir):
    file = os.path.join(backup_dir, filename)
    
    # 如果文件是普通文件并且文件的最后修改时间早于2天前
    if os.path.isfile(file) and os.path.getmtime(file) < now - days_old * 86400:
        # 删除文件
        os.remove(file)
        print("已删除文件：", file)

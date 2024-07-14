# coding: utf-8
import json
import os
import shutil
from datetime import datetime

import re
import log
from app.helper import ChromeHelper, SiteHelper, DbHelper
from app.message import Message
from app.sites.site_limiter import SiteRateLimiter
from app.utils import RequestUtils, StringUtils, PathUtils, ExceptionUtils
from app.utils.commons import singleton
from config import Config, RMT_SUBEXT
from urllib import parse

class MTeamApi:
    # 测试站点连通性
    @staticmethod
    def test_mt_connection(site_info):
        # 计时
        start_time = datetime.now()
        site_url = "https://api.m-team.cc/api/system/hello"
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": site_info.get("ua"),
            "x-api-key": site_info.get("apikey"),
            "Accept": "application/json"
        }
        res = RequestUtils(headers=headers,
                           proxies=Config().get_proxies() if site_info.get("proxy") else None
                           ).post_res(url=site_url)
        seconds = int((datetime.now() - start_time).microseconds / 1000)
        if res and res.status_code == 200:
            msg = res.json().get("message") or "null"
            if msg == "SUCCESS":
                return True, "连接成功", seconds
            else:
                return False, msg, seconds
        elif res is not None:
            return False, f"连接失败，状态码：{res.status_code}", seconds
        else:
            return False, "无法打开网站", seconds

    # 根据种子详情页查询种子地址
    @staticmethod
    def get_torrent_url_by_detail_url(detailurl, site_info):
        m = re.match(".+/detail/([0-9]+)", detailurl)
        if not m:
            log.warn(f"【MTeanApi】 获取馒头种子连接失败 path：{detailurl}")
            return ""
        torrentid = int(m.group(1))
        apikey = site_info.get("apikey")
        if not apikey:
            log.warn(f"【MTeanApi】 {torrentid}未设置站点Api-Key，无法获取种子连接")
            return ""
        downloadurl = "https://api.m-team.cc/api/torrent/genDlToken"
        res = RequestUtils(
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "User-Agent": site_info.get("ua"),
                "x-api-key": site_info.get("apikey"),
            },
            proxies=Config().get_proxies() if site_info.get("proxy") else None,
            timeout=30
        ).post_res(url=downloadurl, data=("id=%d" % torrentid))
        if res and res.status_code == 200:
            res_json = res.json()
            msg = res_json.get('message')
            torrent_url = res_json.get('data')
            if msg != "SUCCESS":
                log.warn(f"【MTeanApi】 {torrentid}获取种子连接失败：{msg}")
                return ""
            log.info(f"【MTeanApi】 {torrentid} 获取馒头种子连接成功: {torrent_url}")
            return torrent_url
        elif res is not None:
            log.warn(f"【MTeanApi】 {torrentid}获取种子连接失败，错误码：{res.status_code}")
        else:
            log.warn(f"【MTeanApi】 {torrentid}获取种子连接失败，无法连接 {base_url}")
        return ""

    # 拉取馒头字幕列表
    @staticmethod
    def get_subtitle_list(torrentid, ua, apikey):
        subtitle_list = []
        site_url = "https://api.m-team.cc/api/subtitle/list"
        res = RequestUtils(
            headers={
                'x-api-key': apikey,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": ua,
                "Accept": "application/json"
            },
            timeout=30
        ).post_res(url=site_url, data=("id=%d" % torrentid))
        if res and res.status_code == 200:
            msg = res.json().get('message')
            if msg != "SUCCESS":
                log.warn(f"【MTeanApi】 获取馒头{torrentid}字幕列表失败：{msg}")
                return subtitle_list
            results = res.json().get('data', [])
            for result in results:
                subtitle = {
                    "id": result.get("id"),
                    "filename": result.get("filename"),
                }
                subtitle_list.append(subtitle)
            log.info(f"【MTeanApi】 获取馒头{torrentid}字幕列表成功，捕获：{len(subtitle_list)}条字幕信息")
        elif res is not None:
            log.warn(f"【MTeanApi】 获取馒头{torrentid}字幕列表失败，错误码：{res.status_code}")
        else:
            log.warn(f"【MTeanApi】 获取馒头{torrentid}字幕列表失败，无法连接 {site_url}")
        return subtitle_list

    # 下载单个馒头字幕
    @staticmethod
    def download_single_subtitle(torrentid, subtitle_info, ua, apikey, download_dir):
        subtitle_id = int(subtitle_info.get("id"))
        filename = subtitle_info.get("filename")
        # log.info(f"【Sites】开始下载馒头{torrentid}字幕 {filename}")
        site_url = "https://api.m-team.cc/api/subtitle/dl?id=%d" % subtitle_id
        res = RequestUtils(
            headers={
                'x-api-key': apikey,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": ua,
                "Accept": "*/*"
            },
            timeout=30
        ).get_res(site_url)
        if res and res.status_code == 200:
            # 创建目录
            if not os.path.exists(download_dir):
                os.makedirs(download_dir, exist_ok=True)
            # 保存ZIP
            file_name = filename
            if not file_name:
                log.warn(f"【MTeanApi】 馒头{torrentid} 字幕文件非法：{subtitle_id}")
                return
            save_tmp_path = Config().get_temp_path()
            if file_name.lower().endswith(".zip"):
                # ZIP包
                zip_file = os.path.join(save_tmp_path, file_name)
                # 解压路径
                zip_path = os.path.splitext(zip_file)[0]
                with open(zip_file, 'wb') as f:
                    f.write(res.content)
                # 解压文件
                shutil.unpack_archive(zip_file, zip_path, format='zip')
                # 遍历转移文件
                for sub_file in PathUtils.get_dir_files(in_path=zip_path, exts=RMT_SUBEXT):
                    target_sub_file = os.path.join(download_dir,
                                                   os.path.splitext(os.path.basename(sub_file))[0])
                    log.info(f"【MTeanApi】 馒头{torrentid} 转移字幕 {sub_file} 到 {target_sub_file}")
                    SiteHelper.transfer_subtitle(sub_file, target_sub_file)
                # 删除临时文件
                try:
                    shutil.rmtree(zip_path)
                    os.remove(zip_file)
                except Exception as err:
                    ExceptionUtils.exception_traceback(err)
            else:
                sub_file = os.path.join(save_tmp_path, file_name)
                # 保存
                with open(sub_file, 'wb') as f:
                    f.write(res.content)
                target_sub_file = os.path.join(download_dir,
                                               os.path.splitext(os.path.basename(sub_file))[0])
                log.info(f"【MTeanApi】 馒头{torrentid} 转移字幕 {sub_file} 到 {target_sub_file}")
                SiteHelper.transfer_subtitle(sub_file, target_sub_file)
        elif res is not None:
            log.warn(f"【MTeanApi】 下载馒头{torrentid}字幕 {filename} 失败，错误码：{res.status_code}")
        else:
            log.warn(f"【MTeanApi】 下载馒头{torrentid}字幕 {filename} 失败，无法连接 {site_url}")

    # 下载馒头字幕
    @staticmethod
    def download_subtitle(media_info, site_id, cookie, ua, apikey, download_dir):
        addr = parse.urlparse(media_info.page_url)
        log.info(f"【Sites】下载馒头字幕 {media_info.page_url}")
        # /detail/770**
        m = re.match("/detail/([0-9]+)", addr.path)
        if not m:
            log.warn(f"【MTeanApi】 获取馒头字幕失败 path：{addr.path}")
            return
        torrentid = int(m.group(1))
        if not apikey:
            log.warn(f"【MTeanApi】 获取馒头字幕失败, 未设置站点Api-Key")
            return
        subtitle_list = MTeamApi.get_subtitle_list(torrentid, ua, apikey)
        # 下载所有字幕文件
        for subtitle_info in subtitle_list:
            MTeamApi.download_single_subtitle(torrentid, subtitle_info, ua, apikey, download_dir)

    # 检查m-team.cc站点
    @staticmethod
    def check():
        site_url = "https://api.m-team.cc/"
        res = RequestUtils().get_res(url=site_url)
        if res and res.status_code == 200:
            try:
                html = res.text
                log.debug(html)
                if html.find("主站点") == -1:
                    return False
                return True
            except Exception as err:
                log.error("【Sites】连接m-team.cc出错：%s" % str(err))
                return False
        return False

    # 获取指定时间后的种子列表
    @staticmethod
    def get_new_torrents(last_time, ua, apikey):
        site_url = "https://api.m-team.cc/api/torrents"
        params = {
            "startdate": last_time
        }
        res = RequestUtils(
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "User-Agent": ua,
                "x-api-key": apikey,
                "Accept": "application/json"
            },
            params=params
        ).get_res(url=site_url)
        if res and res.status_code == 200:
            return res.json().get("data")
        return []

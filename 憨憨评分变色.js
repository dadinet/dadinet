// ==UserScript==
// @name         憨憨评分变色
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  根据豆瓣评分变换条目背景颜色
// @author       You
// @match        https://hhanclub.top/*
// @grant        none
// ==/UserScript==


// 定义一个函数，用于计算红色通道的值
function getR(score) {
    // 计算红色通道的值
    var value = (Math.abs(score - 5) / 5) * 765 - 255;
    if (value > 255) value = 255;
    if (value < 0) value = 0;
    return value;
}

// 定义一个函数，用于计算绿色通道的值
function getG(score) {
    // 计算绿色通道的值
    var value = (1 - (Math.abs(score - 20 / 3) / 5)) * 765 - 255 - 60;
    if (value > 255) value = 255;
    if (value < 0) value = 0;
    return value;
}

// 定义一个函数，用于计算蓝色通道的值
function getB(score) {
    // 计算蓝色通道的值
    var value = (1 - (Math.abs(score - 10 / 3) / 5)) * 765 - 255;
    if (value > 255) value = 255;
    if (value < 0) value = 0;
    return 0;
}

// 定义一个函数，用于修复一对值，确保它们都不是-1或超出范围
function fixPair(d, i) {
    d = d != -1 ? d : i;
    i = i != -1 ? i : d;
    d = d != -1 ? d : 255;
    i = i != -1 ? i : 255;
    return [d, i];
}

(function() {
    'use strict';

    // 获取所有的条目
    var group = $('.torrent-table-sub-info');

    // 遍历每个条目
    group.each(function() {
        var imdbElement = $(this).find('span.flex:has(img[alt="imdb"])');
        var doubanElement = $(this).find('span.flex:has(img[alt="douban"])');

        // 获取 IMDb 和豆瓣评分的文本值
        var imdbRating = parseFloat(imdbElement.text().trim());
        var doubanRating = parseFloat(doubanElement.text().trim());

        // 取得一行的豆瓣和IMDb评分后统一计算颜色
        var dr = -1, dg = -1, db = -1, ir = -1, ig = -1, ib = -1;

        if (!isNaN(imdbRating)) {
            ir = getR(imdbRating);
            ig = getG(imdbRating);
            ib = getB(imdbRating);
        }

        if (!isNaN(doubanRating)) {
            dr = getR(doubanRating);
            dg = getG(doubanRating);
            db = getB(doubanRating);
        }

        [dr, ir] = fixPair(dr, ir);
        [dg, ig] = fixPair(dg, ig);
        [db, ib] = fixPair(db, ib);

        // 如果两个数值都能获取到评分
        if (!isNaN(doubanRating) && !isNaN(imdbRating)) {
            $(this).css({'background-image': 'linear-gradient(to right, rgb(' + ir + ',' + ig + ',' + ib + '), rgb(' + dr + ',' + dg + ',' + db + ')'});

            }
        // 如果只有douban能获取到评分
        if (!isNaN(doubanRating) && isNaN(imdbRating)) {
            $(this).css({'background-image': 'linear-gradient(to right, rgb(' + ir + ',' + ig + ',' + ib + '), rgb(' + dr + ',' + dg + ',' + db + ')'});

            }
        // 如果只有imdb能获取到评分
        if (isNaN(doubanRating) && !isNaN(imdbRating)) {
            $(this).css({'background-image': 'linear-gradient(to right, rgb(' + ir + ',' + ig + ',' + ib + '), rgb(' + dr + ',' + dg + ',' + db + ')'});

            }

});
})();

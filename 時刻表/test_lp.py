const TDX_CONFIG = {
    clientId: 'r36144112-d7b2ebdd-ce4c-40c3',
    clientSecret: '141d81d1-a450-4610-9309-412c8151cc3d'
};

window.trainSchedule = {}; 
let accessToken = "";
window.stationMap = {}; 

// 1. 取得 Access Token
async function getAccessToken() {
    try {
        const params = new URLSearchParams();
        params.append('grant_type', 'client_credentials');
        params.append('client_id', TDX_CONFIG.clientId);
        params.append('client_secret', TDX_CONFIG.clientSecret);
        const res = await fetch("https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token", {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
        });
        const data = await res.json();
        accessToken = data.access_token;
        console.log("Token 取得成功");
        return accessToken;
    } catch (error) {
        console.error("Token Error:", error);
    }
}

// 2. 初始化車站資料 (V2)
async function initStationMap() {
    if (!accessToken) await getAccessToken();
    try {
        const res = await fetch("https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/Station?$format=JSON", {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        const data = await res.json();
        window.stationMap = {};
        data.forEach(s => {
            window.stationMap[s.StationID] = s.StationName.Zh_tw;
        });
        console.log("高鐵車站清單 (V2) 初始化成功");
    } catch (error) {
        console.error("車站資料抓取失敗:", error);
    }
}

// 3. 抓取時刻表 (V2 正確路徑：DailyTrainTimetable/TrainDate/{date})
async function fetchRealData(date) {
    if (!accessToken) await getAccessToken();
    if (Object.keys(window.stationMap || {}).length === 0) await initStationMap();

    try {
        // ✅ 修正：V2 高鐵每日時刻表端點應為 DailyTimetable
const url = `https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/DailyTimetable/TrainDate/${date}?$format=JSON`;
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${accessToken}` } });
        
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        
        const data = await res.json();
        const translated = {};

        data.forEach(item => {
            const trainNo = item.DailyTrainInfo.TrainNo;
            translated[trainNo] = {
                '車站時間': item.StopTimes.map(stop => ([
                    stop.StationName.Zh_tw,
                    stop.DepartureTime, 
                    stop.ArrivalTime
                ]))
            };
        });

        window.trainSchedule = translated;
        console.log("THSR 時刻表轉換成功！車次總數:", Object.keys(window.trainSchedule).length);
    } catch (error) {
        console.error("時刻表解析失敗:", error);
    }
}

/**
 * 抓取指定日期、起訖站的剩餘座位狀態 (V2)
 * @param {string} date - 格式 YYYY-MM-DD
 * @param {string} originID - 起點車站 ID
 * @param {string} destinationID - 終點車站 ID
 */
window.fetchSeatStatusOD = async function(date, originID, destinationID) {
    // 確保參數存在才發送請求
    if (!date || !originID || !destinationID) return {};
    
    if (!accessToken) await getAccessToken();
    const url = `https://tdx.transportdata.tw/api/basic/v2/Rail/THSR/AvailableSeatStatus/Train/OD/${originID}/to/${destinationID}/TrainDate/${date}?$format=JSON`;
    
    try {
        const res = await fetch(url, { headers: { 'Authorization': `Bearer ${accessToken}` } });
        if (!res.ok) return {}; // 若 API 回傳 400/500 直接跳出
        
        const data = await res.json();
        const results = {};
        const items = data.AvailableSeats || [];
        items.forEach(item => {
            results[String(item.TrainNo)] = {
                standard: item.StandardSeatStatus,
                business: item.BusinessSeatStatus
            };
        });
        return results;
    } catch (error) {
        console.error("座位 API 請求失敗:", error);
        return {};
    }
};

// 讓此函數回傳原始代碼，不做文字轉換
function translateSeatStatus(status) {
    return status || '--';
}



// 4. 移除誤點資料抓取邏輯
async function updateLiveDelay() {
    // 根據用戶需求，不再請求即時資訊，直接回傳空值或維持現狀
    liveDelayMap = {}; 
    return Promise.resolve();
}
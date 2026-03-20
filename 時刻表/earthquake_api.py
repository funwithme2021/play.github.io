from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def fetch_earthquake_data():
    url = "https://www.cwa.gov.tw/V8/C/E/index.html"  # 中央氣象局地震資訊頁面
    response = requests.get(url)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    earthquake_data = []

    # 找到地震資訊的表格
    table = soup.find("table", {"class": "eq-table"})
    if table:
        rows = table.find_all("tr")[1:]  # 跳過標題列
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 5:
                data = {
                    "時間": cols[0].text.strip(),
                    "震央": cols[1].text.strip(),
                    "規模": cols[2].text.strip(),
                    "深度": cols[3].text.strip(),
                    "震度分布": cols[4].text.strip(),
                }
                earthquake_data.append(data)
    return earthquake_data

@app.route("/api/earthquakes", methods=["GET"])
def get_earthquake_data():
    data = fetch_earthquake_data()
    return jsonify(data)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

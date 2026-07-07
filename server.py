#!/usr/bin/env python3
"""
安心住 Demo 代理服务器
使用智谱 GLM-5V-Turbo（视觉模型）分析图片安全隐患，
使用 GLM-4-Flash（免费文本模型）生成报告。
API Key 内置服务器端，用户无需配置。
"""
import json
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===== 配置（API Key 内置，用户不可见）=====
ZHIPU_API_KEY = "ccac951090994d7781c9df2d372ca6cb.E6kcQ65JWWgvRzdO"
ZHIPU_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
VISION_MODEL = "glm-5v-turbo"   # 视觉模型，直接看图分析
TEXT_MODEL = "glm-4"      # 文本模型，用于报告生成

PORT = 8099

PHOTO_ANALYSIS_PROMPT = """你是居家安全评估专家，专注老年人跌倒预防。请仔细观察这张{AREA_NAME}的照片，分析所有可能导致老人（特别是夜间起夜时）跌倒或受伤的安全隐患。

请以严格JSON格式返回（不要包含markdown代码块标记），结构如下：
{{
  "hazards": [
    {{
      "title": "隐患简称（4-6个字）",
      "description": "详细说明这个隐患为什么危险，对老人有什么具体影响",
      "severity": "high 或 medium 或 low",
      "location": {{"x": 0.0-1.0, "y": 0.0-1.0, "width": 0.0-1.0, "height": 0.0-1.0}},
      "suggestion": "具体的整改建议",
      "cost": 0
    }}
  ],
  "summary": "这张照片的整体安全评估",
  "objects_detected": ["检测到的主要物品"]
}}

注意：
- location中的x,y是隐患区域中心点的位置（0.0=最左/最上，1.0=最右/最下），width和height是隐患区域占图片的比例大小（0.0-1.0）
- 如果隐患是全局性的（如光线不足），location设为null
- 仔细观察图片中的：地面障碍物、家具边角碰撞风险、物品散落绊倒风险、通道宽度不足、光线照明情况、地面湿滑、电线杂乱等
- 如果看到椅子、桌子等家具，分析其位置是否阻碍通行
- 如果看到鞋子、电线、杂物等物品，分析是否可能绊倒
- 每张照片至少找出2-3个隐患，如果确实安全也要如实说明
- cost单位是元，0表示无需花费（如整理收纳）"""

REPORT_GEN_PROMPT = """你是一个懂中国家庭代际关系的居家安全顾问。

背景：一个成年子女用AI检查了父母（或即将搬来同住的老人）家里的安全隐患，现在需要一份"与父母沟通指南"，帮助子女说服老人接受必要的适老化改造。

分析结果：
{HAZARDS_JSON}

请以严格JSON格式返回（不要包含markdown代码块标记）：
{{
  "child_report": {{
    "comm_tips": ["沟通技巧1", "沟通技巧2"],
    "qa_list": [
      {{"q": "老人说的话", "a": "建议回答"}}
    ],
    "action_plan": "整体改造建议总结"
  }},
  "parent_report": {{
    "encouragement": "给老人的鼓励话语",
    "shopping_note": "购物建议（口语化）"
  }}
}}

【沟通技巧写作要求 - 非常重要】
- 你写的是【成年子女如何跟自己的老年父母沟通】的技巧，不是父母跟小孩说安全须知
- 每条技巧必须包含具体的"话术示范"，给出子女实际该怎么说
- 语气要像一个有经验的朋友在分享实战经验，不要像教科书
- 禁止使用"宝贝""小朋友""孩子"等称呼，这个场景里没有小孩
- 禁止使用"建议您""应当""需要注意"等书面语，用"你可以跟老人说""别急着""先这样"这类口语
- 至少写7条技巧，每条针对一个不同的沟通难点

【问答写作要求 - 非常重要】
- 每个问题必须是【老年父母真实会说的话】，要带情绪、带口语、带抵触心理
- 典型例子："我这身子骨好着呢，不用折腾""花那冤枉钱干啥""我住了几十年了，好好的""装这些乱七八糟的家里跟医院似的""我不想给你们添麻烦""这些东西放了几十年了，你别动我的东西""扶手？我又不是残疾人"
- 回答要有同理心，先认同老人的感受（不能正面反驳），再给出理由和话术
- 回答里要有具体的话术示范，让子女知道怎么开口
- 禁止出现"数据显示""统计表明"这类生硬的引用，用"您想啊""您算算"这类大白话
- 至少写7组问答

【父母版写作要求】
- encouragement 要温暖但不说教，像自家孩子跟老人说话的语气
- shopping_note 要让老人觉得简单，用聊天的方式说"""


class DemoHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/安心住_Demo.html":
            self._serve_file("安心住_Demo.html", "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send_json({"status": "ok"})
        elif self.path == "/test.jpg":
            self._serve_file("/data/user/work/test_room.jpg", "image/jpeg")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/analyze":
            self._handle_analyze()
        elif self.path == "/api/report":
            self._handle_report()
        else:
            self.send_error(404)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _serve_file(self, filename, content_type):
        try:
            with open(filename, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        return json.loads(body)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _call_zhipu(self, messages, model=TEXT_MODEL, max_tokens=4096):
        """Call Zhipu GLM API with built-in API key."""
        headers = {
            "Authorization": f"Bearer {ZHIPU_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
            "temperature": 0.1,
        }
        resp = requests.post(
            ZHIPU_ENDPOINT, json=payload, headers=headers, timeout=120
        )
        data = resp.json()
        if resp.status_code != 200:
            err_msg = data.get("error", {}).get("message", "")
            if not err_msg:
                err_msg = data.get("msg", str(data))
            raise Exception(f"GLM API 错误: {err_msg}")
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            # GLM-5V-Turbo 可能把内容放在 reasoning_content 里
            content = data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")
        if not content:
            raise Exception("GLM API 返回内容为空")
        return content

    def _parse_llm_json(self, text):
        """Strip markdown code fences and parse JSON."""
        import re

        s = text.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
        if fence:
            s = fence.group(1).strip()
        s = re.sub(r"^```|```$", "", s).strip()
        first = s.find("{")
        last = s.rfind("}")
        if first != -1 and last != -1 and last > first:
            s = s[first : last + 1]
        s = re.sub(r",\s*([}\]])", r"\1", s)
        return json.loads(s)

    def _handle_analyze(self):
        try:
            body = self._read_body()
            image_data_url = body.get("image", "")
            area_name = body.get("area_name", "未知区域")

            prompt_text = PHOTO_ANALYSIS_PROMPT.replace("{AREA_NAME}", area_name)

            # GLM-5V-Turbo 支持 content 数组：图片 + 文字
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url},
                        },
                        {
                            "type": "text",
                            "text": prompt_text,
                        },
                    ],
                }
            ]

            print(f"  [分析] 调用 GLM-5V-Turbo 视觉模型... ({area_name})")
            result_text = self._call_zhipu(
                messages, model=VISION_MODEL, max_tokens=16384
            )
            print(f"  [分析] 完成, 返回 {len(result_text)} 字符")

            result = self._parse_llm_json(result_text)
            self._send_json(result)

        except Exception as e:
            print(f"  [分析] 错误: {e}")
            self._send_json({"error": str(e)}, status=500)

    def _handle_report(self):
        try:
            body = self._read_body()
            hazards_json = body["hazards"]

            prompt = REPORT_GEN_PROMPT.replace(
                "{HAZARDS_JSON}", json.dumps(hazards_json, ensure_ascii=False)
            )
            messages = [{"role": "user", "content": prompt}]

            print(f"  [报告] 调用 GLM-4-Flash 生成报告...")
            result_text = self._call_zhipu(
                messages, model=TEXT_MODEL, max_tokens=16384
            )
            print(f"  [报告] 完成, 返回 {len(result_text)} 字符")

            result = self._parse_llm_json(result_text)
            self._send_json(result)

        except Exception as e:
            print(f"  [报告] 错误: {e}")
            self._send_json({"error": str(e)}, status=500)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("0.0.0.0", PORT), DemoHandler)
    print(f"安心住 Demo 服务器运行在 http://localhost:{PORT}")
    print(f"用浏览器打开上述地址即可使用")
    print(f"按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.shutdown()

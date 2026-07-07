安心住 · 居家安全AI自查 Demo
================================

【文件说明】
- 安心住_Demo.html  ：前端页面
- server.py         ：Python 代理服务器（内置智谱 API Key）
- README.txt        ：本说明文件

【运行方式】

1. 安装依赖
   pip install requests

2. 启动代理服务器
   python server.py

3. 打开浏览器访问
   http://localhost:8099

4. 直接开始使用，无需配置 API Key

【技术架构】
- 图片分析：智谱 GLM-5V-Turbo 视觉大模型，直接看图识别安全隐患
- 报告生成：智谱 GLM-4-Flash（免费），生成子女版和父母版报告
- API Key 内置在 server.py 中，用户界面无需配置

【优势】
- GLM-5V-Turbo 能直接看懂图片内容，识别电线、杂物、地毯卷边等细节隐患
- 相比传统物体检测模型（如 COCO-SSD），理解能力大幅提升
- 用户无需配置任何 API Key，一键开始使用

【注意事项】
- 需要联网访问智谱 API
- 端口默认 8099，可在 server.py 中修改 PORT 变量
- API Key 已内置，如需更换请在 server.py 中修改 ZHIPU_API_KEY

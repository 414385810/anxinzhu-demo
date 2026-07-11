安心住 · 居家安全AI自查 Demo
================================

【项目简介】
面向老年人居家跌倒预防的AI安全自查 Demo。用户上传卧室、行走通道、卫生间入口三处照片，AI 自动识别隐患、标注位置、生成子女版与父母版两份改造沟通报告。

线上体验：https://414385810.github.io/anxinzhu-demo/

【文件说明】
- 安心住_Demo_独立版.html  ：当前主版本，纯前端独立运行，无需后端服务器
- 安心住_Demo.html        ：旧版前端页面，需配合 server.py 使用
- server.py               ：Python 代理服务器（旧版方案，内置智谱 API Key）
- README.txt              ：本说明文件

【独立版运行方式】

1. 直接用浏览器打开
   安心住_Demo_独立版.html

2. 或访问 GitHub Pages 线上地址
   https://414385810.github.io/anxinzhu-demo/

3. 手机微信中打开链接即可拍照/选图使用

【旧版运行方式（需本地服务器）】

1. 安装依赖
   pip install requests

2. 启动代理服务器
   python server.py

3. 打开浏览器访问
   http://localhost:8099

【技术架构】
- 图片隐患识别：阿里云百炼 qwen-vl-plus（首选）/ qwen-vl-max（备选）视觉大模型
- 风险交叉验证：火山方舟 doubao-seed-2-1-pro-260628
- 报告生成与润色：火山方舟 doubao-seed-2-1-pro-260628
- 报告长图生成：内联 html2canvas，无需外部 CDN

【优势】
- 视觉大模型直接理解图片内容，可识别电线、杂物、地毯卷边、地面湿滑等细节隐患
- 纯前端独立版部署简单，打开即用，无需配置 API Key
- 同时生成给子女看的“沟通指南”和给父母看的“温和版说明”

【注意事项】
- 需要联网访问阿里云百炼与火山方舟 API
- 端口默认 8099（仅旧版 server.py），可在 server.py 中修改 PORT 变量
- 如需更换 API Key，请在对应 HTML 文件或 server.py 中修改

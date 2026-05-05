# 销售宗师官网部署指南

## 项目结构

```
website/
├── index.html              # 主页面
└── static/
    ├── css/
    │   └── style.css       # 样式文件
    ├── js/
    │   └── main.js         # 脚本文件
    └── images/             # 图片目录（可选）
```

## 快速部署

### 方式一：本地预览

直接用浏览器打开 `index.html` 文件即可预览。

### 方式二：本地开发服务器

```bash
# 使用 Python (推荐)
cd website
python -m http.server 8000
# 访问 http://localhost:8000

# 或使用 Node.js
npx serve .
# 访问 http://localhost:3000
```

### 方式三：部署到静态托管平台

#### Vercel（推荐）

```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署
cd website
vercel
```

#### Netlify

```bash
# 安装 Netlify CLI
npm install -g netlify-cli

# 部署
cd website
netlify deploy --prod
```

#### GitHub Pages

1. 创建 GitHub 仓库
2. 将 `website` 目录内容推送到仓库
3. 在仓库设置中开启 GitHub Pages

### 方式四：部署到云服务器

```bash
# 复制文件到服务器
scp -r website/* user@your-server-ip:/var/www/html/

# 配置 Nginx
# 编辑 /etc/nginx/sites-available/default
location / {
    root /var/www/html;
    index index.html;
    try_files $uri $uri/ /index.html;
}
```

## 环境要求

- 无需后端服务器，纯静态网站
- 支持所有现代浏览器（Chrome、Safari、Firefox、Edge）
- 响应式设计，支持移动端

## 自定义配置

### 修改配色方案

编辑 `static/css/style.css` 中的 CSS 变量：

```css
:root {
    --blue: #0071e3;        /* 主色调 */
    --orange: #ff9500;      /* 辅助色 */
    --gray-500: #6e6e73;   /* 文字颜色 */
}
```

### 修改页面内容

编辑 `index.html` 中的文本内容。

### 添加新页面

在 `index.html` 中添加新的 `<div id="page-xxx" class="page">` 块，并更新导航链接。

## 性能优化建议

1. **压缩资源**：使用 Gzip/Brotli 压缩 CSS/JS 文件
2. **图片优化**：使用 WebP 格式，添加懒加载
3. **启用 CDN**：使用 CDN 加速静态资源
4. **缓存策略**：配置浏览器缓存和 CDN 缓存

## 安全建议

1. **HTTPS**：强制使用 HTTPS
2. **CSP**：配置内容安全策略
3. **X-Frame-Options**：防止点击劫持

## 联系我们

如有部署问题，请联系：contact@salesmaster.com
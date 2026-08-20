# 英语学习

这是一个个人英语学习页面，会自动读取 `英语学习.md` 并展示每天学习的单词。

## 本地运行

```powershell
powershell -ExecutionPolicy Bypass -File .\server.ps1 start
```

访问：

```text
http://127.0.0.1:60001/index.html
```

## GitHub Pages 部署

把本目录推送到 GitHub 仓库后，在 GitHub 仓库页面开启 Pages：

1. 进入仓库的 `Settings`
2. 打开 `Pages`
3. `Build and deployment` 选择 `Deploy from a branch`
4. Branch 选择 `main`
5. Folder 选择 `/root`
6. 保存后等待 GitHub 生成访问地址

生成后通常是：

```text
https://你的用户名.github.io/仓库名/
```
# 回顾记录同步

回顾进度保存在 `回顾记录.md` 中，不依赖云端服务或数据库。页面启动时会读取这个文件，并与当前浏览器里的临时进度按每个单词的更新时间合并。

每次学习结束后：

1. 点击页面右上角的“导出回顾记录”。
2. 用下载得到的 `回顾记录.md` 替换项目中的同名文件。
3. 将更新后的文件提交并推送到 GitHub。

在另一台设备打开 GitHub Pages 后，页面会读取仓库中的 `回顾记录.md`，继续之前的复习进度。浏览器本地存储只作为离线缓存，真正用于跨设备携带的是这个 Markdown 文件。


# GitHub Pages 部署步骤

## 1. 在 GitHub 创建仓库

建议仓库名：

```text
english-learning
```

可以选择 Public，这样 GitHub Pages 免费且最简单。

## 2. 推送本地文件

在本目录运行：

```powershell
git init
git branch -M main
git add .
git commit -m "Initial English learning page"
git remote add origin https://github.com/你的用户名/english-learning.git
git push -u origin main
```

## 3. 开启 GitHub Pages

进入 GitHub 仓库：

```text
Settings -> Pages
```

选择：

```text
Source: Deploy from a branch
Branch: main
Folder: /root
```

保存后等待一会儿，GitHub 会给你一个网址。

## 4. 每天更新单词后同步

以后每天我帮你更新 `英语学习.md` 后，你运行：

```powershell
git add 英语学习.md
git commit -m "Add words for YYYY-MM-DD"
git push
```

手机上刷新 GitHub Pages 页面即可学习。


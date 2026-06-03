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


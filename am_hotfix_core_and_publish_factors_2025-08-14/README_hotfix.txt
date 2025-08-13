AnxiousMonkey Hotfix — core shim + publish-factors rebase push
==============================================================

这个补丁做两件事：
1) 新增 core/ 兼容层：让 `from core.utils import ...` 正常工作（实际转发到 tools.utils）。
2) 修复 publish-factors 工作流推送失败：加入 fetch + pull --rebase，再 push，避免非快进拒绝。

如何使用（网页端一键上传）：
1. 在本地把本 zip 解压。
2. 进入 GitHub 仓库（anxiousmonkey-backtests）→ Code → `main` 分支根目录。
3. 点 “Add file” → “Upload files”，把解压后的 **文件夹内容** 整体拖进去（注意：要保留路径：
   - core/__init__.py
   - core/utils.py
   - .github/workflows/publish-factors.yml
   不是直接上传 zip 文件）。
4. 填写 commit message 随便，比如“hotfix: core shim + publish-factors rebase push”，提交到 main。
5. 打开 Actions 手动重跑 publish-factors、train-models。

备注：如果其它会 git push 的工作流也偶尔撞车，可以把它们的“Commit …”步骤换成和
publish-factors 同款的：先 `git fetch origin main`，再 `git pull --rebase origin main`，最后 push。

祝顺利。

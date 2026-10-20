zan Breakout — 打砖块（模板版）
====================================

玩法
----
- 鼠标/方向键移动挡板，反弹小球清砖
- 发光砖块掉落道具：多球、加长挡板等
- 清空全部砖块进入下一关，球速逐关加快

编译
----
根目录下（公共包在 zan-lang 仓库的 packages/ 下，编译要带 --package-project）：

    pwsh -File client/tools/build.ps1

产物在 build/breakout/，运行所需 DLL 与 assets/ 一并落在同目录。
手动编译（同样在根目录下）：

    $env:ZAN_HOME/build/zanc.exe client/src/main.zan --auto-stdlib --package-project $env:ZAN_HOME -o build/breakout/Breakout.exe

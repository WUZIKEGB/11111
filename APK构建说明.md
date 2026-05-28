# 污水池控制系统 APK 构建说明

## 项目结构

```
1111/
├── main.py                    # Kivy 版主程序（已从 tkinter 转换）
├── buildozer.spec             # Buildozer 打包配置
├── .github/
│   └── workflows/
│       └── build_apk.yml      # GitHub Actions 自动构建流程
└── 污水池控制软件.py             # 原始 tkinter 版本（备份）
```

---

## 如何获取 APK（推荐：免费云端构建）

### 步骤一：上传到 GitHub

1. 在 [github.com](https://github.com) 注册/登录账号
2. 创建一个新的**私有仓库**（推荐私有，防止代码泄露）
3. 将整个 `1111` 文件夹内容上传：

```bash
cd C:\Users\123\Desktop\HI304-4G\1111
git init
git add .
git commit -m "初始化污水池控制APK项目"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 步骤二：等待自动构建

- 推送后，GitHub Actions 会**自动开始构建**
- 在仓库页面点击 `Actions` 标签查看进度
- 首次构建约需 **15~30 分钟**（需要下载 Android SDK/NDK）
- 后续构建有缓存，约 **5~10 分钟**

### 步骤三：下载 APK

1. 构建成功后，点击对应的 workflow run
2. 滚动到底部 `Artifacts` 区域
3. 点击 `sewage-control-apk` 下载 zip 包
4. 解压后即可得到 `.apk` 文件

---

## 安装到手机

1. 将 APK 传输到 Android 手机
2. 在手机设置中开启「允许安装未知来源应用」
3. 点击 APK 文件安装即可

---

## 应用说明

- **应用名称**：污水池控制系统
- **包名**：org.sewage.sewagecontrol
- **最低安卓版本**：Android 8.0 (API 26)
- **目标版本**：Android 13 (API 33)
- **支持架构**：arm64-v8a, armeabi-v7a

### 功能说明

| 功能 | 说明 |
|------|------|
| 连接状态 | 自动连接 MQTT 服务器，顶部显示连接状态 |
| 刷新状态 | 主动查询设备当前状态 |
| 水泵控制 | 一键切换水泵开/关，指示灯实时显示运行状态 |
| 角度控制 | 滑动调节阀角度（0°~90°），松手后自动发送指令 |
| 实时数据 | 显示主管路流量、主管路压力、调节阀压力 |

---

## 注意事项

- 手机需要连接网络才能与 MQTT 服务器通信
- MQTT 服务器地址：`irrigation-mqtt.linkio.cn:1883`
- 如需修改服务器配置，编辑 `main.py` 顶部的 MQTT 配置区域

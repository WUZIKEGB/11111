import json
import time
import threading

# ================ 修复 Kivy 中文/Emoji 显示 ================
import sys, os
from kivy.config import Config

# 判断是否在 Android 环境
IS_ANDROID = hasattr(sys, 'getandroidapilevel')

if IS_ANDROID:
    # 安卓：使用系统内置 DroidSansFallback（所有安卓设备都有）
    Config.set('kivy', 'default_font', ['DroidSansFallback', '/system/fonts/DroidSansFallback.ttf'])

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.core.text import LabelBase

if IS_ANDROID:
    # 显式注册中文字体，覆盖默认 Roboto
    try:
        LabelBase.register(
            name="DroidSansFallback",
            fn_regular="/system/fonts/DroidSansFallback.ttf"
        )
    except Exception:
        pass

Window.clearcolor = (0.96, 0.96, 0.96, 1)

# ===================== MQTT 配置 =====================
BROKER = "irrigation-mqtt.linkio.cn"
PORT = 1883
USERNAME = "hi2g"
PASSWORD = "hi2g2022"

GATEWAY_PUMP = "201C72FFE1"
SUB_PUMP = "hi/fer/201C72FFE1/set"
PUB_PUMP = "hi/fer/201C72FFE1/get"

GATEWAY_VALVE = "B01BB0FFE1"
SUB_VALVE = "hi/zhufu/B01BB0FFE1/set"
PUB_VALVE = "hi/zhufu/B01BB0FFE1/get"

# ===================== 圆角卡片容器 =====================
class CardLayout(BoxLayout):
    def __init__(self, title="", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.orientation = "vertical"
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.spacing = dp(8)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter("height"))
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# ===================== 状态指示灯 =====================
class StatusDot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(24), dp(24))
        self._color = (0.74, 0.74, 0.74, 1)
        with self.canvas:
            self.dot_color = Color(*self._color)
            self.dot = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *args):
        self.dot.pos = self.pos
        self.dot.size = self.size

    def set_active(self, active):
        if active:
            self.dot_color.rgba = (0.0, 0.9, 0.46, 1)
        else:
            self.dot_color.rgba = (0.74, 0.74, 0.74, 1)

# ===================== 主 UI 布局 =====================
class SewageRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.spacing = dp(10)

        self.stir_status = 0
        self.temp_angle = 0
        self.current_angle = 0

        self._build_ui()

    def _build_ui(self):
        # ---- 顶部状态栏 ----
        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50), spacing=dp(10))
        with top.canvas.before:
            Color(1, 1, 1, 1)
            self._top_rect = RoundedRectangle(pos=top.pos, size=top.size, radius=[dp(10)])
        top.bind(pos=lambda i, v: setattr(self._top_rect, "pos", v),
                 size=lambda i, v: setattr(self._top_rect, "size", v))

        self.refresh_btn = Button(
            text="[b]↺ 刷新状态[/b]", markup=True, font_name="DroidSansFallback",
            background_normal="", background_color=(0.098, 0.463, 0.824, 1), color=(1, 1, 1, 1),
            size_hint=(None, 1), width=dp(140), font_size=sp(14)
        )
        self.refresh_btn.bind(on_release=lambda x: self.refresh_btn_click())

        self.status_label = Label(
            text="[b]智能灌溉测试部[/b]", markup=True, font_name="DroidSansFallback",
            color=(0.263, 0.263, 0.263, 1), font_size=sp(13), halign="right", valign="middle"
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))

        top.padding = [dp(10), dp(6), dp(10), dp(6)]
        top.add_widget(self.refresh_btn)
        top.add_widget(self.status_label)
        self.add_widget(top)

        # ---- 水泵卡片 ----
        pump_card = CardLayout(title="潜水泵远程控制")
        pump_title = Label(
            text="[b]潜水泵远程控制[/b]", markup=True, font_name="DroidSansFallback",
            font_size=sp(15), color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        pump_title.bind(size=pump_title.setter("text_size"))
        pump_card.add_widget(pump_title)

        dot_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(10))
        self.pump_dot = StatusDot()
        self.pump_status = Label(
            text="水泵状态：待检测", font_name="DroidSansFallback",
            font_size=sp(14), color=(0.46, 0.46, 0.46, 1),
            halign="left", valign="middle"
        )
        self.pump_status.bind(size=self.pump_status.setter("text_size"))
        dot_row.add_widget(self.pump_dot)
        dot_row.add_widget(self.pump_status)
        pump_card.add_widget(dot_row)

        self.pump_btn = Button(
            text="[b]切换水泵状态[/b]", markup=True, font_name="DroidSansFallback",
            background_normal="", background_color=(1.0, 0.341, 0.133, 1), color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(48), font_size=sp(14)
        )
        self.pump_btn.bind(on_release=lambda x: self.toggle_pump())
        pump_card.add_widget(self.pump_btn)
        self.add_widget(pump_card)

        # ---- 调节阀卡片 ----
        valve_card = CardLayout(title="调节阀角度控制")
        valve_title = Label(
            text="[b]调节阀角度控制[/b]", markup=True, font_name="DroidSansFallback",
            font_size=sp(15), color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        valve_title.bind(size=valve_title.setter("text_size"))
        valve_card.add_widget(valve_title)

        self.angle_text = Label(
            text="当前角度：0 °", font_name="DroidSansFallback",
            font_size=sp(14), color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        self.angle_text.bind(size=self.angle_text.setter("text_size"))
        valve_card.add_widget(self.angle_text)

        self.angle_slider = Slider(min=0, max=90, value=0, size_hint_y=None, height=dp(50))
        self.angle_slider.bind(value=self.angle_drag)
        self.angle_slider.bind(on_touch_up=self.angle_send)
        valve_card.add_widget(self.angle_slider)

        slider_labels = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        slider_labels.add_widget(Label(text="0°", font_name="DroidSansFallback", font_size=sp(12), color=(0.5, 0.5, 0.5, 1)))
        slider_labels.add_widget(Label(text="90°", font_name="DroidSansFallback", font_size=sp(12), color=(0.5, 0.5, 0.5, 1), halign="right"))
        valve_card.add_widget(slider_labels)
        self.add_widget(valve_card)

        # ---- 数据卡片 ----
        data_card = CardLayout(title="实时监测数据")
        data_title = Label(
            text="[b]实时监测数据[/b]", markup=True, font_name="DroidSansFallback",
            font_size=sp(15), color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        data_title.bind(size=data_title.setter("text_size"))
        data_card.add_widget(data_title)

        self.flow_label = Label(
            text="主管路流量：-- m³/h", font_name="DroidSansFallback",
            font_size=sp(13), color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        self.flow_label.bind(size=self.flow_label.setter("text_size"))
        data_card.add_widget(self.flow_label)

        self.press_main_label = Label(
            text="主管路压力：-- MPa", font_name="DroidSansFallback",
            font_size=sp(13), color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        self.press_main_label.bind(size=self.press_main_label.setter("text_size"))
        data_card.add_widget(self.press_main_label)

        self.press_valve_label = Label(
            text="调节阀压力：-- MPa", font_name="DroidSansFallback",
            font_size=sp(13), color=(0.2, 0.2, 0.2, 1),
            size_hint_y=None, height=dp(30), halign="left", valign="middle"
        )
        self.press_valve_label.bind(size=self.press_valve_label.setter("text_size"))
        data_card.add_widget(self.press_valve_label)
        self.add_widget(data_card)

    # ===================== MQTT 方法 =====================
    def set_mqtt_client(self, client):
        self.mqtt_client = client

    def on_connected(self):
        Clock.schedule_once(lambda dt: self._update_connected_ui(), 0)

    def on_disconnected(self):
        Clock.schedule_once(lambda dt: self._update_disconnected_ui(), 0)

    def _update_connected_ui(self):
        self.status_label.text = "[b]✅ 智能灌溉测试部[/b]"
        self.status_label.color = (0.18, 0.49, 0.2, 1)

    def _update_disconnected_ui(self):
        self.status_label.text = "[b]❌ 连接失败[/b]"
        self.status_label.color = (0.78, 0.16, 0.16, 1)

    def refresh_btn_click(self):
        if hasattr(self, "mqtt_client"):
            self._query_device_status()

    def _query_device_status(self):
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        pump_msg = {"gw": {"msg_id": 1, "msg_no": 0, "gateway": GATEWAY_PUMP, "time": t}, "data": {"stat": 0}}
        self.mqtt_client.publish(PUB_PUMP, json.dumps(pump_msg, separators=(",", ":")))
        valve_msg = {"gw": {"msg_id": 1, "msg_no": 0, "gateway": GATEWAY_VALVE, "time": t}, "data": {"stat": 0}}
        self.mqtt_client.publish(PUB_VALVE, json.dumps(valve_msg, separators=(",", ":")))

    def toggle_pump(self):
        if not hasattr(self, "mqtt_client"):
            return
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        if self.stir_status == 0:
            payload = {"gw": {"msg_id": 4, "msg_no": 0, "gateway": GATEWAY_PUMP, "time": t}, "data": {"stir1": 1}}
            self.stir_status = 1
        else:
            payload = {"gw": {"msg_id": 4, "msg_no": 0, "gateway": GATEWAY_PUMP, "time": t}, "data": {"stir1": 0}}
            self.stir_status = 0
        self.mqtt_client.publish(PUB_PUMP, json.dumps(payload, separators=(",", ":")))

    def angle_drag(self, slider, value):
        self.temp_angle = int(value)
        Clock.schedule_once(lambda dt: setattr(self.angle_text, "text", f"当前角度：{self.temp_angle} °"), 0)

    def angle_send(self, slider, touch):
        if not slider.collide_point(*touch.pos):
            return
        if not hasattr(self, "mqtt_client"):
            return
        angle = self.temp_angle
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        payload = {"gw": {"msg_id": 4, "msg_no": 0, "gateway": GATEWAY_VALVE, "time": t}, "data": {"angle1": angle}}
        self.mqtt_client.publish(PUB_VALVE, json.dumps(payload, separators=(",", ":")))

    def handle_message(self, gateway, data):
        if gateway == GATEWAY_PUMP:
            node_list = data.get("node", [])
            if node_list and "stir" in node_list[0]:
                stir = node_list[0]["stir"]
                self.stir_status = stir
                def update_pump(dt):
                    if stir == 1:
                        self.pump_dot.set_active(True)
                        self.pump_status.text = "水泵运行中"
                        self.pump_status.color = (0.0, 0.784, 0.325, 1)
                    else:
                        self.pump_dot.set_active(False)
                        self.pump_status.text = "水泵已关闭"
                        self.pump_status.color = (0.46, 0.46, 0.46, 1)
                Clock.schedule_once(update_pump, 0)

        elif gateway == GATEWAY_VALVE:
            def update_valve(dt):
                if "pressure2" in data:
                    v = f"{data['pressure2']:.2f}"
                    self.press_main_label.text = f"主管路压力：{v} MPa"
                if "pressure1" in data:
                    v = f"{data['pressure1']:.2f}"
                    self.press_valve_label.text = f"调节阀压力：{v} MPa"
                if "flow1" in data:
                    v = f"{data['flow1']:.3f}"
                    self.flow_label.text = f"主管路流量：{v} m³/h"
                if "angle1" in data:
                    a = data["angle1"]
                    self.angle_text.text = f"当前角度：{a} °"
                    self.angle_slider.value = a
            Clock.schedule_once(update_valve, 0)

# ===================== App 入口 =====================
class SewageApp(App):
    def build(self):
        self.title = "水池远程控制"
        from paho.mqtt import client as mqtt_client
        self.root_widget = SewageRoot()
        client_id = f"kivy_mqtt_{int(time.time())}"
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id=client_id)
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        threading.Thread(target=self._connect, daemon=True).start()
        self.root_widget.set_mqtt_client(self.client)
        return self.root_widget

    def _connect(self):
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            Clock.schedule_once(lambda dt: self.root_widget._update_disconnected_ui(), 0)

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            self.root_widget.on_connected()
            client.subscribe(SUB_PUMP)
            client.subscribe(SUB_VALVE)
            Clock.schedule_once(lambda dt: self.root_widget._query_device_status(), 0.5)
        else:
            self.root_widget.on_disconnected()

    def on_message(self, client, userdata, msg):
        try:
            raw = msg.payload.decode("utf-8")
            clean = raw.replace("\n", "").replace("\t", "")
            payload = json.loads(clean)
            gw = payload.get("gw", {})
            gateway = gw.get("gateway", "")
            data = payload.get("data", {})
            self.root_widget.handle_message(gateway, data)
        except Exception:
            pass

    def on_stop(self):
        if hasattr(self, "client"):
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    SewageApp().run()
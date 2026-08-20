#!/usr/bin/env python3
"""Generate BPMN 2.0 XML for StormBPMN import."""

from xml.sax.saxutils import escape

W_TASK, H_TASK = 160, 78
W_GW, H_GW = 50, 50
W_EV, H_EV = 36, 36


def task(x, y):
    return x, y, W_TASK, H_TASK


def gw(x, y_task):
    return x, y_task + (H_TASK - H_GW) // 2, W_GW, H_GW


def ev(x, y_task):
    return x, y_task + (H_TASK - H_EV) // 2, W_EV, H_EV


# --- layout ---
Y_C = 130  # client happy path
Y_C_EX = 300  # client exceptions
Y_S = 560  # STO happy path
Y_S_EX = 730  # STO exceptions

# client X
c = {}
c["create"] = task(400, Y_C)
c["pick"] = task(600, Y_C)
c["check"] = task(800, Y_C)
c["gw_shelf"] = gw(1000, Y_C)
c["reserve"] = task(1090, Y_C)
c["gw_ext"] = gw(1290, Y_C)
c["check_ext"] = task(1380, Y_C)
c["gw_ext_ok"] = gw(1580, Y_C)
c["do_ext"] = task(1670, Y_C)
c["join_ext"] = gw(1870, Y_C)
c["check_pay"] = task(1960, Y_C)
c["gw_pay"] = gw(2160, Y_C)
c["receipt"] = task(2250, Y_C)
c["end_ok"] = ev(2450, Y_C)

c["msg_block"] = task(920, Y_C_EX)
c["repick"] = task(720, Y_C_EX)
c["no_ext"] = task(1480, Y_C_EX)
c["repick_ext"] = task(1280, Y_C_EX)
c["block_sale"] = task(2080, Y_C_EX)
c["end_cancel"] = ev(2280, Y_C_EX)

# STO X
s = {}
s["plan"] = task(400, Y_S)
s["pick"] = task(600, Y_S)
s["check"] = task(800, Y_S)
s["gw_plan"] = gw(1000, Y_S)
s["reserve"] = task(1090, Y_S)
s["install"] = task(1290, Y_S)
s["gw_shift"] = gw(1490, Y_S)
s["receipt"] = task(1580, Y_S)
s["end_ok"] = ev(1780, Y_S)

s["msg_other"] = task(920, Y_S_EX)
s["repick"] = task(720, Y_S_EX)
s["gw_inst"] = gw(1490, Y_S_EX)
s["repick_date"] = task(1290, Y_S_EX)
s["receipt_now"] = task(1580, Y_S_EX)
s["end_early"] = ev(1780, Y_S_EX)

# shared
start = ev(80, 340)
channel = gw(220, 340)


def box(b):
    x, y, w, h = b
    return x, y, w, h


def cx(b):
    x, y, w, h = b
    return x + w / 2, y + h / 2


def right(b):
    x, y, w, h = b
    return x + w, y + h / 2


def left(b):
    x, y, w, h = b
    return x, y + h / 2


def bottom(b):
    x, y, w, h = b
    return x + w / 2, y + h


def top(b):
    x, y, w, h = b
    return x + w / 2, y


nodes = [
    ("StartEvent_1", "startEvent", "Старт", *start),
    ("Gateway_Channel", "exclusiveGateway", "Какой канал продажи?", *channel),
    # client
    ("Task_CreateOrder", "serviceTask", "Создать накладную и резерв 24ч", *c["create"]),
    ("Task_PickClient", "userTask", "Собрать маркированный товар", *c["pick"]),
    ("Task_Check2d", "serviceTask", "Проверить остаток срока годности", *c["check"]),
    ("Gateway_Shelf", "exclusiveGateway", "Остаток срока не менее 2 суток?", *c["gw_shelf"]),
    ("Task_Reserve", "serviceTask", "Зарезервировать КИЗ", *c["reserve"]),
    ("Gateway_Extend", "exclusiveGateway", "Продлевают резерв?", *c["gw_ext"]),
    ("Task_CheckExt", "serviceTask", "Проверить срок на новую дату резерва", *c["check_ext"]),
    ("Gateway_ExtOk", "exclusiveGateway", "Срок покрывает продление?", *c["gw_ext_ok"]),
    ("Task_DoExt", "serviceTask", "Продлить резерв", *c["do_ext"]),
    ("Gateway_ExtJoin", "exclusiveGateway", "", *c["join_ext"]),
    ("Task_CheckPay", "serviceTask", "Проверить срок при оплате", *c["check_pay"]),
    ("Gateway_Pay", "exclusiveGateway", "КИЗ годен на кассе?", *c["gw_pay"]),
    ("Task_Receipt", "userTask", "Пробить чек и вывести КИЗ", *c["receipt"]),
    ("EndEvent_ClientOk", "endEvent", "Продажа клиенту выполнена", *c["end_ok"]),
    ("Task_MsgBlock", "serviceTask", "Сообщить и заблокировать КИЗ", *c["msg_block"]),
    ("Task_Repick", "userTask", "Подобрать другой товар", *c["repick"]),
    ("Task_NoExt", "serviceTask", "Не продлевать, вывести сообщение", *c["no_ext"]),
    ("Task_RepickExt", "userTask", "Подобрать другой товар", *c["repick_ext"]),
    ("Task_BlockSale", "userTask", "Заблокировать продажу", *c["block_sale"]),
    ("EndEvent_ClientCancel", "endEvent", "Продажа отменена", *c["end_cancel"]),
    # STO
    ("Task_PlanDate", "userTask", "Зафиксировать дату выдачи авто", *s["plan"]),
    ("Task_PickSto", "userTask", "Собрать товар отдельной позицией", *s["pick"]),
    ("Task_CheckPlan", "serviceTask", "Проверить срок до даты выдачи", *s["check"]),
    ("Gateway_PlanOk", "exclusiveGateway", "Срок покрывает выдачу + 2 суток?", *s["gw_plan"]),
    ("Task_ReserveSto", "serviceTask", "Зарезервировать КИЗ", *s["reserve"]),
    ("Task_Install", "userTask", "Установить / залить товар", *s["install"]),
    ("Gateway_Shift", "exclusiveGateway", "Дату выдачи авто перенесли?", *s["gw_shift"]),
    ("Task_ReceiptSto", "userTask", "Пробить отдельный товарный чек", *s["receipt"]),
    ("EndEvent_StoOk", "endEvent", "Продажа на СТО выполнена", *s["end_ok"]),
    ("Task_MsgOther", "serviceTask", "Сообщить: другой срок годности", *s["msg_other"]),
    ("Task_RepickSto", "userTask", "Подобрать другой товар", *s["repick"]),
    ("Gateway_Installed", "exclusiveGateway", "Товар уже установлен?", *s["gw_inst"]),
    ("Task_RepickDate", "userTask", "Подобрать КИЗ под новую дату", *s["repick_date"]),
    ("Task_ReceiptNow", "userTask", "Пробить товарный чек сразу", *s["receipt_now"]),
    ("EndEvent_StoEarly", "endEvent", "КИЗ выведен до выдачи авто", *s["end_early"]),
]

node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}

# flows: id, source, target, name, waypoints list of (x,y)
flows = []


def add_flow(fid, src, tgt, name, waypoints):
    flows.append((fid, src, tgt, name, waypoints))


def lr(src, tgt):
    """Left-to-right between boxes."""
    a, b = node_box[src], node_box[tgt]
    return [right(a), left(b)]


def down(src, tgt):
    a, b = node_box[src], node_box[tgt]
    x1, y1 = bottom(a)
    x2, y2 = top(b)
    return [(x1, y1), (x1, y2), (x2, y2)] if abs(x1 - x2) > 1 else [(x1, y1), (x2, y2)]


def up(src, tgt):
    a, b = node_box[src], node_box[tgt]
    x1, y1 = top(a)
    x2, y2 = bottom(b)
    return [(x1, y1), (x1, y2), (x2, y2)] if abs(x1 - x2) > 1 else [(x1, y1), (x2, y2)]


# start -> channel
add_flow("Flow_start", "StartEvent_1", "Gateway_Channel", "", lr("StartEvent_1", "Gateway_Channel"))

# channel to client: right then up then right
a, b = node_box["Gateway_Channel"], node_box["Task_CreateOrder"]
sx, sy = right(a)
tx, ty = left(b)
add_flow(
    "Flow_to_client",
    "Gateway_Channel",
    "Task_CreateOrder",
    "Заказ клиенту",
    [(sx, sy), (sx + 40, sy), (sx + 40, ty), (tx, ty)],
)

# channel to STO
a, b = node_box["Gateway_Channel"], node_box["Task_PlanDate"]
sx, sy = right(a)
tx, ty = left(b)
add_flow(
    "Flow_to_sto",
    "Gateway_Channel",
    "Task_PlanDate",
    "Продажа на СТО",
    [(sx, sy), (sx + 40, sy), (sx + 40, ty), (tx, ty)],
)

# client happy
add_flow("Flow_c1", "Task_CreateOrder", "Task_PickClient", "", lr("Task_CreateOrder", "Task_PickClient"))
add_flow("Flow_c2", "Task_PickClient", "Task_Check2d", "", lr("Task_PickClient", "Task_Check2d"))
add_flow("Flow_c3", "Task_Check2d", "Gateway_Shelf", "", lr("Task_Check2d", "Gateway_Shelf"))
add_flow("Flow_c_shelf_yes", "Gateway_Shelf", "Task_Reserve", "Да", lr("Gateway_Shelf", "Task_Reserve"))
add_flow("Flow_c4", "Task_Reserve", "Gateway_Extend", "", lr("Task_Reserve", "Gateway_Extend"))
add_flow("Flow_c_ext_yes", "Gateway_Extend", "Task_CheckExt", "Да", lr("Gateway_Extend", "Task_CheckExt"))
add_flow("Flow_c5", "Task_CheckExt", "Gateway_ExtOk", "", lr("Task_CheckExt", "Gateway_ExtOk"))
add_flow("Flow_c_extok_yes", "Gateway_ExtOk", "Task_DoExt", "Да", lr("Gateway_ExtOk", "Task_DoExt"))
add_flow("Flow_c6", "Task_DoExt", "Gateway_ExtJoin", "", lr("Task_DoExt", "Gateway_ExtJoin"))

# skip extension: from GW_EXTEND Нет down then right then up to join
a, b = node_box["Gateway_Extend"], node_box["Gateway_ExtJoin"]
x1, y1 = bottom(a)
x2, y2 = bottom(b)
add_flow(
    "Flow_c_ext_no",
    "Gateway_Extend",
    "Gateway_ExtJoin",
    "Нет",
    [(x1, y1), (x1, y1 + 28), (x2, y2 + 28), (x2, y2)],
)

add_flow("Flow_c7", "Gateway_ExtJoin", "Task_CheckPay", "", lr("Gateway_ExtJoin", "Task_CheckPay"))
add_flow("Flow_c8", "Task_CheckPay", "Gateway_Pay", "", lr("Task_CheckPay", "Gateway_Pay"))
add_flow("Flow_c_pay_yes", "Gateway_Pay", "Task_Receipt", "Да", lr("Gateway_Pay", "Task_Receipt"))
add_flow("Flow_c9", "Task_Receipt", "EndEvent_ClientOk", "", lr("Task_Receipt", "EndEvent_ClientOk"))

# client exceptions
add_flow("Flow_c_shelf_no", "Gateway_Shelf", "Task_MsgBlock", "Нет", down("Gateway_Shelf", "Task_MsgBlock"))
a, b = node_box["Task_MsgBlock"], node_box["Task_Repick"]
add_flow("Flow_c10b", "Task_MsgBlock", "Task_Repick", "", [left(a), right(b)])

# repick back to check: up
a, b = node_box["Task_Repick"], node_box["Task_Check2d"]
add_flow(
    "Flow_c_loop_shelf",
    "Task_Repick",
    "Task_Check2d",
    "Повторная сборка",
    [top(a), (top(a)[0], bottom(b)[1]), bottom(b)],
)

# extension fail
add_flow("Flow_c_extok_no", "Gateway_ExtOk", "Task_NoExt", "Нет", down("Gateway_ExtOk", "Task_NoExt"))
a, b = node_box["Task_NoExt"], node_box["Task_RepickExt"]
add_flow("Flow_c11", "Task_NoExt", "Task_RepickExt", "", [left(a), right(b)])
a, b = node_box["Task_RepickExt"], node_box["Task_Check2d"]
# go left along exception row then up to check
x_mid = node_box["Task_Check2d"][0] + W_TASK / 2
add_flow(
    "Flow_c_loop_ext",
    "Task_RepickExt",
    "Task_Check2d",
    "Повторная сборка",
    [
        left(a),
        (node_box["Task_Repick"][0] - 20, left(a)[1]),
        (node_box["Task_Repick"][0] - 20, Y_C + H_TASK + 10),
        (x_mid, Y_C + H_TASK + 10),
        bottom(b),
    ],
)

add_flow("Flow_c_pay_no", "Gateway_Pay", "Task_BlockSale", "Нет", down("Gateway_Pay", "Task_BlockSale"))
add_flow("Flow_c12", "Task_BlockSale", "EndEvent_ClientCancel", "", lr("Task_BlockSale", "EndEvent_ClientCancel"))

# STO happy
add_flow("Flow_s1", "Task_PlanDate", "Task_PickSto", "", lr("Task_PlanDate", "Task_PickSto"))
add_flow("Flow_s2", "Task_PickSto", "Task_CheckPlan", "", lr("Task_PickSto", "Task_CheckPlan"))
add_flow("Flow_s3", "Task_CheckPlan", "Gateway_PlanOk", "", lr("Task_CheckPlan", "Gateway_PlanOk"))
add_flow("Flow_s_yes", "Gateway_PlanOk", "Task_ReserveSto", "Да", lr("Gateway_PlanOk", "Task_ReserveSto"))
add_flow("Flow_s4", "Task_ReserveSto", "Task_Install", "", lr("Task_ReserveSto", "Task_Install"))
add_flow("Flow_s5", "Task_Install", "Gateway_Shift", "", lr("Task_Install", "Gateway_Shift"))
add_flow("Flow_s_shift_no", "Gateway_Shift", "Task_ReceiptSto", "Нет", lr("Gateway_Shift", "Task_ReceiptSto"))
add_flow("Flow_s6", "Task_ReceiptSto", "EndEvent_StoOk", "", lr("Task_ReceiptSto", "EndEvent_StoOk"))

# STO exceptions
add_flow("Flow_s_plan_no", "Gateway_PlanOk", "Task_MsgOther", "Нет", down("Gateway_PlanOk", "Task_MsgOther"))
a, b = node_box["Task_MsgOther"], node_box["Task_RepickSto"]
add_flow("Flow_s7", "Task_MsgOther", "Task_RepickSto", "", [left(a), right(b)])
a, b = node_box["Task_RepickSto"], node_box["Task_CheckPlan"]
add_flow(
    "Flow_s_loop",
    "Task_RepickSto",
    "Task_CheckPlan",
    "Повторная сборка",
    [top(a), (top(a)[0], bottom(b)[1]), bottom(b)],
)

add_flow("Flow_s_shift_yes", "Gateway_Shift", "Gateway_Installed", "Да", down("Gateway_Shift", "Gateway_Installed"))
a, b = node_box["Gateway_Installed"], node_box["Task_RepickDate"]
add_flow(
    "Flow_s_inst_no",
    "Gateway_Installed",
    "Task_RepickDate",
    "Нет",
    [left(a), right(b)],
)
a, b = node_box["Task_RepickDate"], node_box["Task_CheckPlan"]
add_flow(
    "Flow_s_loop_date",
    "Task_RepickDate",
    "Task_CheckPlan",
    "Повторная проверка",
    [
        left(a),
        (node_box["Task_RepickSto"][0] - 20, left(a)[1]),
        (node_box["Task_RepickSto"][0] - 20, Y_S + H_TASK + 10),
        (node_box["Task_CheckPlan"][0] + W_TASK / 2, Y_S + H_TASK + 10),
        bottom(node_box["Task_CheckPlan"]),
    ],
)

add_flow("Flow_s_inst_yes", "Gateway_Installed", "Task_ReceiptNow", "Да", lr("Gateway_Installed", "Task_ReceiptNow"))
add_flow("Flow_s8", "Task_ReceiptNow", "EndEvent_StoEarly", "", lr("Task_ReceiptNow", "EndEvent_StoEarly"))


def waypoints_xml(points):
    parts = []
    for x, y in points:
        parts.append(f'          <di:waypoint x="{x:.1f}" y="{y:.1f}" />')
    return "\n".join(parts)


def shape(eid, x, y, w, h, extra=""):
    return f'''      <bpmndi:BPMNShape id="{eid}_di" bpmnElement="{eid}"{extra}>
        <dc:Bounds x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" />
      </bpmndi:BPMNShape>'''


def label_bounds_for_flow(points, name):
    if not name:
        return ""
    mx = sum(p[0] for p in points) / len(points)
    my = min(p[1] for p in points) - 18
    w = max(80, min(220, 8 * len(name) + 16))
    return f'''
        <bpmndi:BPMNLabel>
          <dc:Bounds x="{mx - w/2:.1f}" y="{my:.1f}" width="{w:.1f}" height="16" />
        </bpmndi:BPMNLabel>'''


elements_xml = []
for eid, etype, name, x, y, w, h in nodes:
    extra = ""
    if etype == "exclusiveGateway":
        extra = ' gatewayDirection="Diverging"'
        if eid in ("Gateway_ExtJoin",):
            extra = ' gatewayDirection="Converging"'
    name_attr = f' name="{escape(name)}"' if name else ""
    elements_xml.append(
        f'    <bpmn:{etype} id="{eid}"{name_attr}{extra} />'
    )

# incoming/outgoing are optional in BPMN; Storm/Camunda work without them if flows exist

seq_xml = []
for fid, src, tgt, name, _ in flows:
    nm = f' name="{escape(name)}"' if name else ""
    seq_xml.append(
        f'    <bpmn:sequenceFlow id="{fid}" sourceRef="{src}" targetRef="{tgt}"{nm} />'
    )

shapes = []
for eid, etype, name, x, y, w, h in nodes:
    extra = ""
    if etype == "exclusiveGateway":
        extra = ' isMarkerVisible="true"'
    shapes.append(shape(eid, x, y, w, h, extra))

# groups
shapes.append(
    '''      <bpmndi:BPMNShape id="Group_Client_di" bpmnElement="Group_Client">
        <dc:Bounds x="370.0" y="70.0" width="2140.0" height="340.0" />
      </bpmndi:BPMNShape>'''
)
shapes.append(
    '''      <bpmndi:BPMNShape id="Group_Sto_di" bpmnElement="Group_Sto">
        <dc:Bounds x="370.0" y="500.0" width="1480.0" height="340.0" />
      </bpmndi:BPMNShape>'''
)

edges = []
for fid, src, tgt, name, pts in flows:
    lab = label_bounds_for_flow(pts, name)
    edges.append(
        f'''      <bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">
{waypoints_xml(pts)}{lab}
      </bpmndi:BPMNEdge>'''
    )

xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  id="Definitions_SrokGodnosti"
                  name="Контроль срока годности маркированного товара"
                  targetNamespace="http://bpmn.io/schema/bpmn"
                  exporter="StormBPMN compatible"
                  exporterVersion="1.0">
  <bpmn:category id="Category_1">
    <bpmn:categoryValue id="CategoryValue_Client" value="Заказ клиенту (резерв 24ч)"/>
    <bpmn:categoryValue id="CategoryValue_Sto" value="Продажа на СТО (отдельный товарный чек)"/>
  </bpmn:category>
  <bpmn:process id="Process_SrokGodnosti" name="Контроль срока годности КИЗ" isExecutable="false">
    <bpmn:documentation>Правило: срок годности проверяется к дате передачи товара, а не к дате сборки.
Заказ клиенту: на сборке остаток срока не менее 2 суток; продление резерва только если срок покрывает новую дату; на кассе повторная проверка, КИЗ выводится в чеке оплаты.
СТО: товар отдельным чеком, не в услуге. На сборке срок должен покрывать плановую выдачу авто + 2 суток. Если дату выдачи сдвинули и товар ещё не установлен — подобрать другой КИЗ. Если уже залили/установили — пробить товарный чек сразу, не ждать выдачи авто.</bpmn:documentation>
    <bpmn:group id="Group_Client" categoryValueRef="CategoryValue_Client"/>
    <bpmn:group id="Group_Sto" categoryValueRef="CategoryValue_Sto"/>
{chr(10).join(elements_xml)}
{chr(10).join(seq_xml)}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1" name="Контроль срока годности маркированного товара">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_SrokGodnosti">
{chr(10).join(shapes)}
{chr(10).join(edges)}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
'''

out = "/workspace/docs/stormbpmn/kontrol-sroka-godnosti-kiz.bpmn"
with open(out, "w", encoding="utf-8") as f:
    f.write(xml)
print(f"Wrote {out} ({len(nodes)} nodes, {len(flows)} flows)")


def wrap(text, width=18):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def svg_text_lines(lines, cx, cy, size=10):
    h = size + 2
    start = cy - (len(lines) - 1) * h / 2
    parts = []
    for i, line in enumerate(lines):
        parts.append(
            f'<text x="{cx:.1f}" y="{start + i * h:.1f}" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="Arial, sans-serif" '
            f'font-size="{size}">{escape(line)}</text>'
        )
    return "\n".join(parts)


svg_parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2640 920" width="2640" height="920">',
    '<rect width="2640" height="920" fill="#f7f8fa"/>',
    '<text x="1320" y="36" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700">Контроль срока годности маркированного товара</text>',
    '<rect x="370" y="70" width="2140" height="340" rx="8" fill="#eef6ff" stroke="#5b8def" stroke-dasharray="6 4"/>',
    '<text x="390" y="92" font-family="Arial, sans-serif" font-size="13" fill="#2b5cb8" font-weight="700">Заказ клиенту (резерв 24ч)</text>',
    '<rect x="370" y="500" width="1480" height="340" rx="8" fill="#eefaf3" stroke="#3ca06a" stroke-dasharray="6 4"/>',
    '<text x="390" y="522" font-family="Arial, sans-serif" font-size="13" fill="#237a4b" font-weight="700">Продажа на СТО (отдельный товарный чек, не услуга)</text>',
    '<defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#4a5568"/></marker></defs>',
]

for fid, src, tgt, name, pts in flows:
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    svg_parts.append(
        f'<path d="{d}" fill="none" stroke="#4a5568" stroke-width="1.6" marker-end="url(#arrow)"/>'
    )
    if name:
        mx = sum(p[0] for p in pts) / len(pts)
        my = min(p[1] for p in pts) - 8
        svg_parts.append(
            f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#1a365d">{escape(name)}</text>'
        )

for eid, etype, name, x, y, w, h in nodes:
    cx_, cy_ = x + w / 2, y + h / 2
    if etype == "startEvent":
        svg_parts.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="18" fill="#d1fae5" stroke="#059669" stroke-width="3"/>')
        svg_parts.append(svg_text_lines([name], cx_, y + h + 12, 11))
    elif etype == "endEvent":
        svg_parts.append(f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="18" fill="#fee2e2" stroke="#b91c1c" stroke-width="5"/>')
        svg_parts.append(svg_text_lines(wrap(name, 16), cx_, y + h + 14, 10))
    elif etype == "exclusiveGateway":
        svg_parts.append(
            f'<polygon points="{cx_:.1f},{y:.1f} {x+w:.1f},{cy_:.1f} {cx_:.1f},{y+h:.1f} {x:.1f},{cy_:.1f}" fill="#fff7ed" stroke="#c2410c" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<text x="{cx_:.1f}" y="{cy_:.1f}" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif" font-size="16" fill="#9a3412">×</text>'
        )
        if name:
            svg_parts.append(svg_text_lines(wrap(name, 18), cx_, y - 16, 10))
    else:
        fill = "#dbeafe" if etype == "serviceTask" else "#fef3c7"
        stroke = "#1d4ed8" if etype == "serviceTask" else "#b45309"
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        svg_parts.append(svg_text_lines(wrap(name, 18), cx_, cy_, 11))

svg_parts.append(
    '<text x="80" y="890" font-family="Arial, sans-serif" font-size="12" fill="#4a5568">'
    "Синие задачи — система. Жёлтые — сотрудник. КИЗ выводится только в товарном чеке на кассе.</text>"
)
svg_parts.append("</svg>")

svg_out = "/workspace/docs/stormbpmn/kontrol-sroka-godnosti-kiz.svg"
with open(svg_out, "w", encoding="utf-8") as f:
    f.write("\n".join(svg_parts))
print(f"Wrote {svg_out}")

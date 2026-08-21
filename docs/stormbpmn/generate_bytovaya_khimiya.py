#!/usr/bin/env python3
"""Generate StormBPMN-compatible BPMN 2.0 and SVG for household chemicals dual-SKU."""

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


def box_cx(b):
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
    w = max(70, min(240, 8 * len(name) + 16))
    return f'''
        <bpmndi:BPMNLabel>
          <dc:Bounds x="{mx - w / 2:.1f}" y="{my:.1f}" width="{w:.1f}" height="16" />
        </bpmndi:BPMNLabel>'''


def write_bpmn(path, defs_id, defs_name, process_id, process_name, documentation, nodes, flows, groups, converging):
    node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}
    elements_xml = []
    for eid, etype, name, x, y, w, h in nodes:
        extra = ""
        if etype == "exclusiveGateway":
            extra = (
                ' gatewayDirection="Converging"'
                if eid in converging
                else ' gatewayDirection="Diverging"'
            )
        elif etype == "parallelGateway":
            extra = (
                ' gatewayDirection="Converging"'
                if eid in converging
                else ' gatewayDirection="Diverging"'
            )
        name_attr = f' name="{escape(name)}"' if name else ""
        elements_xml.append(f'    <bpmn:{etype} id="{eid}"{name_attr}{extra} />')

    seq_xml = []
    for fid, src, tgt, name, _ in flows:
        nm = f' name="{escape(name)}"' if name else ""
        seq_xml.append(
            f'    <bpmn:sequenceFlow id="{fid}" sourceRef="{src}" targetRef="{tgt}"{nm} />'
        )

    cat_xml = []
    group_xml = []
    group_shapes = []
    if groups:
        cat_vals = []
        for gid, cid, value, gx, gy, gw_, gh_ in groups:
            cat_vals.append(f'    <bpmn:categoryValue id="{cid}" value="{escape(value)}"/>')
            group_xml.append(f'    <bpmn:group id="{gid}" categoryValueRef="{cid}"/>')
            group_shapes.append(
                f'''      <bpmndi:BPMNShape id="{gid}_di" bpmnElement="{gid}">
        <dc:Bounds x="{gx:.1f}" y="{gy:.1f}" width="{gw_:.1f}" height="{gh_:.1f}" />
      </bpmndi:BPMNShape>'''
            )
        cat_xml = [
            '  <bpmn:category id="Category_1">',
            *cat_vals,
            "  </bpmn:category>",
        ]

    shapes = []
    for eid, etype, name, x, y, w, h in nodes:
        extra = ""
        if etype in ("exclusiveGateway", "parallelGateway"):
            extra = ' isMarkerVisible="true"'
        shapes.append(shape(eid, x, y, w, h, extra))

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
                  id="{defs_id}"
                  name="{escape(defs_name)}"
                  targetNamespace="http://bpmn.io/schema/bpmn"
                  exporter="StormBPMN compatible"
                  exporterVersion="1.0">
{chr(10).join(cat_xml)}
  <bpmn:process id="{process_id}" name="{escape(process_name)}" isExecutable="false">
    <bpmn:documentation>{escape(documentation)}</bpmn:documentation>
{chr(10).join(group_xml)}
{chr(10).join(elements_xml)}
{chr(10).join(seq_xml)}
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1" name="{escape(defs_name)}">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="{process_id}">
{chr(10).join(shapes + group_shapes)}
{chr(10).join(edges)}
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"Wrote {path} ({len(nodes)} nodes, {len(flows)} flows)")
    return node_box


def write_svg(path, title, width, height, nodes, flows, group_rects, footer):
    svg_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#f7f8fa"/>',
        f'<text x="{width / 2:.1f}" y="36" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700">{escape(title)}</text>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#4a5568"/></marker></defs>',
    ]
    for gx, gy, gw_, gh_, fill, stroke, label, lx, ly, lfill in group_rects:
        svg_parts.append(
            f'<rect x="{gx}" y="{gy}" width="{gw_}" height="{gh_}" rx="8" fill="{fill}" stroke="{stroke}" stroke-dasharray="6 4"/>'
        )
        svg_parts.append(
            f'<text x="{lx}" y="{ly}" font-family="Arial, sans-serif" font-size="13" fill="{lfill}" font-weight="700">{escape(label)}</text>'
        )

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
            svg_parts.append(
                f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="18" fill="#d1fae5" stroke="#059669" stroke-width="3"/>'
            )
            svg_parts.append(svg_text_lines([name], cx_, y + h + 12, 11))
        elif etype == "endEvent":
            svg_parts.append(
                f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="18" fill="#fee2e2" stroke="#b91c1c" stroke-width="5"/>'
            )
            svg_parts.append(svg_text_lines(wrap(name, 16), cx_, y + h + 14, 10))
        elif etype in ("exclusiveGateway", "parallelGateway"):
            svg_parts.append(
                f'<polygon points="{cx_:.1f},{y:.1f} {x + w:.1f},{cy_:.1f} {cx_:.1f},{y + h:.1f} {x:.1f},{cy_:.1f}" fill="#fff7ed" stroke="#c2410c" stroke-width="2"/>'
            )
            mark = "+" if etype == "parallelGateway" else "×"
            svg_parts.append(
                f'<text x="{cx_:.1f}" y="{cy_:.1f}" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif" font-size="16" fill="#9a3412">{mark}</text>'
            )
            if name:
                svg_parts.append(svg_text_lines(wrap(name, 18), cx_, y - 16, 10))
        else:
            fill = "#dbeafe" if etype == "serviceTask" else "#fef3c7"
            stroke = "#1d4ed8" if etype == "serviceTask" else "#b45309"
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
            )
            svg_parts.append(svg_text_lines(wrap(name, 18), cx_, cy_, 11))

    svg_parts.append(
        f'<text x="40" y="{height - 18}" font-family="Arial, sans-serif" font-size="12" fill="#4a5568">{escape(footer)}</text>'
    )
    svg_parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_parts))
    print(f"Wrote {path}")


def lr(node_box, src, tgt):
    return [right(node_box[src]), left(node_box[tgt])]


def build_priemka():
    Y_M, Y, Y_U, Y_Q = 80, 260, 440, 620

    start = ev(40, Y)
    open_ = task(140, Y)
    scan = task(340, Y)
    gw_dm = gw(540, Y)
    to_m = task(640, Y_M)
    gw_date = gw(640, Y_U)
    to_u = task(820, Y_U)
    quar = task(820, Y_Q)
    end_q = ev(1040, Y_Q)
    gw_more = gw(1080, Y)
    gw_mix = gw(1280, Y)
    inv_m = task(1440, Y_M)
    inv_u = task(1440, Y)
    inv_2 = task(1440, Y_U)
    utd = task(1660, Y_M)
    plain = task(1660, Y)
    utd2 = task(1660, Y_U)
    plain2 = task(1880, Y_U)
    end_ok = ev(2140, Y)

    nodes = [
        ("StartEvent_1", "startEvent", "Старт", *start),
        ("Task_Open", "userTask", "Открыть поставку поставщика", *open_),
        ("Task_Scan", "userTask", "Отсканировать каждую единицу 2D", *scan),
        ("Gateway_DM", "exclusiveGateway", "На упаковке Data Matrix?", *gw_dm),
        ("Task_ToMarked", "serviceTask", "В буфер артикула-М", *to_m),
        ("Gateway_Date", "exclusiveGateway", "Дата производства до контрольной?", *gw_date),
        ("Task_ToUnmarked", "serviceTask", "В буфер артикула-остатка", *to_u),
        ("Task_Quarantine", "userTask", "Карантин, возврат поставщику", *quar),
        ("EndEvent_Quarantine", "endEvent", "Поставка отклонена", *end_q),
        ("Gateway_More", "exclusiveGateway", "Есть ещё единицы?", *gw_more),
        ("Gateway_Mix", "exclusiveGateway", "В поставке оба статуса?", *gw_mix),
        ("Task_InvM", "serviceTask", "Одна накладная: только маркированный", *inv_m),
        ("Task_InvU", "serviceTask", "Одна накладная: только остаток", *inv_u),
        ("Task_Inv2", "serviceTask", "Две однородные накладные", *inv_2),
        ("Task_UTD", "userTask", "Подписать УПД ЭДО GTIN + количество", *utd),
        ("Task_Plain", "userTask", "Принять остаток без Честного знака", *plain),
        ("Task_UTD2", "userTask", "Подписать УПД ЭДО по маркированным", *utd2),
        ("Task_Plain2", "userTask", "Принять остаток отдельной накладной", *plain2),
        ("EndEvent_Ok", "endEvent", "Приёмка закрыта", *end_ok),
    ]
    node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}
    flows = []

    def add(fid, src, tgt, name, pts):
        flows.append((fid, src, tgt, name, pts))

    add("Flow_s1", "StartEvent_1", "Task_Open", "", lr(node_box, "StartEvent_1", "Task_Open"))
    add("Flow_s2", "Task_Open", "Task_Scan", "", lr(node_box, "Task_Open", "Task_Scan"))
    add("Flow_s3", "Task_Scan", "Gateway_DM", "", lr(node_box, "Task_Scan", "Gateway_DM"))

    a, b = node_box["Gateway_DM"], node_box["Task_ToMarked"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_dm_yes", "Gateway_DM", "Task_ToMarked", "Да, КИЗ", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])

    a, b = node_box["Gateway_DM"], node_box["Gateway_Date"]
    sx, sy = bottom(a)
    tx, ty = top(b)
    add("Flow_dm_no", "Gateway_DM", "Gateway_Date", "Нет кода", [(sx, sy), (tx, ty)])

    add("Flow_date_yes", "Gateway_Date", "Task_ToUnmarked", "Да, остаток", lr(node_box, "Gateway_Date", "Task_ToUnmarked"))
    add("Flow_date_no", "Gateway_Date", "Task_Quarantine", "Нет, после даты", [bottom(node_box["Gateway_Date"]), top(node_box["Task_Quarantine"])])
    add("Flow_q1", "Task_Quarantine", "EndEvent_Quarantine", "", lr(node_box, "Task_Quarantine", "EndEvent_Quarantine"))

    a, b = node_box["Task_ToMarked"], node_box["Gateway_More"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_m_more", "Task_ToMarked", "Gateway_More", "", [(sx, sy), (tx, sy), (tx, ty)])

    a, b = node_box["Task_ToUnmarked"], node_box["Gateway_More"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_u_more", "Task_ToUnmarked", "Gateway_More", "", [(sx, sy), (tx, sy), (tx, ty)])

    a, b = node_box["Gateway_More"], node_box["Task_Scan"]
    x1, y1 = top(a)
    x2, y2 = top(b)
    add(
        "Flow_loop",
        "Gateway_More",
        "Task_Scan",
        "Да",
        [(x1, y1), (x1, y1 - 52), (x2, y2 - 52), (x2, y2)],
    )
    add("Flow_no_more", "Gateway_More", "Gateway_Mix", "Нет", lr(node_box, "Gateway_More", "Gateway_Mix"))

    a, b = node_box["Gateway_Mix"], node_box["Task_InvM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_only_m", "Gateway_Mix", "Task_InvM", "Только маркированный", [(sx, sy), (sx + 28, sy), (sx + 28, ty), (tx, ty)])
    add("Flow_only_u", "Gateway_Mix", "Task_InvU", "Только остаток", lr(node_box, "Gateway_Mix", "Task_InvU"))
    a, b = node_box["Gateway_Mix"], node_box["Task_Inv2"]
    sx, sy = bottom(a)
    tx, ty = left(b)
    add("Flow_both", "Gateway_Mix", "Task_Inv2", "Оба, как 5 канистр", [(sx, sy), (sx, ty), (tx, ty)])

    add("Flow_utm", "Task_InvM", "Task_UTD", "", lr(node_box, "Task_InvM", "Task_UTD"))
    add("Flow_upu", "Task_InvU", "Task_Plain", "", lr(node_box, "Task_InvU", "Task_Plain"))
    add("Flow_u2", "Task_Inv2", "Task_UTD2", "", lr(node_box, "Task_Inv2", "Task_UTD2"))
    add("Flow_p2", "Task_UTD2", "Task_Plain2", "", lr(node_box, "Task_UTD2", "Task_Plain2"))

    a, b = node_box["Task_UTD"], node_box["EndEvent_Ok"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_end_m", "Task_UTD", "EndEvent_Ok", "", [(sx, sy), (tx, sy), (tx, ty)])
    add("Flow_end_u", "Task_Plain", "EndEvent_Ok", "", lr(node_box, "Task_Plain", "EndEvent_Ok"))
    a, b = node_box["Task_Plain2"], node_box["EndEvent_Ok"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_end_2", "Task_Plain2", "EndEvent_Ok", "", [(sx, sy), (tx, sy), (tx, ty)])

    groups = [
        ("Group_Scan", "CategoryValue_Scan", "Скан классифицирует единицу", 120, 50, 1120, 560),
        ("Group_Docs", "CategoryValue_Docs", "Накладные всегда однородные", 1400, 50, 700, 560),
    ]
    doc = (
        "Один артикул не бывает маркированным и немаркированным сразу. "
        "Скан Data Matrix кладёт единицу на артикул-М, отсутствие кода и дата до контрольной — на артикул-остаток. "
        "Смешанная поставка (3 канистры с КИЗ и 2 без) режется на две однородные накладные. "
        "Маркированный приход закрывается УПД ЭДО в ОСУ (GTIN + количество). Законный остаток в Честный знак не передаётся."
    )
    write_bpmn(
        "/workspace/docs/stormbpmn/priemka-smeshannoj-postavki.bpmn",
        "Definitions_PriemkaHimii",
        "Приёмка смешанной поставки бытовой химии",
        "Process_PriemkaHimii",
        "Приёмка смешанной поставки",
        doc,
        nodes,
        flows,
        groups,
        {"Gateway_More", "EndEvent_Ok"},
    )
    write_svg(
        "/workspace/docs/stormbpmn/priemka-smeshannoj-postavki.svg",
        "Приёмка смешанной поставки: 3 канистры с КИЗ и 2 без кода",
        2360,
        760,
        nodes,
        flows,
        [
            (120, 50, 1120, 560, "#eef6ff", "#5b8def", "Скан классифицирует каждую единицу", 140, 72, "#2b5cb8"),
            (1400, 50, 700, 560, "#eefaf3", "#3ca06a", "Накладные однородные: одна или две", 1420, 72, "#237a4b"),
        ],
        "Синие задачи — система. Жёлтые — сотрудник. Смешивать статусы в одной накладной нельзя. В кассовом чеке — можно.",
    )


def build_outbound():
    Y_A, Y_C, Y_S = 90, 430, 770
    start = ev(40, 430)
    channel = gw(140, 430)

    # assembly
    a_open = task(360, Y_A)
    a_scan = task(560, Y_A)
    a_dm = gw(760, Y_A)
    a_m = task(860, 20)
    a_u = task(860, 160)
    a_more = gw(1080, Y_A)
    a_mix = gw(1240, Y_A)
    a_one = task(1400, 20)
    a_two = task(1400, 160)
    a_end = ev(1640, Y_A)

    # cash
    c_scan = task(360, Y_C)
    c_dm = gw(560, Y_C)
    c_m = task(660, 360)
    c_u = task(660, 500)
    c_more = gw(880, Y_C)
    c_check = task(1040, Y_C)
    c_post = task(1260, Y_C)
    c_end = ev(1500, Y_C)

    # sto
    s_scan = task(360, Y_S)
    s_dm = gw(560, Y_S)
    s_kind_m = gw(720, 700)
    s_kind_u = gw(720, 840)
    s_sale_m = task(880, 640)
    s_use_m = task(880, 740)
    s_sale_u = task(880, 840)
    s_use_u = task(880, 940)
    s_end = ev(1140, Y_S)

    nodes = [
        ("StartEvent_1", "startEvent", "Старт", *start),
        ("Gateway_Channel", "exclusiveGateway", "Какая операция?", *channel),
        ("Task_AOpen", "serviceTask", "Показать остатки обоих двойников", *a_open),
        ("Task_AScan", "userTask", "Сканировать единицу на сборке", *a_scan),
        ("Gateway_ADM", "exclusiveGateway", "Data Matrix?", *a_dm),
        ("Task_AM", "serviceTask", "Строка артикула-М, сначала остаток FIFO", *a_m),
        ("Task_AU", "serviceTask", "Строка артикула-остатка", *a_u),
        ("Gateway_AMore", "exclusiveGateway", "Ещё единицы?", *a_more),
        ("Gateway_AMix", "exclusiveGateway", "В сборке оба статуса?", *a_mix),
        ("Task_AOne", "serviceTask", "Одна расходная накладная", *a_one),
        ("Task_ATwo", "serviceTask", "Две однородные накладные", *a_two),
        ("EndEvent_A", "endEvent", "Сборка закрыта", *a_end),
        ("Task_CScan", "userTask", "Сканировать товар на кассе", *c_scan),
        ("Gateway_CDM", "exclusiveGateway", "Data Matrix?", *c_dm),
        ("Task_CM", "serviceTask", "Строка с КИЗ в чек", *c_m),
        ("Task_CU", "serviceTask", "Строка остатка без КИЗ", *c_u),
        ("Gateway_CMore", "exclusiveGateway", "Ещё товары?", *c_more),
        ("Task_CCheck", "userTask", "Один чек: нал или безнал", *c_check),
        ("Task_CPost", "serviceTask", "Чек режется на 1–2 складских движения", *c_post),
        ("EndEvent_C", "endEvent", "Продажа через кассу", *c_end),
        ("Task_SScan", "userTask", "Сканировать единицу под авто", *s_scan),
        ("Gateway_SDM", "exclusiveGateway", "Data Matrix?", *s_dm),
        ("Gateway_SKindM", "exclusiveGateway", "Продажа или расход в работу?", *s_kind_m),
        ("Gateway_SKindU", "exclusiveGateway", "Продажа или расход в работу?", *s_kind_u),
        ("Task_SSaleM", "userTask", "Товарный чек с КИЗ", *s_sale_m),
        ("Task_SUseM", "serviceTask", "Списание + вывод в ЧЗ ОСУ", *s_use_m),
        ("Task_SSaleU", "userTask", "Товарный чек без КИЗ", *s_sale_u),
        ("Task_SUseU", "serviceTask", "Только складское списание", *s_use_u),
        ("EndEvent_S", "endEvent", "Операция на авто закрыта", *s_end),
    ]
    node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}
    flows = []

    def add(fid, src, tgt, name, pts):
        flows.append((fid, src, tgt, name, pts))

    add("Flow_start", "StartEvent_1", "Gateway_Channel", "", lr(node_box, "StartEvent_1", "Gateway_Channel"))

    a, b = node_box["Gateway_Channel"], node_box["Task_AOpen"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_to_a", "Gateway_Channel", "Task_AOpen", "Сборка", [(sx, sy), (sx + 40, sy), (sx + 40, ty), (tx, ty)])
    add("Flow_to_c", "Gateway_Channel", "Task_CScan", "Касса, нал и безнал", lr(node_box, "Gateway_Channel", "Task_CScan"))
    a, b = node_box["Gateway_Channel"], node_box["Task_SScan"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_to_s", "Gateway_Channel", "Task_SScan", "Списание на авто", [(sx, sy), (sx + 40, sy), (sx + 40, ty), (tx, ty)])

    add("Flow_a1", "Task_AOpen", "Task_AScan", "", lr(node_box, "Task_AOpen", "Task_AScan"))
    add("Flow_a2", "Task_AScan", "Gateway_ADM", "", lr(node_box, "Task_AScan", "Gateway_ADM"))
    a, b = node_box["Gateway_ADM"], node_box["Task_AM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_a_m", "Gateway_ADM", "Task_AM", "Да", [(sx, sy), (sx + 20, sy), (sx + 20, ty), (tx, ty)])
    a, b = node_box["Gateway_ADM"], node_box["Task_AU"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_a_u", "Gateway_ADM", "Task_AU", "Нет", [(sx, sy), (sx + 20, sy), (sx + 20, ty), (tx, ty)])

    a, b = node_box["Task_AM"], node_box["Gateway_AMore"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_am_more", "Task_AM", "Gateway_AMore", "", [(sx, sy), (tx, sy), (tx, ty)])
    a, b = node_box["Task_AU"], node_box["Gateway_AMore"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_au_more", "Task_AU", "Gateway_AMore", "", [(sx, sy), (tx, sy), (tx, ty)])

    a, b = node_box["Gateway_AMore"], node_box["Task_AScan"]
    x1, y1 = top(a)
    x2, y2 = top(b)
    add("Flow_a_loop", "Gateway_AMore", "Task_AScan", "Да", [(x1, y1), (x1, y1 - 36), (x2, y2 - 36), (x2, y2)])
    add("Flow_a_done", "Gateway_AMore", "Gateway_AMix", "Нет", lr(node_box, "Gateway_AMore", "Gateway_AMix"))

    a, b = node_box["Gateway_AMix"], node_box["Task_AOne"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_a_one", "Gateway_AMix", "Task_AOne", "Один статус", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])
    a, b = node_box["Gateway_AMix"], node_box["Task_ATwo"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_a_two", "Gateway_AMix", "Task_ATwo", "Оба статуса", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])

    a, b = node_box["Task_AOne"], node_box["EndEvent_A"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_a_end1", "Task_AOne", "EndEvent_A", "", [(sx, sy), (tx, sy), (tx, ty)])
    a, b = node_box["Task_ATwo"], node_box["EndEvent_A"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_a_end2", "Task_ATwo", "EndEvent_A", "", [(sx, sy), (tx, sy), (tx, ty)])

    add("Flow_c1", "Task_CScan", "Gateway_CDM", "", lr(node_box, "Task_CScan", "Gateway_CDM"))
    a, b = node_box["Gateway_CDM"], node_box["Task_CM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_c_m", "Gateway_CDM", "Task_CM", "Да", [(sx, sy), (sx + 20, sy), (sx + 20, ty), (tx, ty)])
    a, b = node_box["Gateway_CDM"], node_box["Task_CU"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_c_u", "Gateway_CDM", "Task_CU", "Нет", [(sx, sy), (sx + 20, sy), (sx + 20, ty), (tx, ty)])
    a, b = node_box["Task_CM"], node_box["Gateway_CMore"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_cm_more", "Task_CM", "Gateway_CMore", "", [(sx, sy), (tx, sy), (tx, ty)])
    a, b = node_box["Task_CU"], node_box["Gateway_CMore"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_cu_more", "Task_CU", "Gateway_CMore", "", [(sx, sy), (tx, sy), (tx, ty)])
    a, b = node_box["Gateway_CMore"], node_box["Task_CScan"]
    x1, y1 = top(a)
    x2, y2 = top(b)
    add("Flow_c_loop", "Gateway_CMore", "Task_CScan", "Да", [(x1, y1), (x1, y1 - 28), (x2, y2 - 28), (x2, y2)])
    add("Flow_c_done", "Gateway_CMore", "Task_CCheck", "Нет", lr(node_box, "Gateway_CMore", "Task_CCheck"))
    add("Flow_c2", "Task_CCheck", "Task_CPost", "", lr(node_box, "Task_CCheck", "Task_CPost"))
    add("Flow_c3", "Task_CPost", "EndEvent_C", "", lr(node_box, "Task_CPost", "EndEvent_C"))

    add("Flow_s1", "Task_SScan", "Gateway_SDM", "", lr(node_box, "Task_SScan", "Gateway_SDM"))
    a, b = node_box["Gateway_SDM"], node_box["Gateway_SKindM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_s_m", "Gateway_SDM", "Gateway_SKindM", "Да, маркированный", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])
    a, b = node_box["Gateway_SDM"], node_box["Gateway_SKindU"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_s_u", "Gateway_SDM", "Gateway_SKindU", "Нет, остаток", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])

    a, b = node_box["Gateway_SKindM"], node_box["Task_SSaleM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_sm_sale", "Gateway_SKindM", "Task_SSaleM", "Продажа", [(sx, sy), (sx + 16, sy), (sx + 16, ty), (tx, ty)])
    a, b = node_box["Gateway_SKindM"], node_box["Task_SUseM"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_sm_use", "Gateway_SKindM", "Task_SUseM", "Расход", [(sx, sy), (sx + 16, sy), (sx + 16, ty), (tx, ty)])
    a, b = node_box["Gateway_SKindU"], node_box["Task_SSaleU"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_su_sale", "Gateway_SKindU", "Task_SSaleU", "Продажа", [(sx, sy), (sx + 16, sy), (sx + 16, ty), (tx, ty)])
    add("Flow_su_use", "Gateway_SKindU", "Task_SUseU", "Расход", lr(node_box, "Gateway_SKindU", "Task_SUseU"))

    for src in ("Task_SSaleM", "Task_SUseM", "Task_SSaleU", "Task_SUseU"):
        a, b = node_box[src], node_box["EndEvent_S"]
        sx, sy = right(a)
        tx, ty = left(b)
        add(f"Flow_end_{src}", src, "EndEvent_S", "", [(sx, sy), (tx, sy), (tx, ty)])

    groups = [
        ("Group_A", "CategoryValue_A", "Сборка заказа", 340, 0, 1380, 280),
        ("Group_C", "CategoryValue_C", "Касса розницы и магазина запчастей", 340, 330, 1240, 280),
        ("Group_S", "CategoryValue_S", "СТО: товарный чек или расход на авто", 340, 610, 900, 430),
    ]
    doc = (
        "Сборка и складские накладные не смешивают статусы: при обоих типах единиц — две накладные. "
        "Кассовый чек с 01.07.2026 один на покупку, нал и безнал одинаковы; смешанный чек разрешён, склад режет движения. "
        "На авто маркированный расход в работу выводится в Честный знак в ОСУ без кассы; законный остаток в ЧЗ не отправляется."
    )
    write_bpmn(
        "/workspace/docs/stormbpmn/sborka-prodazha-spisanie.bpmn",
        "Definitions_OutboundHimii",
        "Сборка, продажа и списание бытовой химии",
        "Process_OutboundHimii",
        "Сборка, касса, списание на авто",
        doc,
        nodes,
        flows,
        groups,
        {"Gateway_AMore", "Gateway_CMore", "EndEvent_A", "EndEvent_S"},
    )
    write_svg(
        "/workspace/docs/stormbpmn/sborka-prodazha-spisanie.svg",
        "Сборка, продажа через кассу и списание на авто",
        1860,
        1120,
        nodes,
        flows,
        [
            (340, 0, 1380, 280, "#eef6ff", "#5b8def", "Сборка заказа: сначала остаток без кода, FIFO по сроку", 360, 22, "#2b5cb8"),
            (340, 330, 1240, 280, "#fff7ed", "#c2410c", "Касса: один чек может смешивать статусы, накладная — нет", 360, 352, "#9a3412"),
            (340, 610, 900, 430, "#eefaf3", "#3ca06a", "СТО: продажа — товарный чек; расход в работу — списание", 360, 632, "#237a4b"),
        ],
        "Синие задачи — система. Жёлтые — сотрудник. С 01.07.2026 маркированный товар выводится через кассу или отдельным выводом в ЧЗ.",
    )


def build_etap():
    Y, Y_NO, Y1, Y2, Y3 = 220, 430, 60, 220, 380
    start = ev(40, Y)
    read = task(140, Y)
    gw_ex = gw(340, Y)
    find = task(500, Y)
    skip = task(500, Y_NO)
    gw_both = gw(700, Y)
    calc = task(820, Y)
    none = task(820, Y_NO)
    gw_date = gw(1020, Y)
    t1 = task(1140, Y1)
    t2 = task(1140, Y2)
    t3 = task(1140, Y3)
    end_ok = ev(1380, Y2)
    end_no = ev(1040, Y_NO)

    nodes = [
        ("StartEvent_1", "startEvent", "Старт", *start),
        ("Task_Read", "userTask", "Взять ТН ВЭД и ОКПД 2 с карточки", *read),
        ("Gateway_Excl", "exclusiveGateway", "Код в исключениях?", *gw_ex),
        ("Task_Find", "serviceTask", "Найти этапы каждого кода", *find),
        ("Task_Skip", "serviceTask", "Не маркируется, двойник не нужен", *skip),
        ("Gateway_Both", "exclusiveGateway", "Оба кода есть в перечне?", *gw_both),
        ("Task_Calc", "serviceTask", "Дата = поздняя из двух дат этапов", *calc),
        ("Task_None", "serviceTask", "Не маркируется, двойник не нужен", *none),
        ("Gateway_Date", "exclusiveGateway", "Какая контрольная дата?", *gw_date),
        ("Task_S1", "serviceTask", "Этап 1, двойники с датой 01.05.2025", *t1),
        ("Task_S2", "serviceTask", "Этап 2, двойники с датой 01.07.2025", *t2),
        ("Task_S3", "serviceTask", "Этап 3, двойники с датой 01.10.2025", *t3),
        ("EndEvent_Ok", "endEvent", "Пара создана", *end_ok),
        ("EndEvent_No", "endEvent", "Обычный артикул", *end_no),
    ]
    node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}
    flows = []

    def add(fid, src, tgt, name, pts):
        flows.append((fid, src, tgt, name, pts))

    add("Flow_1", "StartEvent_1", "Task_Read", "", lr(node_box, "StartEvent_1", "Task_Read"))
    add("Flow_2", "Task_Read", "Gateway_Excl", "", lr(node_box, "Task_Read", "Gateway_Excl"))
    add("Flow_ex_no", "Gateway_Excl", "Task_Find", "Нет", lr(node_box, "Gateway_Excl", "Task_Find"))
    a, b = node_box["Gateway_Excl"], node_box["Task_Skip"]
    sx, sy = bottom(a)
    tx, ty = left(b)
    add("Flow_ex_yes", "Gateway_Excl", "Task_Skip", "Да", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_3", "Task_Find", "Gateway_Both", "", lr(node_box, "Task_Find", "Gateway_Both"))
    add("Flow_both_yes", "Gateway_Both", "Task_Calc", "Да", lr(node_box, "Gateway_Both", "Task_Calc"))
    a, b = node_box["Gateway_Both"], node_box["Task_None"]
    sx, sy = bottom(a)
    tx, ty = left(b)
    add("Flow_both_no", "Gateway_Both", "Task_None", "Нет", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_skip_end", "Task_Skip", "EndEvent_No", "", lr(node_box, "Task_Skip", "EndEvent_No"))
    add("Flow_none_end", "Task_None", "EndEvent_No", "", lr(node_box, "Task_None", "EndEvent_No"))
    add("Flow_4", "Task_Calc", "Gateway_Date", "", lr(node_box, "Task_Calc", "Gateway_Date"))

    a, b = node_box["Gateway_Date"], node_box["Task_S1"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_d1", "Gateway_Date", "Task_S1", "01.05.2025", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])
    add("Flow_d2", "Gateway_Date", "Task_S2", "01.07.2025", lr(node_box, "Gateway_Date", "Task_S2"))
    a, b = node_box["Gateway_Date"], node_box["Task_S3"]
    sx, sy = right(a)
    tx, ty = left(b)
    add("Flow_d3", "Gateway_Date", "Task_S3", "01.10.2025", [(sx, sy), (sx + 24, sy), (sx + 24, ty), (tx, ty)])

    a, b = node_box["Task_S1"], node_box["EndEvent_Ok"]
    sx, sy = right(a)
    tx, ty = top(b)
    add("Flow_e1", "Task_S1", "EndEvent_Ok", "", [(sx, sy), (tx, sy), (tx, ty)])
    add("Flow_e2", "Task_S2", "EndEvent_Ok", "", lr(node_box, "Task_S2", "EndEvent_Ok"))
    a, b = node_box["Task_S3"], node_box["EndEvent_Ok"]
    sx, sy = right(a)
    tx, ty = bottom(b)
    add("Flow_e3", "Task_S3", "EndEvent_Ok", "", [(sx, sy), (tx, sy), (tx, ty)])

    groups = [
        ("Group_Codes", "CategoryValue_Codes", "Классификация по кодам", 120, 30, 860, 520),
        ("Group_Twin", "CategoryValue_Twin", "Карточки-двойники этапа", 1120, 30, 320, 460),
    ]
    doc = (
        "Этап и контрольная дата считаются по паре ТН ВЭД + ОКПД 2, а не по названию товара. "
        "Нужны оба кода в перечне ПП РФ № 1681. Если коды из разных волн, берётся более поздняя дата. "
        "20.42.19 входит в 1 и 2 этапы: дату даёт ТН ВЭД. Исключённые коды и товары вне перечня остаются обычным артикулом."
    )
    write_bpmn(
        "/workspace/docs/stormbpmn/opredelenie-etapa.bpmn",
        "Definitions_EtapHimii",
        "Определение этапа маркировки по ТН ВЭД и ОКПД 2",
        "Process_EtapHimii",
        "Определение этапа по ТН ВЭД и ОКПД 2",
        doc,
        nodes,
        flows,
        groups,
        {"EndEvent_Ok", "EndEvent_No"},
    )
    write_svg(
        "/workspace/docs/stormbpmn/opredelenie-etapa.svg",
        "Определение этапа маркировки по ТН ВЭД и ОКПД 2",
        1600,
        620,
        nodes,
        flows,
        [
            (120, 30, 860, 520, "#eef6ff", "#5b8def", "Сначала коды, потом дата. Название товара не используется", 140, 52, "#2b5cb8"),
            (1120, 30, 320, 460, "#eefaf3", "#3ca06a", "Двойники с датой этапа", 1140, 52, "#237a4b"),
        ],
        "Если коды из разных волн — контрольная дата та, когда они пересекаются. С 01.07.2026 касса одинакова для всех трёх этапов.",
    )


def build_etapy_poster():
    cols = [
        {
            "title": "Этап 1  ·  с 01.05.2025",
            "fill": "#eff6ff",
            "stroke": "#1d4ed8",
            "head": "#1e40af",
            "tn": "ТН ВЭД: 3401; 3402 50 000 0; 3405 40 000 0",
            "okpd": "ОКПД 2: 20.41.3; 20.41.44; 20.42.19",
            "name": "Мыло, моющие средства, бытовая химия",
            "rest": "Остаток без КИЗ — если произведён или ввезён до 01.05.2025",
            "lines": [
                "3401 — мыло",
                "3402 50 000 0 — моющие для розницы",
                "3405 40 000 0 — чистящие пасты и порошки",
                "20.41.3 — мыло, моющие, чистящие",
                "20.41.44 — пасты и порошки чистящие",
                "20.42.19 — прочая продукция (вместе с ТН ВЭД этапа 1)",
            ],
        },
        {
            "title": "Этап 2  ·  с 01.07.2025",
            "fill": "#fff7ed",
            "stroke": "#c2410c",
            "head": "#9a3412",
            "tn": "ТН ВЭД: 3305; 3307 (кроме 3307 41 000 0, 3307 90 000 1/2)",
            "okpd": "ОКПД 2: 20.41.41; 20.42.16; 20.42.17; 20.42.19",
            "name": "Волосы, бритьё, дезодоранты, ароматизаторы",
            "rest": "Остаток без КИЗ — если произведён или ввезён до 01.07.2025",
            "lines": [
                "3305 — средства для волос",
                "3307 — бритьё, дезодоранты, ванны",
                "кроме благовоний и растворов для линз",
                "20.41.41 — ароматизаторы воздуха",
                "20.42.16 / 20.42.17 — шампуни и уход для волос",
                "20.42.19 — с ТН ВЭД этапа 2 даёт дату 01.07.2025",
            ],
        },
        {
            "title": "Этап 3  ·  с 01.10.2025",
            "fill": "#eefaf3",
            "stroke": "#15803d",
            "head": "#166534",
            "tn": "ТН ВЭД: 3304; 3306 (кроме 3306 20 000 0)",
            "okpd": "ОКПД 2: 20.42.12–15, 20.42.18 (с исключениями)",
            "name": "Косметика, декоративка, полость рта",
            "rest": "Остаток без КИЗ — если произведён или ввезён до 01.10.2025",
            "lines": [
                "3304 — косметика и уход за кожей",
                "3306 — полость рта и зубы, кроме зубной нити",
                "кроме антимикробной гигиены рук 3304 99 000 0",
                "20.42.12 / .13 — макияж губ, глаз, маникюр",
                "20.42.14 / .15 — пудра и уход за кожей",
                "20.42.18 — зубные пасты, кроме нитей .130",
            ],
        },
    ]
    w, h = 1680, 720
    gap, cw, ch = 24, 520, 600
    x0, y0 = 40, 70
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
        f'<rect width="{w}" height="{h}" fill="#f7f8fa"/>',
        f'<text x="{w / 2:.1f}" y="36" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" font-weight="700">Три этапа маркировки: ТН ВЭД и ОКПД 2</text>',
    ]
    for i, col in enumerate(cols):
        x = x0 + i * (cw + gap)
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{cw}" height="{ch}" rx="12" fill="{col["fill"]}" stroke="{col["stroke"]}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{x + 24}" y="{y0 + 36}" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="{col["head"]}">{escape(col["title"])}</text>'
        )
        parts.append(
            f'<text x="{x + 24}" y="{y0 + 64}" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#111827">{escape(col["name"])}</text>'
        )
        for j, line in enumerate((col["tn"], col["okpd"])):
            parts.append(
                f'<text x="{x + 24}" y="{y0 + 96 + j * 20}" font-family="Arial, sans-serif" font-size="12" fill="#374151">{escape(line)}</text>'
            )
        parts.append(
            f'<text x="{x + 24}" y="{y0 + 150}" font-family="Arial, sans-serif" font-size="12" font-style="italic" fill="#4b5563">{escape(col["rest"])}</text>'
        )
        for j, line in enumerate(col["lines"]):
            parts.append(
                f'<text x="{x + 24}" y="{y0 + 190 + j * 28}" font-family="Arial, sans-serif" font-size="13" fill="#1f2937">{escape(line)}</text>'
            )
    parts.append(
        f'<text x="40" y="{h - 28}" font-family="Arial, sans-serif" font-size="13" fill="#4b5568">'
        "Маркируется только пара кодов. Если ТН ВЭД и ОКПД 2 из разных волн — дата та, когда они пересекутся. "
        "20.42.19 входит в этапы 1 и 2. С 01.07.2026 касса для всех этапов общая.</text>"
    )
    parts.append("</svg>")
    path = "/workspace/docs/stormbpmn/etapy-tnved-okpd2.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"Wrote {path}")


def build_kassa_km():
    Y_OK, Y, Y_IT, Y_Q = 80, 280, 480, 660

    start = ev(40, Y)
    scan = task(140, Y)
    fn = task(340, Y)
    gw_fn = gw(540, Y)
    join_ok = gw(720, Y_OK)
    to_ok = task(860, Y_OK)
    end_ok = ev(1100, Y_OK)
    rescan = task(660, Y)
    gw_re = gw(880, Y)
    parse = task(1040, Y)
    gw_gs = gw(1260, Y)
    scanner = task(1420, Y_IT)
    end_it = ev(1680, Y_IT)
    chz = task(1420, Y)
    gw_chz = gw(1640, Y)
    hold = task(1800, Y)
    end_hold = ev(2040, Y)
    quar = task(1800, Y_Q)
    end_q = ev(2040, Y_Q)

    nodes = [
        ("StartEvent_1", "startEvent", "Старт", *start),
        ("Task_Scan", "userTask", "Сканировать Data Matrix", *scan),
        ("Task_FN", "serviceTask", "ФН проверяет формат КМ", *fn),
        ("Gateway_FN", "exclusiveGateway", "LocalError 0 и Result 1?", *gw_fn),
        ("Gateway_JoinOk", "exclusiveGateway", "", *join_ok),
        ("Task_Ok", "serviceTask", "Строка с КИЗ в чек", *to_ok),
        ("EndEvent_Ok", "endEvent", "Вывод через кассу", *end_ok),
        ("Task_Rescan", "userTask", "Повторить скан той же единицы", *rescan),
        ("Gateway_Rescan", "exclusiveGateway", "Повтор принят?", *gw_re),
        ("Task_Parse", "serviceTask", "Разобрать GS и криптохвост", *parse),
        ("Gateway_GS", "exclusiveGateway", "В КМ есть GS и 93 или 91/92?", *gw_gs),
        ("Task_Scanner", "userTask", "Настроить сканер на ASCII 29", *scanner),
        ("EndEvent_IT", "endEvent", "Продажа отложена, править сканер", *end_it),
        ("Task_CHZ", "userTask", "Проверить КМ в Честном знаке", *chz),
        ("Gateway_CHZ", "exclusiveGateway", "КМ наш и в обороте?", *gw_chz),
        ("Task_Hold", "userTask", "Отложить единицу, вызвать IT", *hold),
        ("EndEvent_Hold", "endEvent", "Не продавать как остаток", *end_hold),
        ("Task_Quarantine", "userTask", "Карантин, уведомить бухгалтера", *quar),
        ("EndEvent_Q", "endEvent", "Возврат поставщику", *end_q),
    ]
    node_box = {n[0]: (n[3], n[4], n[5], n[6]) for n in nodes}
    flows = []

    def add(fid, src, tgt, name, pts):
        flows.append((fid, src, tgt, name, pts))

    add("Flow_s1", "StartEvent_1", "Task_Scan", "", lr(node_box, "StartEvent_1", "Task_Scan"))
    add("Flow_s2", "Task_Scan", "Task_FN", "", lr(node_box, "Task_Scan", "Task_FN"))
    add("Flow_s3", "Task_FN", "Gateway_FN", "", lr(node_box, "Task_FN", "Gateway_FN"))

    a, b = node_box["Gateway_FN"], node_box["Gateway_JoinOk"]
    sx, sy = top(a)
    tx, ty = left(b)
    add("Flow_fn_yes", "Gateway_FN", "Gateway_JoinOk", "Да", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_fn_no", "Gateway_FN", "Task_Rescan", "Нет, ошибка формата", lr(node_box, "Gateway_FN", "Task_Rescan"))
    add("Flow_r1", "Task_Rescan", "Gateway_Rescan", "", lr(node_box, "Task_Rescan", "Gateway_Rescan"))

    a, b = node_box["Gateway_Rescan"], node_box["Gateway_JoinOk"]
    sx, sy = top(a)
    tx, ty = bottom(b)
    add("Flow_re_yes", "Gateway_Rescan", "Gateway_JoinOk", "Да", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_join_ok", "Gateway_JoinOk", "Task_Ok", "", lr(node_box, "Gateway_JoinOk", "Task_Ok"))
    add("Flow_ok_end", "Task_Ok", "EndEvent_Ok", "", lr(node_box, "Task_Ok", "EndEvent_Ok"))
    add("Flow_re_no", "Gateway_Rescan", "Task_Parse", "Нет", lr(node_box, "Gateway_Rescan", "Task_Parse"))
    add("Flow_p1", "Task_Parse", "Gateway_GS", "", lr(node_box, "Task_Parse", "Gateway_GS"))

    a, b = node_box["Gateway_GS"], node_box["Task_Scanner"]
    sx, sy = bottom(a)
    tx, ty = left(b)
    add("Flow_gs_no", "Gateway_GS", "Task_Scanner", "Нет, сканер съел GS", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_it_end", "Task_Scanner", "EndEvent_IT", "", lr(node_box, "Task_Scanner", "EndEvent_IT"))
    add("Flow_gs_yes", "Gateway_GS", "Task_CHZ", "Да", lr(node_box, "Gateway_GS", "Task_CHZ"))
    add("Flow_c1", "Task_CHZ", "Gateway_CHZ", "", lr(node_box, "Task_CHZ", "Gateway_CHZ"))
    add("Flow_chz_yes", "Gateway_CHZ", "Task_Hold", "Да", lr(node_box, "Gateway_CHZ", "Task_Hold"))
    add("Flow_hold_end", "Task_Hold", "EndEvent_Hold", "", lr(node_box, "Task_Hold", "EndEvent_Hold"))

    a, b = node_box["Gateway_CHZ"], node_box["Task_Quarantine"]
    sx, sy = bottom(a)
    tx, ty = left(b)
    add("Flow_chz_no", "Gateway_CHZ", "Task_Quarantine", "Нет, брак кода", [(sx, sy), (sx, ty), (tx, ty)])
    add("Flow_q_end", "Task_Quarantine", "EndEvent_Q", "", lr(node_box, "Task_Quarantine", "EndEvent_Q"))

    groups = [
        ("Group_Cash", "CategoryValue_Cash", "Касса: не закрывать отвергнутый КМ", 120, 30, 1060, 390),
        ("Group_Cause", "CategoryValue_Cause", "Сканер или сам код", 1320, 30, 860, 390),
        ("Group_Q", "CategoryValue_Q", "Карантин", 1320, 600, 860, 160),
    ]
    doc = (
        "CheckItemLocalError 1 и CheckItemLocalResult 0 — КМ некорректного формата, ФН его не проверил. "
        "«Ошибок нет» — ответ драйвера ККТ, не успех маркировки. "
        "Не подменять артикул-остатком и не закрывать чек с отвергнутой маркировкой. "
        "Сначала повторный скан, затем GS/криптохвост, затем Честный знак."
    )
    write_bpmn(
        "/workspace/docs/stormbpmn/oshibka-proverki-km-kassa.bpmn",
        "Definitions_KassaKm",
        "Ошибка проверки КМ на кассе",
        "Process_KassaKm",
        "Ошибка проверки КМ, маркировка будет отвергнута",
        doc,
        nodes,
        flows,
        groups,
        {"Gateway_JoinOk"},
    )
    write_svg(
        "/workspace/docs/stormbpmn/oshibka-proverki-km-kassa.svg",
        "Ошибка проверки КМ на кассе: формат, сканер, карантин",
        2200,
        820,
        nodes,
        flows,
        [
            (120, 30, 1060, 390, "#eef6ff", "#5b8def", "Касса: повторный скан, не закрывать отвергнутый КМ", 140, 52, "#2b5cb8"),
            (1320, 30, 860, 390, "#fff7ed", "#c2410c", "Нет GS — сканер. Код в ЧЗ — IT. Кода нет — карантин", 1340, 52, "#9a3412"),
            (1320, 600, 860, 160, "#fef2f2", "#b91c1c", "Карантин, уведомить бухгалтера", 1340, 622, "#991b1b"),
        ],
        "LocalError 1 = некорректный формат КМ. Не продавать как законный остаток: на упаковке есть Data Matrix.",
    )


if __name__ == "__main__":
    build_priemka()
    build_outbound()
    build_etap()
    build_etapy_poster()
    build_kassa_km()


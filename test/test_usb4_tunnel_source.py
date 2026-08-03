from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "handmade" / "src" / "usb4_lanebond.h"


def _function_body(source: str, name: str, next_name: str) -> str:
    return source.split(f"static void {name}", 1)[1].split(f"static void {next_name}", 1)[0]


def test_tunnel_power_on_preserves_lane_control_register_bits():
    """Power-on must not copy unrelated B402 bits into lane control C659."""
    source = SOURCE.read_text()
    body = _function_body(source, "u4lb_pcie_tunnel_pwron", "u4lb_rxpll_cfg_trigger")

    assert "REG_PCIE_CTRL_B402 & 0xFE" not in body
    assert "REG_PCIE_LANE_CTRL_C659 & 0xFE" in body
    assert "REG_PCIE_LANE_CTRL_C659 | 0x01" in body


def test_device_router_events_are_acknowledged_before_dispatch():
    """route_mode=4 events must be W1C-acked even when a handler is gated."""
    source = SOURCE.read_text()
    body = _function_body(source, "u4lb_tunnel_event_dispatch", "u4lb_tunnel_pwron_train")

    event_10 = body.split("if (p1508 & 0x10)", 1)[1].split("else if", 1)[0]
    event_08 = body.split("else if (p1508 & 0x08)", 1)[1].split("else if", 1)[0]
    assert event_10.index("P1_WR") < event_10.index("u4_cfg.route_mode")
    assert event_08.index("P1_WR") < event_08.index("u4_cfg.route_mode")
    assert "u4_cfg.route_mode & 0x85" in event_10
    assert "u4_cfg.route_mode & 0x85" in event_08


def test_unknown_tunnel_events_are_cleared():
    """Unknown W1C bits must not leave the USB4 interrupt dispatcher storming."""
    source = SOURCE.read_text()
    body = _function_body(source, "u4lb_tunnel_event_dispatch", "u4lb_tunnel_pwron_train")

    assert "else if (p1508)" in body
    assert "P1_WR(P1_USB4_TUNNEL_EVENT_STATUS_1508, p1508)" in body
